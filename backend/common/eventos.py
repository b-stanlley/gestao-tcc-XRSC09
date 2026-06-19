"""Tipos de evento e a estrutura de mensagem do sistema.
Mensagem (tupla do relatorio): m = (e, o, i, t, d)
  e = evento (topico)   o = operacao   i = id (idempotencia)
  t = timestamp         d = payload (dados em JSON)
"""
from enum import Enum
from datetime import datetime
import uuid
import json


class TipoEvento(Enum):
    # Entrada do cliente (injetada pelo gateway na malha)
    VERSAO_RECEBIDA = "versao_recebida"        # gateway -> Documentos
    PARECER_RECEBIDO = "parecer_recebido"      # gateway -> Feedback & Avaliacao

    # Cenario implementado: submissao e revisao
    VERSAO_SUBMETIDA = "versao_submetida"              # Documentos -> IA
    RECOMENDACAO_IA_GERADA = "recomendacao_ia_gerada"  # IA -> Notificacoes
    FEEDBACK_ENVIADO = "feedback_enviado"              # Feedback & Avaliacao -> IA
    FEEDBACK_ATENDIDO = "feedback_atendido"            # IA -> Notificacoes
    PENDENCIAS_IDENTIFICADAS = "pendencias_identificadas"  # IA -> Notificacoes
    ALERTA_PENDENCIA_DISPARADO = "alerta_pendencia_disparado"  # Notificacoes -> Orientador

    # Cenario 1 — Proposta (entrada do cliente + reacoes)
    PROPOSTA_RECEBIDA = "proposta_recebida"            # gateway -> Propostas (discente submete)
    PROPOSTA_AVALIADA = "proposta_avaliada"            # gateway -> Propostas (orientador avalia)
    PROPOSTA_SUBMETIDA = "proposta_submetida"          # Propostas -> Coordenacao/Orientador
    PROPOSTA_APROVADA = "proposta_aprovada"
    PROPOSTA_REJEITADA = "proposta_rejeitada"
    PROPOSTA_AJUSTES = "proposta_ajustes_solicitados"
    CRONOGRAMA_REGISTRADO = "cronograma_registrado"    # opcional (orientador escolhe)
    ENTREGA_CRIADA = "entrega_criada"                  # coordenador cria entrega dinamica

    # Cenario 2 — Banca e defesa
    APTO_PARA_DEFESA = "apto_para_defesa"
    BANCA_DEFINIDA = "banca_definida"                  # gateway(orientador) -> Bancas
    BANCA_COMPOSTA = "banca_composta"
    DEFESA_AGENDADA = "defesa_agendada"                # Bancas -> Notificacoes/Discente
    CONVOCACAO_BANCA_ENVIADA = "convocacao_banca_enviada"
    NOTA_BANCA_SUBMETIDA = "nota_banca_submetida"      # gateway(banca) -> Bancas
    DEFESA_APROVADA = "defesa_aprovada"                # Bancas -> Notificacoes
    DEFESA_REPROVADA = "defesa_reprovada"

    # Cenario 3 — Relatorios
    RELATORIO_GERADO = "relatorio_gerado"


class Evento:
    """Mensagem trafegada na malha. Serializa para JSON no formato (e,o,i,t,d)."""
    def __init__(self, tipo: TipoEvento, aluno_id: int, payload: dict,
                 operacao: str = "", **kwargs):
        self.evento = tipo.value        # e
        self.operacao = operacao        # o
        self.id = str(uuid.uuid4())     # i (idempotencia)
        self.timestamp = datetime.now().isoformat()  # t
        self.aluno_id = aluno_id
        self.payload = payload          # d
        self.__dict__.update(kwargs)

    def to_dict(self):
        return self.__dict__

    def to_json_str(self):
        return json.dumps(self.to_dict())

    def __str__(self):
        return f"[{self.evento}] aluno={self.aluno_id} op={self.operacao} id={self.id[:8]}"
