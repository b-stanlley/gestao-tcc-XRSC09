"""Servico de Notificacoes & Alertas (PUB/SUB) — RF05.

Reage a eventos da IA (Cenario 1) e das Bancas (Cenario 2), registra a
notificacao (persistida) e, quando cabivel, publica alertas/convocacoes.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import zmq, json
from common.eventos import Evento, TipoEvento
from common.config import get_zmq_address
from common.logger import criar_logger
from common.db import Repositorio

log = criar_logger("Notificacoes")
ctx = zmq.Context.instance()

sub_ia = ctx.socket(zmq.SUB); sub_ia.connect(get_zmq_address("ia"))
for t in (TipoEvento.RECOMENDACAO_IA_GERADA, TipoEvento.FEEDBACK_ATENDIDO, TipoEvento.PENDENCIAS_IDENTIFICADAS):
    sub_ia.setsockopt_string(zmq.SUBSCRIBE, t.value)

sub_banca = ctx.socket(zmq.SUB); sub_banca.connect(get_zmq_address("banca"))
for t in (TipoEvento.DEFESA_AGENDADA, TipoEvento.DEFESA_APROVADA, TipoEvento.DEFESA_REPROVADA):
    sub_banca.setsockopt_string(zmq.SUBSCRIBE, t.value)

pub = ctx.socket(zmq.PUB); pub.bind(get_zmq_address("notificacao", "bind"))
repo = Repositorio()
log.info("no ar | SUB ia + banca -> notifica (persistida); PUB alerta_pendencia_disparado / convocacao_banca_enviada")


def notificar(role, aluno, tipo, msg):
    repo.salvar_notificacao(role, aluno, tipo, msg)
    log.info(f"[notif->{role}] {msg} (aluno {aluno})")


def handle(topico, dados):
    if not repo.registrar_evento(dados):       # idempotencia
        return
    aluno = dados["aluno_id"]
    if topico == TipoEvento.RECOMENDACAO_IA_GERADA.value:
        notificar("orientador", aluno, topico, "Nova recomendacao da IA disponivel")
    elif topico == TipoEvento.FEEDBACK_ATENDIDO.value:
        notificar("discente", aluno, topico, "Feedback atendido")
    elif topico == TipoEvento.PENDENCIAS_IDENTIFICADAS.value:
        notificar("orientador", aluno, topico, "Pendencias identificadas")
        ev = Evento(TipoEvento.ALERTA_PENDENCIA_DISPARADO, aluno_id=aluno, operacao="alertar",
                    payload={"para": ["orientador", "coorientador"], "motivo": "pendencias_identificadas"})
        pub.send_string(f"{ev.evento} {ev.to_json_str()}")
    elif topico == TipoEvento.DEFESA_AGENDADA.value:
        notificar("banca", aluno, topico, "Convocacao: defesa agendada")
        ev = Evento(TipoEvento.CONVOCACAO_BANCA_ENVIADA, aluno_id=aluno, operacao="convocar",
                    payload=dados.get("payload", {}))
        pub.send_string(f"{ev.evento} {ev.to_json_str()}")
    elif topico == TipoEvento.DEFESA_APROVADA.value:
        notificar("discente", aluno, topico, "Defesa APROVADA")
    elif topico == TipoEvento.DEFESA_REPROVADA.value:
        notificar("discente", aluno, topico, "Defesa reprovada")


if __name__ == "__main__":
    poller = zmq.Poller()
    poller.register(sub_ia, zmq.POLLIN)
    poller.register(sub_banca, zmq.POLLIN)
    try:
        while True:
            socks = dict(poller.poll(1000))
            try:
                for s in (sub_ia, sub_banca):
                    if s in socks:
                        _, c = s.recv_string().split(" ", 1)
                        d = json.loads(c)
                        handle(d["evento"], d)
            except Exception as e:
                log.error(f"erro ao processar evento: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        sub_ia.close(); sub_banca.close(); pub.close(); repo.fechar(); ctx.term()
