import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import zmq, json
from common.eventos import Evento, TipoEvento
from common.config import get_zmq_address
from common.logger import criar_logger
from common.llm import get_provedor
from common.db import Repositorio

log = criar_logger("IA")
ctx = zmq.Context.instance()
sub_doc = ctx.socket(zmq.SUB)
sub_doc.connect(get_zmq_address("documentos"))
sub_doc.setsockopt_string(zmq.SUBSCRIBE, TipoEvento.VERSAO_SUBMETIDA.value)
sub_fb = ctx.socket(zmq.SUB)
sub_fb.connect(get_zmq_address("avaliacao"))
sub_fb.setsockopt_string(zmq.SUBSCRIBE, TipoEvento.FEEDBACK_ENVIADO.value)
pub = ctx.socket(zmq.PUB)
pub.bind(get_zmq_address("ia", "bind"))
provedor = get_provedor()
repo = Repositorio()
ultima_versao = {}   # cache local p/ fallback offline (sem MySQL); a fonte da verdade e o banco
log.info("no ar | SUB versao_submetida/feedback_enviado -> LLM -> PUB recomendacao/feedback")

def on_versao(dados):
    if not repo.registrar_evento(dados):     # idempotencia
        return
    aluno = dados["aluno_id"]
    texto = dados.get("payload", {}).get("texto", "")
    p_in = dados.get("payload", {})
    entrega_id = p_in.get("entrega_id")
    versao_id = p_in.get("versao_id") or p_in.get("id")
    submission_id = p_in.get("submission_id")   # id unico da submissao (correlacao com a interface)

    ultima_versao[aluno] = texto             # cache de fallback (demo sem MySQL)
    an = provedor.analisar(texto, "geral")   # monta prompt + consulta provedor de LLM
    ev = Evento(TipoEvento.RECOMENDACAO_IA_GERADA, aluno_id=aluno, operacao="recomendar",
                payload={"recomendacoes": an.get("recomendacoes", []),
                         "score": an.get("score", 0), "observacoes": an.get("observacoes", ""),
                         "entrega_id": entrega_id, "versao_id": versao_id, "submission_id": submission_id})
    pub.send_string(f"{ev.evento} {ev.to_json_str()}")
    log.info(f"recomendacao gerada p/ aluno {aluno}; publicado {ev}")

def on_feedback(dados):
    if not repo.registrar_evento(dados):     # idempotencia
        return
    aluno = dados["aluno_id"]
    # le a versao vigente do banco (fonte da verdade); cai no cache local so no modo offline
    texto = repo.texto_versao_vigente(aluno) or ultima_versao.get(aluno, "")
    an = provedor.analisar(texto, "feedback_atendimento")
    atendido = an.get("status") == "apto"
    tipo = TipoEvento.FEEDBACK_ATENDIDO if atendido else TipoEvento.PENDENCIAS_IDENTIFICADAS
    ev = Evento(tipo, aluno_id=aluno, operacao="reavaliar",
                payload={"status": an.get("status"), "recomendacoes": an.get("recomendacoes", []),
                         "score": an.get("score", 0)})
    pub.send_string(f"{ev.evento} {ev.to_json_str()}")
    log.info(f"reavaliacao: {'feedback_atendido' if atendido else 'pendencias_identificadas'} p/ aluno {aluno}")

if __name__ == "__main__":
    poller = zmq.Poller()
    poller.register(sub_doc, zmq.POLLIN)
    poller.register(sub_fb, zmq.POLLIN)
    try:
        while True:
            socks = dict(poller.poll(1000))
            try:
                if sub_doc in socks:
                    _, c = sub_doc.recv_string().split(" ", 1); on_versao(json.loads(c))
                if sub_fb in socks:
                    _, c = sub_fb.recv_string().split(" ", 1); on_feedback(json.loads(c))
            except Exception as e:               # uma mensagem ruim nao derruba o servico
                log.error(f"erro ao processar evento: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        sub_doc.close(); sub_fb.close(); pub.close(); repo.fechar(); ctx.term()
