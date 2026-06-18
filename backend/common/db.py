"""Repositorio (DAO) com MySQL como fonte da verdade e fallback em memoria
(para rodar/demonstrar sem o servidor MySQL). Cumpre o C4 Nivel 4 (RepositorioDocumentos)."""
import json
import hashlib
from common.config import DB_CONFIG
from common.logger import criar_logger

logger = criar_logger("DB")


def _hash(senha: str) -> str:
    return hashlib.sha256((senha or "").encode("utf-8")).hexdigest()


# Usuarios de demonstracao (espelham os seeds do bd.sql) para o modo offline.
# Senhas: aluno123 / orient123 / coord123 / banca123
# Inclui tambem os e-mails de "acesso rapido" da interface SINTCC (senha 123), para
# que os botoes de demonstracao autentiquem pela MESMA malha (DEALER/ROUTER).
USUARIOS_DEMO = {
    "aluno@unifei.edu.br":      {"id": 1, "nome": "Larissa (Aluno)",    "role": "aluno",       "senha": "aluno123"},
    "orientador@unifei.edu.br": {"id": 2, "nome": "Bruno (Orientador)", "role": "orientador",  "senha": "orient123"},
    "coord@unifei.edu.br":      {"id": 3, "nome": "Coordenacao de TCC", "role": "coordenador", "senha": "coord123"},
    "banca@unifei.edu.br":      {"id": 4, "nome": "Membro da Banca",    "role": "banca",       "senha": "banca123"},
    "estudante@univ.edu":       {"id": 1, "nome": "Estudante Teste",    "role": "aluno",       "senha": "123"},
    "orientador@univ.edu":      {"id": 3, "nome": "Orientador Teste",   "role": "orientador",  "senha": "123"},
    "coordenador@univ.edu":     {"id": 2, "nome": "Coordenador Teste",  "role": "coordenador", "senha": "123"},
    "banca@univ.edu":           {"id": 4, "nome": "Membro da Banca",    "role": "banca",       "senha": "123"},
}


