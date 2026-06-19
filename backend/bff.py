"""BFF (Backend-for-Frontend) do SINTCC — ponte HTTP <-> malha ZeroMQ.

Substitui o antigo gateway Node (que dependia do binding `zeromq` nativo,
quebrado nesta maquina). Aqui usamos pyzmq, que roda. O BFF NAO faz parte da
coreografia: e apenas a borda que traduz as chamadas HTTP da interface React
para eventos na malha brokerless, e devolve a coreografia ao usuario.

Demonstra, na borda, os 3 padroes ZeroMQ do projeto:
  - PUB (bind 5570)      : injeta comandos do cliente na malha (versao_recebida,
                           parecer_recebido, banca_definida, nota_banca_submetida).
  - SUB (connect)        : ouve os eventos publicados pelos servicos e os transforma
                           em notificacoes legiveis (feed da interface).
  - DEALER (connect 5561): login sincrono no servico de Autenticacao (DEALER/ROUTER).
  - PUSH (connect 5567)  : solicita a geracao distribuida de relatorios (PUSH/PULL).

Servidor HTTP em stdlib (sem dependencia extra): REST em /api/* + serve o build
estatico do React (../dist) quando presente. Em desenvolvimento, o Vite faz proxy
de /api para ca (ver vite.config.ts).
"""
import sys, os, json, time, threading, base64, hmac, hashlib, mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zmq
from common.eventos import Evento, TipoEvento
from common.config import get_zmq_address
from common.logger import criar_logger
from common.llm import get_provedor

log = criar_logger("BFF")

HTTP_PORT = int(os.getenv("PORT", "3000"))
DIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")
TOKEN_SECRET = os.getenv("BFF_SECRET", "sintcc-demo-secret").encode("utf-8")

# Mapeia os papeis da malha (aluno/orientador/coordenador/banca) para o vocabulario
# que a interface React ja usa (student/advisor/coordinator).
ROLE_MAP = {"aluno": "student", "orientador": "advisor",
            "coordenador": "coordinator", "banca": "coordinator"}

# --------------------------------------------------------------------------- #
# Camada ZeroMQ (a borda da malha)
# --------------------------------------------------------------------------- #
ctx = zmq.Context.instance()

pub = ctx.socket(zmq.PUB)                 # injeta comandos do cliente na malha
pub.bind(get_zmq_address("gateway", "bind"))
pub_lock = threading.Lock()

dealer = ctx.socket(zmq.DEALER)           # login sincrono (DEALER/ROUTER)
dealer.setsockopt(zmq.RCVTIMEO, 4000)
dealer.connect(get_zmq_address("autenticacao"))
dealer_lock = threading.Lock()

push = ctx.socket(zmq.PUSH)               # solicita relatorios (PUSH/PULL)
push.connect(get_zmq_address("relatorio_req"))
push_lock = threading.Lock()

provedor = get_provedor()                 # provedor de LLM (mesmo da malha)

# Feed de notificacoes derivado dos eventos reais da malha (read-model do BFF).
_notifs = []
_notifs_lock = threading.Lock()
_seq = 0
_ultimo_relatorio = {"valor": None}

# Read-model para manter o estado sincronizado com a interface React
_proposals_store = {}   # aluno_id -> dados da proposta
_submissions_store = []
_feedbacks_store = []
_deliveries_store = []
_store_lock = threading.Lock()


def _add_notif(message, evento="", aluno_id=None, role=None):
    global _seq
    with _notifs_lock:
        _seq += 1
        _notifs.insert(0, {
            "id": _seq, "message": message, "evento": evento,
            "aluno_id": aluno_id, "role": role, "is_read": False,
            "created_at": time.strftime("%H:%M:%S"),
        })
        del _notifs[200:]


