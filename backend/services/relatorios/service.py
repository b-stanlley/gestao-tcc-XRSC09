"""Servico de Relatorios — padrao PUSH/PULL (geracao distribuida por workers).

E o 3o dos tres padroes ZeroMQ do relatorio. Ao receber uma solicitacao
(do coordenador/NDE, via gateway), o coordenador DIVIDE o trabalho de agregacao
em subtarefas e as VENTILA (PUSH) a um pool de workers; cada worker processa sua
fatia em paralelo e devolve o parcial (PUSH) ao SINK (PULL); o coordenador
CONSOLIDA o panorama e publica `relatorio_gerado` (PUB) ao solicitante.

Sockets:
  relatorio_req  (PULL bind)  <- solicitacoes
  relatorio_vent (PUSH bind)  -> subtarefas aos workers
  relatorio_sink (PULL bind)  <- parciais dos workers
  relatorio      (PUB  bind)  -> relatorio_gerado (panorama)
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import zmq
from common.config import get_zmq_address
from common.logger import criar_logger
from common.eventos import Evento, TipoEvento

log = criar_logger("Relatorios")
ctx = zmq.Context.instance()
req  = ctx.socket(zmq.PULL); req.bind(get_zmq_address("relatorio_req", "bind"))
vent = ctx.socket(zmq.PUSH); vent.bind(get_zmq_address("relatorio_vent", "bind"))
sink = ctx.socket(zmq.PULL); sink.bind(get_zmq_address("relatorio_sink", "bind"))
pub  = ctx.socket(zmq.PUB);  pub.bind(get_zmq_address("relatorio", "bind"))

N_SUBTAREFAS = 4

# Conjunto representativo de TCCs (modo offline). Com MySQL, viria de
# SELECT em propostas/historico_eventos. O panorama agrega estes registros.
DATASET = [
    {"aluno_id": 1,  "status": "em_desenvolvimento", "area": "Sistemas Distribuidos",  "defesa_no_prazo": True},
    {"aluno_id": 2,  "status": "defesa_aprovada",    "area": "Inteligencia Artificial","defesa_no_prazo": True},
    {"aluno_id": 3,  "status": "proposta_aprovada",  "area": "Redes",                  "defesa_no_prazo": False},
    {"aluno_id": 4,  "status": "em_desenvolvimento", "area": "Sistemas Distribuidos",  "defesa_no_prazo": True},
    {"aluno_id": 5,  "status": "defesa_aprovada",    "area": "Banco de Dados",         "defesa_no_prazo": False},
    {"aluno_id": 6,  "status": "pendente",           "area": "Inteligencia Artificial","defesa_no_prazo": False},
    {"aluno_id": 7,  "status": "defesa_aprovada",    "area": "Sistemas Distribuidos",  "defesa_no_prazo": True},
    {"aluno_id": 8,  "status": "em_desenvolvimento", "area": "Redes",                  "defesa_no_prazo": True},
    {"aluno_id": 9,  "status": "proposta_aprovada",  "area": "Inteligencia Artificial","defesa_no_prazo": False},
    {"aluno_id": 10, "status": "defesa_aprovada",    "area": "Banco de Dados",         "defesa_no_prazo": True},
]


def gerar(tipo: str, solicitante: str):
    chunks = [DATASET[i::N_SUBTAREFAS] for i in range(N_SUBTAREFAS)]
    for i, chunk in enumerate(chunks):
        vent.send_string(json.dumps({"chunk_id": i, "registros": chunk}))
    log.info(f"solicitacao '{tipo}' de {solicitante}: {len(chunks)} subtarefas ventiladas aos workers")

    total = defesas = recebidos = 0
    por_status, por_area = {}, {}
    while recebidos < len(chunks):
        parcial = json.loads(sink.recv_string())
        recebidos += 1
        total += parcial["total"]
        defesas += parcial["defesas_no_prazo"]
        for k, v in parcial["por_status"].items(): por_status[k] = por_status.get(k, 0) + v
        for k, v in parcial["por_area"].items():   por_area[k]   = por_area.get(k, 0) + v
        log.info(f"parcial recebido do sink ({recebidos}/{len(chunks)})")

    panorama = {"tipo": tipo, "solicitante": solicitante, "total_tccs": total,
                "por_status": por_status, "por_area": por_area, "defesas_no_prazo": defesas}
    ev = Evento(TipoEvento.RELATORIO_GERADO, aluno_id=0, operacao="gerar_relatorio", payload=panorama)
    pub.send_string(f"{ev.evento} {ev.to_json_str()}")
    log.info(f"panorama consolidado e publicado: {panorama}")
    return panorama


if __name__ == "__main__":
    log.info("no ar | PUSH/PULL: ventila subtarefas -> workers -> sink -> consolida -> PUB relatorio_gerado")
    try:
        while True:
            try:
                pedido = json.loads(req.recv_string())
                time.sleep(0.3)   # folga p/ os workers conectarem ao ventilador
                gerar(pedido.get("tipo", "geral"), pedido.get("solicitante", "coordenador"))
            except Exception as e:
                log.error(f"erro ao gerar relatorio: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        req.close(); vent.close(); sink.close(); pub.close(); ctx.term()
