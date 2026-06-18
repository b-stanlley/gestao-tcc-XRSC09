import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import zmq, json
from common.eventos import Evento, TipoEvento
from common.config import get_zmq_address
from common.logger import criar_logger
from common.db import Repositorio

log = criar_logger("Feedback&Avaliacao")
ctx = zmq.Context.instance()
sub = ctx.socket(zmq.SUB)
sub.connect(get_zmq_address("gateway"))
sub.setsockopt_string(zmq.SUBSCRIBE, TipoEvento.PARECER_RECEBIDO.value)
pub = ctx.socket(zmq.PUB)
pub.bind(get_zmq_address("avaliacao", "bind"))
repo = Repositorio()
log.info("no ar | SUB gateway:parecer_recebido -> persiste -> PUB feedback_enviado (parecer padronizado)")

# Formulario de parecer PADRONIZADO (inspirado no JEMS): criterios 0-10 -> nota -> decisao.
CRITERIOS_PADRAO = ["originalidade", "metodologia", "escrita", "relevancia"]

def _num(v):
    try: return float(v)
    except (TypeError, ValueError): return None

def _media(criterios):
    vals = [n for n in (_num(v) for v in criterios.values()) if n is not None]
    return round(sum(vals) / len(vals), 1) if vals else 0.0

def handle(dados):
    if not repo.registrar_evento(dados):       # idempotencia
        return
    aluno = dados["aluno_id"]
    p = dados.get("payload", {})
    # aceita o formulario padronizado; cai p/ texto livre (compat) se vier so 'feedback'
    criterios = p.get("criterios") or {}
    comentario = p.get("comentario", p.get("feedback", ""))
    nota = p.get("nota")
    nota = _media(criterios) if nota is None else _num(nota)
    decisao = p.get("decisao") or ("aprovado" if (nota or 0) >= 6.0 else "correcoes")
    versao_id = p.get("versao_id")
    secoes_criticas = [k for k, v in criterios.items() if (_num(v) or 0) < 6.0]

    repo.salvar_parecer(aluno, versao_id, criterios, nota, decisao, comentario)
    ev = Evento(TipoEvento.FEEDBACK_ENVIADO, aluno_id=aluno, operacao="publicar_parecer",
                payload={"criterios": criterios, "nota": nota, "decisao": decisao,
                         "comentario": comentario,
                         # compat com IA/Notificacoes que ja liam estes campos:
                         "feedback": comentario, "secoes_criticas": secoes_criticas})
    pub.send_string(f"{ev.evento} {ev.to_json_str()}")
    log.info(f"parecer PADRONIZADO publicado: aluno={aluno} nota={nota} decisao={decisao}")

if __name__ == "__main__":
    try:
        while True:
            try:
                _, c = sub.recv_string().split(" ", 1)
                handle(json.loads(c))
            except Exception as e:               # uma mensagem ruim nao derruba o servico
                log.error(f"erro ao processar evento: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        sub.close(); pub.close(); repo.fechar(); ctx.term()