# Como cada evento da malha vira uma notificacao legivel no feed da interface.
def _mensagem_do_evento(topico, dados):
    p = dados.get("payload", {}) or {}
    aluno = dados.get("aluno_id")
    if topico == TipoEvento.PROPOSTA_SUBMETIDA.value:
        return f"📨 Proposta submetida: \"{p.get('titulo', '')[:40]}\" (à coordenação/orientador)"
    if topico == TipoEvento.PROPOSTA_APROVADA.value:
        return "✅ Proposta aprovada pelo orientador"
    if topico == TipoEvento.PROPOSTA_REJEITADA.value:
        return "❌ Proposta rejeitada (ajustes solicitados)"
    if topico == TipoEvento.CRONOGRAMA_REGISTRADO.value:
        return "🗓️ Cronograma registrado (orientador + discente)"
    if topico == TipoEvento.VERSAO_SUBMETIDA.value:
        return f"📄 Versão v{p.get('numero', '?')} registrada e enviada à IA (Documentos)"
    if topico == TipoEvento.RECOMENDACAO_IA_GERADA.value:
        recs = p.get("recomendacoes", [])
        extra = f" — {len(recs)} recomendação(ões)" if recs else ""
        return f"🤖 IA gerou análise (score {p.get('score', 0)}){extra}"
    if topico == TipoEvento.FEEDBACK_ENVIADO.value:
        return f"📝 Parecer padronizado publicado: {p.get('decisao', '?')} (nota {p.get('nota', '?')})"
    if topico == TipoEvento.FEEDBACK_ATENDIDO.value:
        return "✅ IA: feedback atendido pelo aluno"
    if topico == TipoEvento.PENDENCIAS_IDENTIFICADAS.value:
        return "⚠️ IA: pendências identificadas na versão"
    if topico == TipoEvento.ALERTA_PENDENCIA_DISPARADO.value:
        return "🔔 Alerta de pendência enviado ao orientador"
    if topico == TipoEvento.DEFESA_AGENDADA.value:
        return f"🎓 Defesa agendada (banca {p.get('avaliadores', [])})"
    if topico == TipoEvento.CONVOCACAO_BANCA_ENVIADA.value:
        return "📨 Convocação de banca enviada"
    if topico == TipoEvento.DEFESA_APROVADA.value:
        return f"🎉 Defesa APROVADA (nota {p.get('nota', '?')})"
    if topico == TipoEvento.DEFESA_REPROVADA.value:
        return f"❌ Defesa reprovada (nota {p.get('nota', '?')})"
    if topico == TipoEvento.RELATORIO_GERADO.value:
        return f"📊 Relatório gerado: {p.get('total_tccs', '?')} TCCs consolidados"
    return None


def _loop_sub():
    """Ouve TODAS as PUBs dos servicos e alimenta o feed (read-model)."""
    poller = zmq.Poller()
    # Conecta-se diretamente ao PUB de cada servico para receber as atualizacoes de estado
    for service_name in ("propostas", "documentos", "ia", "avaliacao", "notificacao", "banca", "relatorio"):
        s = ctx.socket(zmq.SUB)
        s.connect(get_zmq_address(service_name))
        s.setsockopt_string(zmq.SUBSCRIBE, "")
        poller.register(s, zmq.POLLIN)
    log.info("SUB conectado às PUBs dos serviços (feed da coreografia ao vivo)")
    while True:
        try:
            socks = dict(poller.poll(1000))
            for s in socks:
                raw = s.recv_string()
                topico, c = raw.split(" ", 1)
                dados = json.loads(c)
                aluno = dados.get("aluno_id")
                p = dados.get("payload", {}) or {}
                if topico == TipoEvento.RELATORIO_GERADO.value:
                    _ultimo_relatorio["valor"] = dados.get("payload", {})
                msg = _mensagem_do_evento(topico, dados)
                if msg:
                    _add_notif(msg, topico, dados.get("aluno_id"))
                
                # Atualiza o Read-Model do BFF com base nos eventos da malha
                with _store_lock:
                    if topico == TipoEvento.PROPOSTA_SUBMETIDA.value:
                        _proposals_store[aluno] = {
                            "id": p.get("id") or dados.get("id"), "student_id": aluno,
                            "title": p.get("titulo"), "summary": p.get("resumo"), "status": "pending"
                        }
                    elif topico == TipoEvento.PROPOSTA_APROVADA.value:
                        if aluno in _proposals_store: _proposals_store[aluno]["status"] = "approved"
                    elif topico == TipoEvento.PROPOSTA_REJEITADA.value:
                        if aluno in _proposals_store: _proposals_store[aluno]["status"] = "adjustments"
                    elif topico == TipoEvento.VERSAO_SUBMETIDA.value:
                        # Evita duplicatas buscando por student_id e delivery_id
                        existente = None
                        ent_id = p.get("entrega_id")
                        for s in _submissions_store:
                            if str(s.get("student_id")) == str(aluno) and str(s.get("delivery_id")) == str(ent_id):
                                existente = s
                                break
                        
                        if existente:
                            existente["id"] = p.get("versao_id") or existente["id"]
                            existente["version"] = p.get("numero") or existente["version"]
                            if p.get("texto"):
                                existente["text"] = p.get("texto")
                        else:
                            _submissions_store.append({
                                "id": p.get("versao_id") or p.get("id") or int(time.time()),
                                "delivery_id": ent_id,
                                "student_id": aluno,
                                "file_path": "uploads/documento.pdf",
                                "version": p.get("numero"),
                                "text": p.get("texto"),
                                "created_at": time.strftime("%d/%m/%Y")
                            })
                    elif topico == TipoEvento.FEEDBACK_ENVIADO.value:
                        existente = None
                        sub_id = p.get("versao_id")
                        for f in _feedbacks_store:
                            if str(f.get("submission_id")) == str(sub_id) and sub_id is not None:
                                existente = f
                                break
                        
                        if existente:
                            existente["id"] = p.get("id") or existente["id"]
                            existente["comment"] = p.get("comentario") or existente["comment"]
                            existente["status"] = "approved" if p.get("decisao") == "aprovado" else "corrections"
                        else:
                            _feedbacks_store.append({
                                "id": p.get("id", int(time.time())),
                                "submission_id": sub_id,
                                "advisor_id": 3,
                                "comment": p.get("comentario"),
                                "status": "approved" if p.get("decisao") == "aprovado" else "corrections",
                                "created_at": time.strftime("%d/%m/%Y")
                            })
        except Exception as e:
            log.error(f"erro no loop SUB: {e}")


