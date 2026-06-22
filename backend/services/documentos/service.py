"""Servico de Documentos & Versoes — Cenario 1 (PUB/SUB).

Protagonista do cenario de submissao/revisao. Estruturado conforme o C4 Nivel 4
(Codigo) do relatorio: classes ServicoDocumentos, Documento, Versao e
RepositorioDocumentos (alem da classe Evento, em common/eventos.py).

Coreografia: SUB gateway:versao_recebida -> versiona/persiste (DAO/MySQL) ->
PUB versao_submetida. Sem orquestrador; a IA reage diretamente ao evento publicado.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import zmq
from datetime import datetime
from common.eventos import Evento, TipoEvento
from common.config import get_zmq_address
from common.logger import criar_logger
from common.db import Repositorio

log = criar_logger("Documentos")


class Documento:
    """Entidade do TCC de um discente (C4 N4)."""
    def __init__(self, tcc_id, titulo=""):
        self.id = tcc_id
        self.tcc_id = tcc_id
        self.titulo = titulo


class Versao:
    """Versao de um Documento (C4 N4): numero, arquivo (texto/blob), status, criada_em."""
    def __init__(self, numero, arquivo, tipo="desenvolvimento", status="vigente", criada_em=None):
        self.numero = numero
        self.arquivo = arquivo
        self.tipo = tipo
        self.status = status
        self.criada_em = criada_em or datetime.now().isoformat()


class RepositorioDocumentos:
    """DAO de Documentos (C4 N4 / RNF02). Encapsula o Repositorio (MySQL + fallback
    em memoria) expondo a interface salvar(Versao)/buscarVigente(tcc)."""
    def __init__(self, repo=None):
        self._repo = repo or Repositorio()

    def evento_novo(self, evento):
        return self._repo.registrar_evento(evento)  # idempotencia (RNF05)

    def salvar(self, tcc_id, versao: "Versao") -> int:
        numero = self._repo.salvar_versao(tcc_id, versao.arquivo, versao.tipo)
        versao.numero = numero
        return numero

    def buscarVigente(self, tcc_id) -> "Versao":
        texto = self._repo.texto_versao_vigente(tcc_id)
        return Versao(numero=None, arquivo=texto) if texto is not None else None

    def fechar(self):
        self._repo.fechar()


class ServicoDocumentos:
    """Peer de Documentos & Versoes (C4 N3/N4): Assinante (SUB) -> Controle de
    Versoes -> Repositorio (DAO) -> Publicador (PUB)."""
    def __init__(self):
        self.ctx = zmq.Context.instance()
        self.sub = self.ctx.socket(zmq.SUB)
        self.sub.connect(get_zmq_address("gateway"))
        self.sub.setsockopt_string(zmq.SUBSCRIBE, TipoEvento.VERSAO_RECEBIDA.value)
        self.pub = self.ctx.socket(zmq.PUB) # Publica em seu próprio canal
        self.pub.bind(get_zmq_address("documentos", "bind"))
        self.repo = RepositorioDocumentos()
        log.info("no ar | SUB gateway:versao_recebida -> versiona/persiste -> PUB versao_submetida")

    def versionar(self, documento: Documento, payload: dict) -> Versao:
        """Controle de Versoes: monta a nova Versao a partir do payload recebido."""
        return Versao(numero=None, arquivo=payload.get("texto", ""),
                      tipo=payload.get("tipo", "desenvolvimento"))

    def persistir(self, documento: Documento, versao: Versao) -> int:
        """Persiste a versao via DAO (fonte da verdade)."""
        return self.repo.salvar(documento.tcc_id, versao)

    def publicar(self, evento: Evento):
        self.pub.send_string(f"{evento.evento} {evento.to_json_str()}")

    def consumir(self, dados: dict):
        """Reage a um versao_recebida: versiona, persiste e publica versao_submetida."""
        if not self.repo.evento_novo(dados):  # idempotencia
            log.info("evento ja processado; ignorado (idempotencia)")
            return
        documento = Documento(tcc_id=dados["aluno_id"])
        versao = self.versionar(documento, dados.get("payload", {}))
        numero = self.persistir(documento, versao)
        ev = Evento(TipoEvento.VERSAO_SUBMETIDA, aluno_id=documento.tcc_id, operacao="versionar",
                    payload={"versao_id": numero, "numero": numero, "tipo": versao.tipo,
                             "texto": versao.arquivo, "caracteres": len(versao.arquivo or ""),
                             "entrega_id": dados.get("payload", {}).get("entrega_id")})
        self.publicar(ev)
        log.info(f"versao v{numero} persistida; publicado {ev}")

    def run(self):
        try:
            while True:
                try:
                    _, c = self.sub.recv_string().split(" ", 1)
                    self.consumir(json.loads(c))
                except Exception as e:                      # uma mensagem ruim nao derruba o servico
                    log.error(f"erro ao processar evento: {e}")
        except KeyboardInterrupt:
            pass
        finally:
            self.sub.close(); self.pub.close(); self.repo.fechar(); self.ctx.term()


if __name__ == "__main__":
    ServicoDocumentos().run()