class Repositorio:
    def __init__(self):
        self.con = None
        self.cur = None
        self._mem = {}   # aluno_id -> {"numero","texto","tipo"} (fallback sem MySQL)
        self._seen = set()  # ids de eventos ja processados (idempotencia no fallback)
        try:
            import mysql.connector
            self.con = mysql.connector.connect(**DB_CONFIG)
            self.cur = self.con.cursor()
            logger.info("MySQL conectado (fonte da verdade).")
        except Exception as e:
            logger.warning(f"MySQL indisponivel ({e}); usando memoria (fallback de demonstracao).")

    def validar_usuario(self, email, senha):
        """Valida credenciais e devolve {id,nome,email,role} ou None.
        Usado pela Autenticacao (DEALER/ROUTER). MySQL como fonte da verdade;
        no modo offline usa os usuarios de demonstracao."""
        senha_hash = _hash(senha)
        if self.cur:
            try:
                self.cur.execute(
                    "SELECT id, nome, email, role FROM usuarios WHERE email=%s AND senha_hash=%s",
                    (email, senha_hash))
                row = self.cur.fetchone()
                if row:
                    return {"id": row[0], "nome": row[1], "email": row[2], "role": row[3]}
                return None
            except Exception as e:
                logger.error(f"Erro validar_usuario: {e}")
        u = USUARIOS_DEMO.get((email or "").strip().lower())
        if u and _hash(u["senha"]) == senha_hash:
            return {"id": u["id"], "nome": u["nome"], "email": email, "role": u["role"]}
        return None

    def salvar_versao(self, aluno_id, texto, tipo):
        if self.cur:
            try:
                self.cur.execute("SELECT COALESCE(MAX(numero),0)+1 FROM versoes WHERE aluno_id=%s", (aluno_id,))
                numero = self.cur.fetchone()[0]
                self.cur.execute("UPDATE versoes SET vigente=FALSE WHERE aluno_id=%s", (aluno_id,))
                self.cur.execute(
                    "INSERT INTO versoes (aluno_id,numero,tipo,texto,vigente) VALUES (%s,%s,%s,%s,TRUE)",
                    (aluno_id, numero, tipo, texto))
                self.con.commit()
                return numero
            except Exception as e:
                logger.error(f"Erro salvar_versao: {e}")
        n = self._mem.get(aluno_id, {}).get("numero", 0) + 1
        self._mem[aluno_id] = {"numero": n, "texto": texto, "tipo": tipo}
        return n

    def texto_versao_vigente(self, aluno_id):
        """Texto da versao vigente: fonte da verdade no MySQL; fallback em memoria.
        Permite que a IA leia o estado do banco em vez de manter estado em processo."""
        if self.cur:
            try:
                self.cur.execute(
                    "SELECT texto FROM versoes WHERE aluno_id=%s AND vigente=TRUE LIMIT 1", (aluno_id,))
                row = self.cur.fetchone()
                return row[0] if row else None
            except Exception as e:
                logger.error(f"Erro texto_versao_vigente: {e}")
        return self._mem.get(aluno_id, {}).get("texto")

    def salvar_feedback(self, aluno_id, feedback, secoes):
        if self.cur:
            try:
                self.cur.execute(
                    "INSERT INTO feedbacks (aluno_id,feedback,secoes_criticas) VALUES (%s,%s,%s)",
                    (aluno_id, feedback, json.dumps(secoes)))
                self.con.commit()
            except Exception as e:
                logger.error(f"Erro salvar_feedback: {e}")

    def salvar_parecer(self, aluno_id, versao_id, criterios, nota, decisao, comentario):
        """Persiste um parecer PADRONIZADO (RF04 / JEMS). Offline: a coreografia
        segue pelo evento, sem persistencia."""
        if self.cur:
            try:
                self.cur.execute(
                    "INSERT INTO pareceres (aluno_id,versao_id,avaliador_id,nota,decisao,criterios,comentario) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (aluno_id, versao_id, None, nota, decisao, json.dumps(criterios), comentario))
                self.con.commit()
            except Exception as e:
                logger.error(f"Erro salvar_parecer: {e}")

    def salvar_banca(self, aluno_id, orientador_id, data_defesa, avaliadores):
        """Cria a banca + membros (Cenario 2). Retorna o id da banca (ou None offline)."""
        if self.cur:
            try:
                self.cur.execute(
                    "INSERT INTO bancas (aluno_id,orientador_id,data_defesa,status) VALUES (%s,%s,%s,'agendada')",
                    (aluno_id, orientador_id, data_defesa))
                banca_id = self.cur.lastrowid
                for nome in (avaliadores or []):
                    self.cur.execute(
                        "INSERT INTO banca_membros (banca_id,nome) VALUES (%s,%s)", (banca_id, nome))
                self.con.commit()
                return banca_id
            except Exception as e:
                logger.error(f"Erro salvar_banca: {e}")
        return None

    def salvar_defesa(self, banca_id, aluno_id, nota, resultado, parecer):
        if self.cur:
            try:
                self.cur.execute(
                    "INSERT INTO defesas (banca_id,aluno_id,nota_final,resultado,parecer) VALUES (%s,%s,%s,%s,%s)",
                    (banca_id, aluno_id, nota, resultado, parecer))
                self.con.commit()
            except Exception as e:
                logger.error(f"Erro salvar_defesa: {e}")

    def salvar_notificacao(self, destino_role, aluno_id, tipo, mensagem):
        """Persiste uma notificacao interna (RF05). Offline: no-op."""
        if self.cur:
            try:
                self.cur.execute(
                    "INSERT INTO notificacoes (destino_role,aluno_id,tipo,mensagem) VALUES (%s,%s,%s,%s)",
                    (destino_role, aluno_id, tipo, mensagem))
                self.con.commit()
            except Exception as e:
                logger.error(f"Erro salvar_notificacao: {e}")

    def registrar_evento(self, ev: dict) -> bool:
        """Grava a trilha de eventos e sinaliza se o evento e novo.
        Retorna True se deve ser processado; False se ja foi visto (idempotencia
        via evento_id UNIQUE no MySQL, ou via conjunto em memoria no fallback)."""
        evento_id = ev.get("id")
        if self.cur:
            try:
                self.cur.execute(
                    "INSERT IGNORE INTO historico_eventos (evento_id,tipo_evento,aluno_id,dados) VALUES (%s,%s,%s,%s)",
                    (evento_id, ev.get("evento"), ev.get("aluno_id"), json.dumps(ev.get("payload", {}))))
                self.con.commit()
                return self.cur.rowcount == 1   # 1 = inserido (novo); 0 = ignorado (duplicado)
            except Exception as e:
                logger.error(f"Erro registrar_evento: {e}")
                return True   # em caso de falha de BD, nao bloqueia o fluxo
        if evento_id in self._seen:
            return False
        self._seen.add(evento_id)
        return True

    def fechar(self):
        try:
            if self.cur: self.cur.close()
            if self.con: self.con.close()
        except Exception:
            pass
