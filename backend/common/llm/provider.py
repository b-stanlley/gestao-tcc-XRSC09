"""Provedor de LLM plugavel (interface + implementacoes).
Materializa a classe ProvedorLLM do C4 Nivel 4. Selecao por env LLM_PROVIDER.
"""
from abc import ABC, abstractmethod
from common.config import LLM_CONFIG
from common.logger import criar_logger

logger = criar_logger("LLM")


class ProvedorLLM(ABC):
    @abstractmethod
    def analisar(self, texto: str, modo: str = "geral") -> dict:
        """Retorna {'status','recomendacoes','score','observacoes'}."""
        ...


class SimuladoProvider(ProvedorLLM):
    """Heuristica local, sem rede. Default para demonstracao offline."""
    def analisar(self, texto: str, modo: str = "geral") -> dict:
        n = len(texto or "")
        if modo == "feedback_atendimento":
            atendido = n >= 500
            return {"status": "apto" if atendido else "pendente",
                    "recomendacoes": [] if atendido else ["Revisar pontos do feedback anterior"],
                    "score": min(100, n / 10), "observacoes": "Reavaliacao simulada"}
        if n < 500:
            return {"status": "pendente",
                    "recomendacoes": ["Expandir a metodologia", "Adicionar exemplos", "Revisar referencias"],
                    "score": round(n / 10, 1), "observacoes": "Texto incompleto (simulado)"}
        return {"status": "apto", "recomendacoes": [], "score": 90.0,
                "observacoes": "Atende aos requisitos basicos (simulado)"}


class OllamaProvider(ProvedorLLM):
    """Chama um modelo local via Ollama (HTTP). Unica chamada nao-ZeroMQ do sistema."""
    def __init__(self):
        import requests
        self._requests = requests
        self.url = LLM_CONFIG["ollama_url"]
        self.model = LLM_CONFIG["ollama_model"]
        self.timeout = LLM_CONFIG["timeout"]

    def analisar(self, texto: str, modo: str = "geral") -> dict:
        prompt = (
            "Voce avalia um trecho de TCC. Responda em JSON com as chaves "
            "status (apto|pendente), recomendacoes (lista), score (0-100), observacoes.\n\n"
            f"Modo: {modo}\nTrecho:\n{texto[:4000]}"
        )
        try:
            r = self._requests.post(self.url, json={"model": self.model, "prompt": prompt,
                                    "stream": False, "format": "json"}, timeout=self.timeout)
            r.raise_for_status()
            import json as _json
            data = _json.loads(r.json().get("response", "{}"))
            data.setdefault("status", "pendente")
            return data
        except Exception as e:
            logger.warning(f"Ollama indisponivel ({e}); usando fallback simulado.")
            return SimuladoProvider().analisar(texto, modo)


class HttpProvider(ProvedorLLM):
    """Consulta um Provedor de LLM por HTTP/JSON (ex.: o stub local em llm/stub_server.py).
    Materializa, ao vivo, a seta 'consulta (HTTP/JSON)' do diagrama de sequencia.
    Usa urllib (biblioteca padrao) -> nao requer dependencia extra. Em caso de falha,
    cai no SimuladoProvider para nao interromper a coreografia."""
    def __init__(self):
        self.url = LLM_CONFIG["url"]
        self.timeout = LLM_CONFIG["timeout"]

    def analisar(self, texto: str, modo: str = "geral") -> dict:
        import json as _json
        import urllib.request as _req
        try:
            corpo = _json.dumps({"texto": texto, "modo": modo}).encode("utf-8")
            requisicao = _req.Request(self.url, data=corpo,
                                      headers={"Content-Type": "application/json"})
            with _req.urlopen(requisicao, timeout=self.timeout) as resp:
                data = _json.loads(resp.read().decode("utf-8"))
            data.setdefault("status", "pendente")
            return data
        except Exception as e:
            logger.warning(f"Provedor de LLM HTTP indisponivel ({e}); usando fallback simulado.")
            return SimuladoProvider().analisar(texto, modo)


def get_provedor() -> ProvedorLLM:
    nome = LLM_CONFIG["provider"].lower()
    if nome == "http":
        logger.info(f"Provedor de LLM: HTTP ({LLM_CONFIG['url']})")
        return HttpProvider()
    if nome == "ollama":
        logger.info("Provedor de LLM: Ollama")
        return OllamaProvider()
    logger.info("Provedor de LLM: Simulado")
    return SimuladoProvider()
