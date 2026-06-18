"""Servico de Propostas & Cronograma — Cenario 1 (PUB/SUB).

Reage a comandos injetados pelo gateway na malha brokerless:
  proposta_recebida   (discente submete a proposta) -> persiste -> PUB proposta_submetida
  proposta_avaliada   (orientador avalia)            -> PUB proposta_aprovada | proposta_rejeitada
  cronograma_registrado (orientador + discente, opcional) -> PUB cronograma_registrado

Cobre o sub-problema (i)/(iii) (acompanhamento e coordenacao) e a etapa de Proposta
do BPMN. Coreografia pura: nenhum orquestrador; os interessados (Notificacoes, IA,
Coordenacao/Orientador) reagem aos eventos publicados aqui.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import zmq
from common.eventos import Evento, TipoEvento
from common.config import get_zmq_address
from common.logger import criar_logger
from common.db import Repositorio

log = criar_logger("Propostas&Cronograma")
ctx = zmq.Context.instance()
sub = ctx.socket(zmq.SUB)
sub.connect(get_zmq_address("gateway"))
for t in (TipoEvento.PROPOSTA_RECEBIDA, TipoEvento.PROPOSTA_AVALIADA,
          TipoEvento.CRONOGRAMA_REGISTRADO):
    sub.setsockopt_string(zmq.SUBSCRIBE, t.value)
pub = ctx.socket(zmq.PUB)
pub.bind(get_zmq_address("propostas", "bind"))
repo = Repositorio()
log.info("no ar | SUB gateway:proposta_recebida/proposta_avaliada/cronograma_registrado "
         "-> PUB proposta_submetida/aprovada/rejeitada")

# Estado leve por aluno (fallback offline; a fonte da verdade seria o MySQL).
_propostas = {}


def _publicar(tipo, aluno, operacao, payload):
    ev = Evento(tipo, aluno_id=aluno, operacao=operacao, payload=payload)
    pub.send_string(f"{ev.evento} {ev.to_json_str()}")
    log.info(f"publicado {ev}")


def on_proposta_recebida(dados):
    aluno = dados["aluno_id"]
    p = dados.get("payload", {})
    _propostas[aluno] = {"titulo": p.get("titulo", ""), "resumo": p.get("resumo", ""),
                         "status": "submetida"}
    # interessados: Coordenacao e Orientador
    _publicar(TipoEvento.PROPOSTA_SUBMETIDA, aluno, "submeter_proposta",
              {"titulo": p.get("titulo", ""), "resumo": p.get("resumo", ""),
               "para": ["coordenacao", "orientador"]})


def on_proposta_avaliada(dados):
    aluno = dados["aluno_id"]
    p = dados.get("payload", {})
    decisao = (p.get("decisao") or "").lower()
    if decisao == "aprovada" or decisao == "aprovado":
        _propostas.setdefault(aluno, {})["status"] = "aprovada"
        _publicar(TipoEvento.PROPOSTA_APROVADA, aluno, "aprovar_proposta",
                  {"para": ["coordenacao", "discente"]})
    else:
        _propostas.setdefault(aluno, {})["status"] = "rejeitada"
        _publicar(TipoEvento.PROPOSTA_REJEITADA, aluno, "rejeitar_proposta",
                  {"motivo": p.get("motivo", ""), "para": ["notificacoes", "discente"]})


def on_cronograma(dados):
    aluno = dados["aluno_id"]
    # cronograma e OPCIONAL: o orientador escolhe registrar ou nao.
    _publicar(TipoEvento.CRONOGRAMA_REGISTRADO, aluno, "registrar_cronograma",
              dados.get("payload", {}))


HANDLERS = {
    TipoEvento.PROPOSTA_RECEBIDA.value: on_proposta_recebida,
    TipoEvento.PROPOSTA_AVALIADA.value: on_proposta_avaliada,
    TipoEvento.CRONOGRAMA_REGISTRADO.value: on_cronograma,
}

if __name__ == "__main__":
    try:
        while True:
            try:
                _, c = sub.recv_string().split(" ", 1)
                dados = json.loads(c)
                if not repo.registrar_evento(dados):       # idempotencia
                    continue
                handler = HANDLERS.get(dados.get("evento"))
                if handler:
                    handler(dados)
            except Exception as e:                          # uma mensagem ruim nao derruba o servico
                log.error(f"erro ao processar evento: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        sub.close(); pub.close(); repo.fechar(); ctx.term()
