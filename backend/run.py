"""Sobe a malha brokerless (8 peers Python sobre ZeroMQ) + o BFF, num comando.

Ordem importa por causa do "slow joiner" do PUB/SUB: os consumidores sobem antes
dos publicadores; o BFF (que injeta comandos) sobe por ultimo.

Modo offline por padrao: sem MySQL (fallback em memoria) e LLM 'simulado' (em processo).
Para o provedor de LLM via HTTP (fiel ao diagrama de sequencia):  set LLM_PROVIDER=http

Uso:
    python backend/run.py
Depois, em outro terminal, suba a interface:  npm run dev   (Vite, com proxy /api -> :3000)
"""
import subprocess, sys, os, time

base = os.path.dirname(os.path.abspath(__file__))


def peer(rel):
    return subprocess.Popen([sys.executable, os.path.join(base, *rel.split("/"))])


# Consumidores/servicos primeiro; workers do relatorio depois; BFF por ultimo.
PEERS = [
    "services/notificacao/service.py",
    "services/ia/service.py",
    "services/avaliacao/service.py",
    "services/propostas/service.py",
    "services/documentos/service.py",
    "services/banca/service.py",
    "services/autenticacao/service.py",
    "services/relatorios/service.py",
    "services/relatorios/worker.py",
    "services/relatorios/worker.py",   # 2 workers (paralelismo do PUSH/PULL)
]

if os.getenv("LLM_PROVIDER", "simulado").lower() == "http":
    PEERS.insert(0, "common/llm/stub_server.py")

procs = []
print("== subindo a malha brokerless (consumidores primeiro) ==", flush=True)
for s in PEERS:
    procs.append(peer(s))
    time.sleep(0.4)

time.sleep(1.0)
print("== subindo o BFF (HTTP <-> ZeroMQ) ==", flush=True)
procs.append(peer("bff.py"))

print("== tudo no ar. BFF em http://localhost:3000/api • suba a interface com `npm run dev`. "
      "Ctrl+C encerra tudo. ==", flush=True)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    for p in procs:
        p.terminate()
    for p in procs:
        try:
            p.wait(timeout=3)
        except Exception:
            p.kill()
