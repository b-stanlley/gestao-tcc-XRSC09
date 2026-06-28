# Guia de Execução e Apresentação — SINTCC

Sistema de Gestão de TCC: **frontend React (Vite)** + **BFF/serviços em Python (PyZMQ)** +
**MySQL** + **IA (Gemini, plugável)**, sob **coreografia brokerless (ZeroMQ)**.

---

## 1. Pré-requisitos (uma vez)

- **Node 18+** e **npm**
- **Python 3.11+**
- Dependências:
  ```powershell
  npm install
  pip install -r backend/requirements.txt
  ```

## 2. Configuração (`.env`)

Copie o modelo e preencha (o backend carrega o `.env` automaticamente):
```powershell
Copy-Item .env.example .env
```
```
# Banco (opcional — sem MySQL, roda em memória)
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=sua_senha_do_mysql
DB_NAME=tcc_db

# IA: simulado (offline) | gemini | http | ollama
LLM_PROVIDER=gemini
GEMINI_API_KEY=sua_chave        # gere em https://aistudio.google.com/apikey
GEMINI_MODEL=gemini-3.5-flash
```
> 🔒 O `.env` tem segredos e **não vai para o Git** (`.gitignore`). Nunca coloque a chave/senha no README.
> 💡 Para **poupar a cota do Gemini** nos testes, use `LLM_PROVIDER=simulado` (grátis/ilimitado).

## 3. MySQL (opcional — persistência real)

Sem MySQL o sistema roda em **fallback de memória**. Para persistir de verdade:
```powershell
# (mysql-connector-python já vem no requirements)
cd backend/services/database/mysql
python setup_db.py          # cria o banco tcc_db, as tabelas e os usuários
cd ../../../..
```
Com o `.env` correto, o log mostra `MySQL conectado (fonte da verdade)`.

## 4. Rodar localmente (1 máquina) — 2 terminais

```powershell
# Terminal 1 — backend (BFF + 8 peers ZeroMQ)
npm run backend
#   -> espere "MySQL conectado" e "Provedor de LLM: Gemini" (ou Simulado)

# Terminal 2 — interface
npm run dev
#   -> abra http://localhost:5173
```

### Usuários de demonstração

| Perfil | E-mail | Senha |
|---|---|---|
| Aluno | `aluno@unifei.edu.br` | `aluno123` |
| Orientador | `orientador@unifei.edu.br` | `orient123` |
| Coordenador | `coord@unifei.edu.br` | `coord123` |
| Banca | `banca@unifei.edu.br` | `banca123` |

---

## 5. Apresentação multi-máquina (plano recomendado)

**Servidor inteiro em UMA máquina; as demais só abrem o navegador.** Simples e à prova de falhas:
a malha ZeroMQ roda no servidor e os **logs no projetor** comprovam a coreografia ao vivo.

**Na máquina-servidor:**
```powershell
npm run build       # gera o dist
npm run backend     # o BFF passa a servir o dist + a API na porta 3000
```
- Descubra o **IP** do servidor: `ipconfig` → IPv4 (ex.: `192.168.0.10`).
- **Libere a porta 3000** no Firewall do Windows (na 1ª vez ele pergunta → permitir em redes privadas).

**Nas outras máquinas (aluno, orientador, coordenador):**
- Mesma rede Wi-Fi/LAN.
- Abrir no navegador: **`http://IP_DO_SERVIDOR:3000`** e logar com o perfil de cada um.

**Durante a defesa:** deixe o terminal do servidor visível. A cada ação, a banca vê os eventos
percorrerem a malha: `versao_recebida → versao_submetida → recomendacao_ia_gerada →
feedback_enviado → ...` — a prova viva do **brokerless** (sem broker central).

> **Por que é distribuído mesmo rodando num servidor?** São 8 processos independentes, sem
> memória compartilhada, cooperando só por mensagens ZeroMQ, sem broker. Como o transporte é
> `tcp://`, a malha escala para várias máquinas **só mudando o IP** (variáveis `HOST_*`), sem
> alterar o código — rodamos junto por estabilidade na demonstração.

---

## 6. Padrões ZeroMQ (o núcleo da disciplina)

| Padrão | Onde |
|---|---|
| **PUB/SUB** | coreografia (submissão/revisão, banca) |
| **DEALER/ROUTER** | login síncrono (Autenticação) |
| **PUSH/PULL** | geração distribuída de relatórios (workers) |

## 7. Portas

| Porta | Uso |
|---|---|
| 3000 | BFF (API REST) e, com `npm run build`, a interface |
| 5173 | Vite (interface, modo dev) |
| 5561 | Autenticação (ROUTER) |
| 5555 / 5562 / 5563 / 5566 | Documentos / IA / Avaliação / Notificações (PUB) |
| 5564 | Bancas & Defesas (PUB) |
| 5565 / 5567 / 5568 / 5569 | Relatórios (PUB / req / ventilador / sink) |
| 5570 | BFF (PUB na malha) |
| 5571 | Provedor de LLM (stub HTTP, se `LLM_PROVIDER=http`) |

## 8. Problemas comuns

- **Porta 3000 ocupada:** feche um BFF/Node antigo (Gerenciador de Tarefas) ou reinicie.
- **2ª máquina não abre a interface:** mesma rede? IP certo? **porta 3000 liberada no firewall**?
- **`MySQL indisponivel ... using password: NO`:** falta `DB_PASSWORD` no `.env` (ou MySQL parado). Sem ele, roda em memória — ok para a demo.
- **`Gemini indisponível`:** chave/modelo inválidos → cai no simulado automaticamente (não quebra). Confira `GEMINI_API_KEY`/`GEMINI_MODEL`.
- **`npm`/PowerShell bloqueado:** `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.
