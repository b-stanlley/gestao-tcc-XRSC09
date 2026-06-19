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
class ServicoPropostas:
    def __init__(self):
        self.ctx = zmq.Context.instance()
        self.sub = self.ctx.socket(zmq.SUB)
        self.sub.connect(get_zmq_address("gateway"))
        for t in (TipoEvento.PROPOSTA_RECEBIDA, TipoEvento.PROPOSTA_AVALIADA, TipoEvento.CRONOGRAMA_REGISTRADO):
            self.sub.setsockopt_string(zmq.SUBSCRIBE, t.value)
        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.bind(get_zmq_address("propostas", "bind"))
        self.repo = Repositorio()
        self._propostas = {}  # Estado leve por aluno (fallback offline)
        log.info("no ar | SUB gateway:proposta_recebida/avaliada -> PUB proposta_submetida/aprovada/rejeitada")
    def _publicar(self, tipo, aluno, operacao, payload):
        ev = Evento(tipo, aluno_id=aluno, operacao=operacao, payload=payload)
        self.pub.send_string(f"{ev.evento} {ev.to_json_str()}")
        log.info(f"publicado {ev}")
    def on_proposta_recebida(self, dados):
        aluno = dados["aluno_id"]
        p = dados.get("payload", {})
        self._propostas[aluno] = {"titulo": p.get("titulo", ""), "resumo": p.get("resumo", ""), "status": "submetida"}
        self._publicar(TipoEvento.PROPOSTA_SUBMETIDA, aluno, "submeter_proposta",
                       {"id": dados.get("id"), "titulo": p.get("titulo", ""), "resumo": p.get("resumo", ""),
                        "para": ["coordenacao", "orientador"]})
    def on_proposta_avaliada(self, dados):
        aluno = dados["aluno_id"]
        p = dados.get("payload", {})
        decisao = (p.get("decisao") or "").lower()
        if decisao == "aprovada" or decisao == "aprovado":
            self._propostas.setdefault(aluno, {})["status"] = "aprovada"
            self._publicar(TipoEvento.PROPOSTA_APROVADA, aluno, "aprovar_proposta",
                           {"para": ["coordenacao", "discente"]})
        else:
            self._propostas.setdefault(aluno, {})["status"] = "rejeitada"
            self._publicar(TipoEvento.PROPOSTA_REJEITADA, aluno, "rejeitar_proposta",
                           {"motivo": p.get("motivo", ""), "para": ["notificacoes", "discente"]})
    def on_cronograma(self, dados):
        aluno = dados["aluno_id"]
        self._publicar(TipoEvento.CRONOGRAMA_REGISTRADO, aluno, "registrar_cronograma",
                       dados.get("payload", {}))
    def run(self):
        handlers = {
            TipoEvento.PROPOSTA_RECEBIDA.value: self.on_proposta_recebida,
            TipoEvento.PROPOSTA_AVALIADA.value: self.on_proposta_avaliada,
            TipoEvento.CRONOGRAMA_REGISTRADO.value: self.on_cronograma,
        }
        try:
            while True:
                try:
                    topico, c = self.sub.recv_string().split(" ", 1)
                    dados = json.loads(c)
                    if not self.repo.registrar_evento(dados):
                        continue
                    handler = handlers.get(topico)
                    if handler:
                        handler(dados)
                except Exception as e:
                    log.error(f"erro ao processar evento: {e}")
        except KeyboardInterrupt:
            pass
        finally:
            self.sub.close()
            self.pub.close()
            self.repo.fechar()
            self.ctx.term()
if __name__ == "__main__":
    ServicoPropostas().run()
