"""Servico de Autenticacao — padrao DEALER/ROUTER (request-reply assincrono).

E o unico servico SINCRONO do sistema: o gateway (DEALER) envia as credenciais,
este peer (ROUTER) valida contra o MySQL (ou os usuarios de demonstracao, offline)
e responde. Demonstra o 2o dos tres padroes ZeroMQ do relatorio.

Protocolo: o ROUTER recebe [identidade, ..., payload_json] e responde
[identidade, payload_json]. A identidade e adicionada pelo proprio ZeroMQ e
serve para o ROUTER enderecar a resposta de volta ao cliente certo.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import zmq
from common.config import get_zmq_address
from common.logger import criar_logger
from common.db import Repositorio

log = criar_logger("Autenticacao")
ctx = zmq.Context.instance()
router = ctx.socket(zmq.ROUTER)
router.bind(get_zmq_address("autenticacao", "bind"))
repo = Repositorio()
log.info("no ar | ROUTER autenticacao (DEALER/ROUTER) -> valida credenciais (login sincrono)")


def autenticar(req: dict) -> dict:
    """Valida e-mail/senha e devolve o perfil do usuario (ou erro)."""
    email = (req.get("email") or "").strip().lower()
    usuario = repo.validar_usuario(email, req.get("senha", ""))
    if usuario:
        log.info(f"login OK: {email} ({usuario['role']})")
        return {"ok": True, "usuario": usuario}
    log.info(f"login NEGADO: {email}")
    return {"ok": False, "erro": "Credenciais invalidas"}


if __name__ == "__main__":
    try:
        while True:
            try:
                frames = router.recv_multipart()
                identidade, payload = frames[0], frames[-1]     # ZeroMQ prefixa a identidade
                req = json.loads(payload.decode("utf-8"))
                resp = autenticar(req)
                router.send_multipart([identidade, json.dumps(resp).encode("utf-8")])
            except Exception as e:                              # uma requisicao ruim nao derruba o servico
                log.error(f"erro ao autenticar: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        router.close(); repo.fechar(); ctx.term()
