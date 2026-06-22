"""Cria o banco e as tabelas a partir de bd.sql. Credenciais via .env ou variaveis de ambiente."""
import os, sys
import mysql.connector

# Carrega o .env da raiz (reutiliza o leitor do config.py): a senha pode vir do .env aqui tambem.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
try:
    import common.config  # noqa: F401  (o import ja carrega o .env)
except Exception:
    pass

DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
}

aqui = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(aqui, "bd.sql"), "r", encoding="utf-8") as f:
    script = f.read()

con = mysql.connector.connect(**DB)
cur = con.cursor()
for q in (s.strip() for s in script.split(";")):
    if not q:
        continue
    try:
        cur.execute(q)
        print(f"OK: {q[:60].replace(chr(10),' ')}...")
    except Exception as e:
        print(f"ERRO: {e}")
con.commit(); cur.close(); con.close()
print("Banco configurado.")
