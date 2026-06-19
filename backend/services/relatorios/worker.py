"""Worker de Relatorios — consumidor do pipeline PUSH/PULL.

Conecta-se ao ventilador (PULL) e ao sink (PUSH) do coordenador. Em laco:
puxa uma subtarefa, agrega a sua fatia de registros e devolve o parcial.
Pode-se subir VARIOS workers em paralelo (round-robin distribui as subtarefas).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import zmq
from common.config import get_zmq_address
from common.logger import criar_logger

log = criar_logger("Relatorios-Worker")
ctx = zmq.Context.instance()
pull = ctx.socket(zmq.PULL); pull.connect(get_zmq_address("relatorio_vent"))
push = ctx.socket(zmq.PUSH); push.connect(get_zmq_address("relatorio_sink"))
log.info("worker no ar | PULL subtarefa -> agrega -> PUSH parcial ao sink")


def agregar(registros):
    por_status, por_area, defesas = {}, {}, 0
    for r in registros:
        s = r.get("status", "?"); por_status[s] = por_status.get(s, 0) + 1
        a = r.get("area", "?");   por_area[a]   = por_area.get(a, 0) + 1
        if r.get("defesa_no_prazo"):
            defesas += 1
    return {"total": len(registros), "por_status": por_status,
            "por_area": por_area, "defesas_no_prazo": defesas}


if __name__ == "__main__":
    try:
        while True:
            try:
                tarefa = json.loads(pull.recv_string())
                parcial = agregar(tarefa.get("registros", []))
                push.send_string(json.dumps(parcial))
                log.info(f"chunk {tarefa.get('chunk_id')} agregado: {parcial['total']} registros")
            except Exception as e:
                log.error(f"erro no worker: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        pull.close(); push.close(); ctx.term()
