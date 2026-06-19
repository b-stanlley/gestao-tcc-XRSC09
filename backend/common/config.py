"""Configuracao centralizada: portas ZeroMQ, banco e provedor de LLM.
Segredos vem de variaveis de ambiente (.env), nunca hardcoded.
"""
import os

# Porta do socket PUB de cada participante da malha
PORTAS = {
    "gateway":     5570,  # PUB do gateway: injeta comandos do cliente na malha
    "documentos":  5555,
    "ia":          5562,
    "avaliacao":   5563,  # Feedback & Avaliacao
    "notificacao": 5566,
    "autenticacao": 5561, # ROUTER (login sincrono, padrao DEALER/ROUTER)
    "propostas":   5556,  # PUB: Propostas & Cronograma (proposta_submetida/aprovada)
    # Servicos do escopo completo (fora do cenario corrigido submissao/revisao),
    # mantidos para os servicos banca/relatorios/submissao do grupo continuarem funcionando.
    "submissao":   5560,
    "banca":       5564,
    "relatorio":   5565,  # PUB: publica relatorio_gerado
    # Pipeline PUSH/PULL dos Relatorios (geracao distribuida por workers)
    "relatorio_req":  5567,  # PULL: recebe solicitacoes de relatorio (gateway/coordenador)
    "relatorio_vent": 5568,  # PUSH: ventila subtarefas aos workers
    "relatorio_sink": 5569,  # PULL: coleta os resultados parciais dos workers
}

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "tcc_db"),
    "autocommit": True,
}

# Provedor de LLM plugavel:
#   "simulado" -> heuristica em processo (offline, zero setup)
#   "http"     -> consulta um Provedor de LLM por HTTP/JSON (o stub local em
#                 common/llm/stub_server.py), tornando real a seta "consulta (HTTP/JSON)"
#                 do diagrama de sequencia, sem internet nem modelo pesado
#   "ollama"   -> modelo local via Ollama (HTTP)
LLM_STUB_PORT = int(os.getenv("LLM_STUB_PORT", "5571"))
LLM_CONFIG = {
    "provider":     os.getenv("LLM_PROVIDER", "simulado"),
    "url":          os.getenv("LLM_URL", f"http://localhost:{LLM_STUB_PORT}/analisar"),
    "stub_port":    LLM_STUB_PORT,
    "ollama_url":   os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate"),
    "ollama_model": os.getenv("OLLAMA_MODEL", "llama3"),
    "timeout":      int(os.getenv("LLM_TIMEOUT", "30")),
}

def get_host(servico: str) -> str:
    """Host (IP) de um peer. Padrao 'localhost' (tudo numa maquina).
    Para multi-maquina, defina HOST_<SERVICO> (ex.: HOST_DOCUMENTOS=192.168.0.10)
    na maquina que precisa se conectar a ele, ou ZMQ_HOST_DEFAULT para todos."""
    return os.getenv(f"HOST_{servico.upper()}",
                     os.getenv("ZMQ_HOST_DEFAULT", "localhost"))

def get_zmq_address(servico: str, tipo: str = "connect") -> str:
    porta = PORTAS.get(servico, 5555)
    if tipo == "bind":
        return f"tcp://*:{porta}"           # ouve em todas as interfaces (acessivel de outra maquina)
    return f"tcp://{get_host(servico)}:{porta}"