# --------------------------------------------------------------------------- #
# Tokens de sessao (HMAC com a stdlib — sem dependencia extra)
# --------------------------------------------------------------------------- #
def emitir_token(usuario):
    corpo = {"id": usuario["id"], "role": usuario["role"], "nome": usuario.get("nome", "")}
    raw = base64.urlsafe_b64encode(json.dumps(corpo).encode()).decode()
    assinatura = hmac.new(TOKEN_SECRET, raw.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{raw}.{assinatura}"


def ler_token(token):
    try:
        raw, assinatura = (token or "").split(".", 1)
        esperado = hmac.new(TOKEN_SECRET, raw.encode(), hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(assinatura, esperado):
            return None
        return json.loads(base64.urlsafe_b64decode(raw.encode()))
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Acoes: traduzem HTTP -> eventos na malha brokerless
# --------------------------------------------------------------------------- #
def _publicar(tipo_evento, aluno_id, operacao, payload):
    ev = Evento(tipo_evento, aluno_id=int(aluno_id or 0), operacao=operacao, payload=payload)
    with pub_lock:
        pub.send_string(f"{ev.evento} {ev.to_json_str()}")
    log.info(f"📤 injetado na malha: {ev}")
    return ev.id


def login(body):
    email = (body.get("email") or "").strip().lower()
    senha = body.get("password") or body.get("senha") or ""
    with dealer_lock:
        dealer.send_string(json.dumps({"email": email, "senha": senha}))
        try:
            frames = dealer.recv_multipart()
        except zmq.Again:
            return 503, {"error": "Serviço de autenticação indisponível"}
    r = json.loads(frames[-1].decode("utf-8"))
    if not r.get("ok"):
        return 401, {"error": r.get("erro", "Credenciais inválidas")}
    u = r["usuario"]
    user = {"id": u["id"], "name": u.get("nome", email), "role": ROLE_MAP.get(u["role"], u["role"])}
    return 200, {"token": emitir_token(u), "user": user}


def submeter_versao(body, claims):
    aluno = body.get("student_id") or (claims or {}).get("id")
    texto = body.get("text") or body.get("texto") or ""
    delivery_id = body.get("delivery_id")
    
    sub_id = int(time.time()) % 100000
    
    # Salva na lista em memória de imediato para resolver condição de corrida no polling do React
    with _store_lock:
        existente = None
        for s in _submissions_store:
            if str(s.get("student_id")) == str(aluno) and str(s.get("delivery_id")) == str(delivery_id):
                existente = s
                break
        
        if existente:
            existente["text"] = texto
            existente["version"] = existente.get("version", 1) + 1
        else:
            _submissions_store.append({
                "id": sub_id,
                "delivery_id": delivery_id,
                "student_id": aluno,
                "file_path": "uploads/documento.pdf",
                "version": 1,
                "text": texto,
                "created_at": time.strftime("%d/%m/%Y")
            })

    _publicar(TipoEvento.VERSAO_RECEBIDA, aluno, "submeter",
              {"texto": texto, "tipo": body.get("tipo", "desenvolvimento"), "caracteres": len(texto),
               "entrega_id": delivery_id})
    return 202, {"success": True, "submission_id": sub_id}


def submeter_proposta(body, claims):
    aluno = body.get("student_id") or (claims or {}).get("id")
    _publicar(TipoEvento.PROPOSTA_RECEBIDA, aluno, "submeter_proposta",
              {"titulo": body.get("title", ""), "resumo": body.get("summary", "")})
    return 202, {"success": True, "proposal_id": int(time.time()) % 100000}


def avaliar_proposta(body, claims):
    aluno = body.get("student_id") or (claims or {}).get("id")
    _publicar(TipoEvento.PROPOSTA_AVALIADA, aluno, "avaliar_proposta",
              {"decisao": body.get("decisao", "aprovada"), "motivo": body.get("motivo", "")})
    return 202, {"success": True}


def registrar_cronograma(body, claims):
    aluno = body.get("student_id") or (claims or {}).get("id")
    _publicar(TipoEvento.CRONOGRAMA_REGISTRADO, aluno, "registrar_cronograma",
              {"etapas": body.get("etapas", []), "observacoes": body.get("observacoes", "")})
    return 202, {"success": True}


def enviar_parecer(body, claims):
    aluno = body.get("student_id") or (claims or {}).get("id")
    status = body.get("status", "")
    comment = body.get("comment") or body.get("comentario") or ""
    submission_id = body.get("submission_id")
    
    fb_id = int(time.time()) % 100000
    
    # Salva na lista em memória de feedbacks síncronamente para evitar condição de corrida no polling do React
    with _store_lock:
        existente = None
        for f in _feedbacks_store:
            if str(f.get("submission_id")) == str(submission_id) and f.get("submission_id") is not None:
                existente = f
                break
        
        if existente:
            existente["comment"] = comment
            existente["status"] = status
        else:
            _feedbacks_store.append({
                "id": fb_id,
                "submission_id": submission_id,
                "advisor_id": 3,
                "comment": comment,
                "status": status,
                "created_at": time.strftime("%d/%m/%Y")
            })

    decisao = "aprovado" if status == "approved" else "correcoes"
    _publicar(TipoEvento.PARECER_RECEBIDO, aluno, "registrar_parecer",
              {"comentario": comment, "feedback": comment,
               "decisao": decisao, "criterios": body.get("criterios") or {},
               "nota": body.get("nota"), "versao_id": submission_id})

    # Notifica o serviço de propostas para atualizar o status do TCC na malha
    _publicar(TipoEvento.PROPOSTA_AVALIADA, aluno, "avaliar_proposta",
              {"decisao": "aprovada" if status == "approved" else "rejeitada", 
               "motivo": comment})

    return 202, {"success": True, "feedback_id": fb_id}



def definir_banca(body, claims):
    aluno = body.get("student_id") or (claims or {}).get("id")
    _publicar(TipoEvento.BANCA_DEFINIDA, aluno, "definir_banca",
              {"avaliadores": body.get("avaliadores", []), "data_defesa": body.get("data_defesa"),
               "orientador_id": (claims or {}).get("id")})
    return 202, {"success": True}


def nota_banca(body, claims):
    aluno = body.get("student_id") or (claims or {}).get("id")
    _publicar(TipoEvento.NOTA_BANCA_SUBMETIDA, aluno, "nota_banca",
              {"nota": body.get("nota"), "comentario": body.get("comentario", "")})
    return 202, {"success": True}


def gerar_relatorio(body, claims):
    with push_lock:
        push.send_string(json.dumps({"tipo": body.get("tipo", "panorama"),
                                     "solicitante": (claims or {}).get("nome", "coordenador")}))
    return 202, {"success": True, "message": "Relatório solicitado ao pipeline PUSH/PULL"}

def registrar_entrega_local(body):
    with _store_lock:
        new_id = int(time.time()) % 100000
        delivery = {"id": new_id, "name": body.get("name"), 
                    "description": body.get("description"), "deadline": body.get("deadline")}
        _deliveries_store.append(delivery)
        return new_id


def analisar_ia(body, claims):
    texto = body.get("docContent") or body.get("texto") or ""
    an = provedor.analisar(texto, "geral")
    recs = an.get("recomendacoes", [])
    linhas = [f"📊 Score estimado: {an.get('score', 0)}/100",
              f"Status: {an.get('status', '?')}", ""]
    if recs:
        linhas.append("Recomendações:")
        linhas += [f"• {r}" for r in recs]
    else:
        linhas.append("Nenhuma pendência crítica detectada.")
    linhas += ["", f"Observações: {an.get('observacoes', '')}"]
    return 200, {"analysis": "\n".join(linhas), "raw": an}


# --------------------------------------------------------------------------- #
# Servidor HTTP
# --------------------------------------------------------------------------- #
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass  # silencia o log padrao (verboso); usamos o logger da malha

    def _claims(self):
        auth = self.headers.get("Authorization", "")
        return ler_token(auth[7:]) if auth.startswith("Bearer ") else None

    def _json_body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except Exception:
            return {}

    def _send_json(self, code, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/health":
            return self._send_json(200, {"status": "ok", "message": "SINTCC BFF (pyzmq) no ar"})
        if path == "/api/notifications":
            with _notifs_lock:
                return self._send_json(200, list(_notifs))
        if path == "/api/relatorios/ultimo":
            return self._send_json(200, _ultimo_relatorio["valor"] or {})
        if path == "/api/proposals":
            with _store_lock: return self._send_json(200, list(_proposals_store.values()))
        if path == "/api/submissions":
            with _store_lock: return self._send_json(200, _submissions_store)
        if path == "/api/feedbacks":
            with _store_lock: return self._send_json(200, _feedbacks_store)
        if path == "/api/deliveries":
            with _store_lock: return self._send_json(200, _deliveries_store)
        return self._serve_static(path)

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        body = self._json_body()
        claims = self._claims()
        try:
            if path == "/api/auth/login":
                return self._send_json(*login(body))
            if path == "/api/submissions":
                return self._send_json(*submeter_versao(body, claims))
            if path == "/api/proposals":
                return self._send_json(*submeter_proposta(body, claims))
            if path == "/api/proposals/avaliar":
                return self._send_json(*avaliar_proposta(body, claims))
            if path == "/api/cronograma":
                return self._send_json(*registrar_cronograma(body, claims))
            if path == "/api/feedback":
                return self._send_json(*enviar_parecer(body, claims))
            if path == "/api/deliveries":
                new_id = registrar_entrega_local(body)
                return self._send_json(202, {"success": True, "delivery_id": new_id})
            if path == "/api/ai/analyze":
                return self._send_json(*analisar_ia(body, claims))
            if path == "/api/banca/definir":
                return self._send_json(*definir_banca(body, claims))
            if path == "/api/banca/nota":
                return self._send_json(*nota_banca(body, claims))
            if path == "/api/relatorios/gerar":
                return self._send_json(*gerar_relatorio(body, claims))
        except Exception as e:
            log.error(f"erro em {path}: {e}")
            return self._send_json(500, {"error": str(e)})
        return self._send_json(404, {"error": "Rota não encontrada"})

    def _serve_static(self, path):
        if not os.path.isdir(DIST_DIR):
            return self._send_json(200, {"info": "Frontend em modo dev — use o Vite (npm run dev)."})
        rel = path.lstrip("/") or "index.html"
        alvo = os.path.join(DIST_DIR, rel)
        if not os.path.isfile(alvo):
            alvo = os.path.join(DIST_DIR, "index.html")  # SPA fallback
        try:
            with open(alvo, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(alvo)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception:
            self._send_json(404, {"error": "arquivo não encontrado"})


def main():
    threading.Thread(target=_loop_sub, daemon=True).start()
    time.sleep(0.3)
    server = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), Handler)
    log.info(f"✅ BFF HTTP em http://localhost:{HTTP_PORT}  (PUB 5570 | DEALER 5561 | PUSH 5567)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        with pub_lock: pub.close()
        dealer.close(); push.close(); ctx.term()


if __name__ == "__main__":
    main()
