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


class GeminiProvider(ProvedorLLM):
    """Consulta a API do Google Gemini (HTTP/JSON) via urllib (sem dependencia extra).
    Pronto para conectar: defina GEMINI_API_KEY e LLM_PROVIDER=gemini (e, se quiser,
    GEMINI_MODEL). Sem chave / em caso de erro, cai no SimuladoProvider — a coreografia
    nao para. A chamada ao Gemini e a unica chamada nao-ZeroMQ do Servico de IA."""
    def __init__(self):
        self.api_key = LLM_CONFIG.get("gemini_api_key", "")
        self.model = LLM_CONFIG.get("gemini_model", "gemini-3.5-flash")
        self.timeout = LLM_CONFIG["timeout"]

    def analisar(self, texto: str, modo: str = "geral") -> dict:
        import json as _json
        import urllib.request as _req
        if not self.api_key:
            logger.warning("GEMINI_API_KEY ausente; usando fallback simulado.")
            return SimuladoProvider().analisar(texto, modo)
        prompt = (
            "Voce avalia um trecho de TCC. Responda SOMENTE com um JSON com as chaves: "
            "status (\"apto\" ou \"pendente\"), recomendacoes (lista de strings), "
            "score (numero 0-100) e observacoes (string).\n\n"
            f"Modo: {modo}\nTrecho:\n{(texto or '')[:4000]}"
        )
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:generateContent?key={self.api_key}")
        corpo = _json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"},
        }).encode("utf-8")
        try:
            requisicao = _req.Request(url, data=corpo, headers={"Content-Type": "application/json"})
            with _req.urlopen(requisicao, timeout=self.timeout) as resp:
                resposta = _json.loads(resp.read().decode("utf-8"))
            texto_json = resposta["candidates"][0]["content"]["parts"][0]["text"]
            data = _json.loads(texto_json)
            data.setdefault("status", "pendente")
            data.setdefault("recomendacoes", [])
            data.setdefault("score", 0)
            data.setdefault("observacoes", "")
            return data
        except Exception as e:
            logger.warning(f"Gemini indisponivel ({e}); usando fallback simulado.")
            return SimuladoProvider().analisar(texto, modo)


def get_provedor() -> ProvedorLLM:
    nome = LLM_CONFIG["provider"].lower()
    if nome == "gemini":
        logger.info(f"Provedor de LLM: Gemini ({LLM_CONFIG.get('gemini_model')})")
        return GeminiProvider()
    if nome == "http":
        logger.info(f"Provedor de LLM: HTTP ({LLM_CONFIG['url']})")
        return HttpProvider()
    if nome == "ollama":
        logger.info("Provedor de LLM: Ollama")
        return OllamaProvider()
    logger.info("Provedor de LLM: Simulado")
    return SimuladoProvider()
