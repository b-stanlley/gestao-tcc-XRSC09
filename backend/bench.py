"""Benchmark da coreografia (cenario de submissao e revisao) - SINTCC / Gestao de TCC.

Coloque este arquivo em  backend/  (ao lado de common/).  Rode a partir da raiz do repo:
    LLM_PROVIDER=simulado python backend/bench.py
ou de dentro de backend/:
    python bench.py

IMPORTANTE: rode-o SOZINHO. Ele faz bind nas portas 5570/5555/5562, entao nao deve
ser executado junto com o run.py (conflito de porta).

Mede, sobre o mesmo transporte (ZeroMQ PUB/SUB), formato de mensagem (classe Evento) e
provedor de IA do sistema: latencia ponta-a-ponta, latencia por salto, vazao e o tempo da
analise da IA. Reproduz a cadeia Documentos -> IA -> Notificacoes em um processo (threads),
para medir de forma estavel e isolar o custo do transporte/processamento.
"""
import sys, os, time, json, threading, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # caminho relativo: pasta backend/
os.environ.setdefault("LLM_PROVIDER", "simulado")                # offline e reproduzivel por padrao
import zmq
from common.eventos import Evento, TipoEvento
from common.llm import get_provedor

ctx = zmq.Context.instance()
provedor = get_provedor()
P = {"gateway": 5570, "documentos": 5555, "ia": 5562}
HWM = 500000

stop = threading.Event()
lat = {"e2e": [], "doc": [], "ia": [], "notif": [], "llm": []}
recv = [0]; first = [None]; last = [None]

def mk_sub(port, topic):
    s = ctx.socket(zmq.SUB); s.setsockopt(zmq.RCVHWM, HWM)
    s.connect(f"tcp://127.0.0.1:{port}"); s.setsockopt_string(zmq.SUBSCRIBE, topic)
    return s

def mk_pub(port):
    s = ctx.socket(zmq.PUB); s.setsockopt(zmq.SNDHWM, HWM)
    s.bind(f"tcp://*:{port}"); return s

def th_doc():
    sub = mk_sub(P["gateway"], TipoEvento.VERSAO_RECEBIDA.value); pub = mk_pub(P["documentos"])
    pl = zmq.Poller(); pl.register(sub, zmq.POLLIN)
    while not stop.is_set():
        if dict(pl.poll(200)):
            _, c = sub.recv_string().split(" ", 1); d = json.loads(c)
            p = d["payload"]; p["_t_doc"] = time.perf_counter()
            ev = Evento(TipoEvento.VERSAO_SUBMETIDA, aluno_id=d["aluno_id"], operacao="versionar", payload=p)
            pub.send_string(f"{ev.evento} {ev.to_json_str()}")

def th_ia():
    sub = mk_sub(P["documentos"], TipoEvento.VERSAO_SUBMETIDA.value); pub = mk_pub(P["ia"])
    pl = zmq.Poller(); pl.register(sub, zmq.POLLIN)
    while not stop.is_set():
        if dict(pl.poll(200)):
            _, c = sub.recv_string().split(" ", 1); d = json.loads(c)
            p = d["payload"]
            t0 = time.perf_counter(); an = provedor.analisar(p.get("texto", ""), "geral")
            lat["llm"].append((time.perf_counter() - t0) * 1000)
            p["_t_ia"] = time.perf_counter(); p["score"] = an.get("score", 0)
            ev = Evento(TipoEvento.RECOMENDACAO_IA_GERADA, aluno_id=d["aluno_id"], operacao="recomendar", payload=p)
            pub.send_string(f"{ev.evento} {ev.to_json_str()}")

def th_notif():
    sub = mk_sub(P["ia"], TipoEvento.RECOMENDACAO_IA_GERADA.value)
    pl = zmq.Poller(); pl.register(sub, zmq.POLLIN)
    while not stop.is_set():
        if dict(pl.poll(200)):
            _, c = sub.recv_string().split(" ", 1); d = json.loads(c)
            now = time.perf_counter(); p = d["payload"]; ti = p["_t_inject"]
            lat["e2e"].append((now - ti) * 1000)
            lat["doc"].append((p["_t_doc"] - ti) * 1000)
            lat["ia"].append((p["_t_ia"] - p["_t_doc"]) * 1000)
            lat["notif"].append((now - p["_t_ia"]) * 1000)
            recv[0] += 1
            if first[0] is None: first[0] = now
            last[0] = now

def stat(xs):
    if not xs: return "sem dados"
    s = sorted(xs); n = len(s); p95 = s[min(n - 1, int(0.95 * n))]
    return f"media {statistics.mean(xs):.2f} | mediana {statistics.median(xs):.2f} | p95 {p95:.2f} | min {min(xs):.2f} | max {max(xs):.2f}  (ms)"

for t in (th_notif, th_ia, th_doc):
    threading.Thread(target=t, daemon=True).start()
time.sleep(0.8)
inj = mk_pub(P["gateway"]); time.sleep(0.4)

# ---- Run 1: latencia (cadencia controlada ~100 msg/s) ----
N1 = 200
for i in range(N1):
    p = {"texto": "x" * 800, "_t_inject": time.perf_counter()}
    ev = Evento(TipoEvento.VERSAO_RECEBIDA, aluno_id=i + 1, operacao="submeter", payload=p)
    inj.send_string(f"{ev.evento} {ev.to_json_str()}"); time.sleep(0.01)
tw = time.time()
while recv[0] < N1 and time.time() - tw < 10: time.sleep(0.05)
print("=== LATENCIA  (submissao -> recomendacao | N=%d) ===" % recv[0])
print("ponta-a-ponta            :", stat(lat["e2e"]))
print("  hop Documentos         :", stat(lat["doc"]))
print("  hop IA (inclui analise):", stat(lat["ia"]))
print("  hop Notificacoes       :", stat(lat["notif"]))
print("  analise IA (provedor)  :", stat(lat["llm"]))

# ---- Run 2: throughput (rajada) ----
for k in lat: lat[k].clear()
recv[0] = 0; first[0] = None; last[0] = None
N2 = 3000
t0 = time.perf_counter()
for i in range(N2):
    p = {"texto": "x" * 800, "_t_inject": time.perf_counter()}
    ev = Evento(TipoEvento.VERSAO_RECEBIDA, aluno_id=i + 1, operacao="submeter", payload=p)
    inj.send_string(f"{ev.evento} {ev.to_json_str()}")
t_sent = time.perf_counter()
tw = time.time()
while recv[0] < N2 and time.time() - tw < 25: time.sleep(0.05)
elapsed = (last[0] - first[0]) if (first[0] and last[0] and last[0] > first[0]) else (time.perf_counter() - t0)
print()
print("=== THROUGHPUT  (rajada | enviados=%d) ===" % N2)
print("recebidos                :", recv[0])
print("tempo p/ enviar os %d    : %.1f ms" % (N2, (t_sent - t0) * 1000))
print("vazao (chegada)          : %.0f eventos/s" % (recv[0] / elapsed if elapsed > 0 else 0))
print("e2e sob carga            :", stat(lat["e2e"]))
stop.set(); time.sleep(0.3); print("\nOK")
