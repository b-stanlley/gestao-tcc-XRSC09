"""Stub de Provedor de LLM por HTTP (offline, sem modelo pesado).

Representa a linha de vida "Provedor de LLM (HTTP)" do diagrama de sequencia:
o Servico de IA consulta este servidor por HTTP/JSON e recebe a analise.
Por baixo usa a mesma heuristica do SimuladoProvider, mas a chamada e' HTTP de verdade.

Como usar (cenario fiel ao diagrama):
    1) rode este servidor:        python common/llm/stub_server.py
    2) selecione no Servico de IA: LLM_PROVIDER=http   (e, se preciso, LLM_URL)

Usa apenas a biblioteca padrao do Python (http.server) -> nao precisa de Flask.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from common.llm.provider import SimuladoProvider
from common.config import LLM_CONFIG
from common.logger import criar_logger

log = criar_logger("LLM-HTTP")
_provedor = SimuladoProvider()


class Handler(BaseHTTPRequestHandler):
    def _responder(self, code: int, obj: dict):
        corpo = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_POST(self):
        try:
            tam = int(self.headers.get("Content-Length", 0))
            dados = json.loads(self.rfile.read(tam) or b"{}")
            texto = dados.get("texto", "")
            modo = dados.get("modo", "geral")
            resultado = _provedor.analisar(texto, modo)   # monta a "resposta" do LLM
            log.info(f"consulta HTTP recebida (modo={modo}) -> status={resultado.get('status')}")
            self._responder(200, resultado)
        except Exception as e:
            self._responder(500, {"erro": str(e), "status": "pendente"})

    def do_GET(self):   # health check simples
        self._responder(200, {"servico": "Provedor de LLM (stub HTTP)", "status": "ok"})

    def log_message(self, *args):   # silencia o log padrao do http.server
        pass


if __name__ == "__main__":
    porta = LLM_CONFIG["stub_port"]
    log.info(f"Provedor de LLM (stub HTTP) no ar em http://localhost:{porta}/analisar")
    # 0.0.0.0 -> acessivel tambem de outra maquina (multi-maquina)
    ThreadingHTTPServer(("0.0.0.0", porta), Handler).serve_forever()
