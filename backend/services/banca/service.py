"""Servico de Bancas & Defesas — Cenario 2 (PUB/SUB).

Reage a comandos injetados pelo gateway:
  banca_definida       (orientador compoe a banca) -> persiste + PUB defesa_agendada
  nota_banca_submetida (banca registra a nota)     -> regra nota>=6 -> PUB defesa_aprovada|defesa_reprovada

Cobre os sub-problemas (v) composicao de bancas e agendamento de defesas
(RF06/RF07) e materializa a 'atribuicao de revisores' do JEMS.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import zmq
from common.eventos import Evento, TipoEvento
from common.config import get_zmq_address
from common.logger import criar_logger
from common.db import Repositorio

log = criar_logger("Bancas&Defesas")
ctx = zmq.Context.instance()
sub = ctx.socket(zmq.SUB)
sub.connect(get_zmq_address("gateway"))
for t in (TipoEvento.BANCA_DEFINIDA, TipoEvento.NOTA_BANCA_SUBMETIDA):
    sub.setsockopt_string(zmq.SUBSCRIBE, t.value)
pub = ctx.socket(zmq.PUB)
pub.bind(get_zmq_address("banca", "bind"))
repo = Repositorio()
log.info("no ar | SUB gateway:banca_definida/nota_banca_submetida -> PUB defesa_agendada / defesa_aprovada|reprovada")

# guarda o id da banca por aluno (para vincular a nota a defesa) — fallback offline
_banca_por_aluno = {}


def on_banca_definida(dados):
    aluno = dados["aluno_id"]
    p = dados.get("payload", {})
    avaliadores = p.get("avaliadores", [])
    data_defesa = p.get("data_defesa")
    orientador_id = p.get("orientador_id")
    banca_id = repo.salvar_banca(aluno, orientador_id, data_defesa, avaliadores)
    _banca_por_aluno[aluno] = banca_id
    ev = Evento(TipoEvento.DEFESA_AGENDADA, aluno_id=aluno, operacao="agendar_defesa",
                payload={"avaliadores": avaliadores, "data_defesa": data_defesa, "banca_id": banca_id})
    pub.send_string(f"{ev.evento} {ev.to_json_str()}")
    log.info(f"banca definida e defesa agendada p/ aluno {aluno}: {avaliadores} em {data_defesa}")


def on_nota_banca(dados):
    aluno = dados["aluno_id"]
    p = dados.get("payload", {})
    nota = float(p.get("nota", 0))
    comentario = p.get("comentario", "")
    aprovado = nota >= 6.0                         # criterio unico do relatorio
    tipo = TipoEvento.DEFESA_APROVADA if aprovado else TipoEvento.DEFESA_REPROVADA
    resultado = "aprovado" if aprovado else "reprovado"
    repo.salvar_defesa(_banca_por_aluno.get(aluno), aluno, nota, resultado, comentario)
    ev = Evento(tipo, aluno_id=aluno, operacao="avaliar_defesa",
                payload={"nota": nota, "resultado": resultado, "comentario": comentario})
    pub.send_string(f"{ev.evento} {ev.to_json_str()}")
    log.info(f"defesa avaliada p/ aluno {aluno}: nota={nota} -> {resultado}")


HANDLERS = {
    TipoEvento.BANCA_DEFINIDA.value: on_banca_definida,
    TipoEvento.NOTA_BANCA_SUBMETIDA.value: on_nota_banca,
}

if __name__ == "__main__":
    try:
        while True:
            try:
                _, c = sub.recv_string().split(" ", 1)
                dados = json.loads(c)
                if not repo.registrar_evento(dados):        # idempotencia
                    continue
                handler = HANDLERS.get(dados.get("evento"))
                if handler:
                    handler(dados)
            except Exception as e:
                log.error(f"erro ao processar evento: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        sub.close(); pub.close(); repo.fechar(); ctx.term()
