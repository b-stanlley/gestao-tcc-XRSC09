# SINTCC — Sistema Integrado de Gestão de TCC

Plataforma web de gestão de TCC com **arquitetura distribuída brokerless sobre ZeroMQ**.
A interface React (limpa, para demonstração) conversa com um **BFF em Python (pyzmq)** que
faz a ponte HTTP↔ZeroMQ e injeta comandos numa **malha de serviços coreografados** — sem
broker central. Cada serviço reage a eventos e publica novos eventos.

> **Por que Python no backend?** A malha brokerless é o núcleo do projeto e roda sobre
> ZeroMQ via **pyzmq**. O binding nativo de ZeroMQ para Node (`zeromq@6`) faz *abort* nativo
> nesta classe de máquina (Windows), então a borda (BFF) foi escrita em Python — mantendo a
> stack 100% ZeroMQ/brokerless e consistente com os diagramas do projeto.

---

## 🧩 Arquitetura

```
  React (Vite, :5173)
        │  HTTP /api/*  (proxy do Vite)
        ▼
  BFF Python (pyzmq, :3000)  ── borda HTTP↔ZeroMQ (NÃO faz parte da coreografia)
        │ PUB 5570 (injeta comandos)      ▲ SUB (ouve a coreografia → feed)
        │ DEALER 5561 (login síncrono)    │ PUSH 5567 (solicita relatórios)
        ▼                                 │
  ┌─────────────── malha brokerless (coreografia) ───────────────┐
  │ Documentos → IA → Notificações   (PUB/SUB, Cenário 1)         │
  │ Avaliação (parecer padronizado) → IA → Notificações           │
  │ Autenticação (DEALER/ROUTER)                                  │
  │ Bancas & Defesas (PUB/SUB, Cenário 2)                         │
  │ Relatórios + workers (PUSH/PULL, Cenário 3)                   │
  └───────────────────────────────────────────────────────────────┘
```

Os **3 padrões ZeroMQ** do relatório: **PUB/SUB** (coreografia), **DEALER/ROUTER**
(login), **PUSH/PULL** (relatórios distribuídos).

---

## 📂 Organização

- `/src` — interface React (Vite + Tailwind).
- `/backend` — **backend distribuído (Python)**:
  - `backend/run.py` — sobe a malha (8 peers) + o BFF, num comando.
  - `backend/bff.py` — BFF: ponte HTTP↔ZeroMQ (PUB/SUB/DEALER/PUSH) + REST + serve o `dist`.
  - `backend/common/` — config (portas ZeroMQ), eventos, logger, DAO (MySQL com fallback em memória), provedor de LLM plugável.
  - `backend/services/` — os serviços coreografados (documentos, ia, avaliacao, notificacao, autenticacao, banca, relatorios + worker).

---

## 🚀 Rodar localmente (modo demo, offline)

Pré-requisitos: **Node 18+**, **Python 3.11+**. Sem MySQL e sem internet — o DAO usa
fallback em memória e o LLM roda em modo `simulado` (em processo).

**1. Dependências**
```bash
npm install                          # frontend
pip install -r backend/requirements.txt   # backend (pyzmq)
```

**2. Subir o backend (malha + BFF)** — terminal 1:
```bash
npm run backend            # = python backend/run.py  (BFF em http://localhost:3000)
```

**3. Subir a interface** — terminal 2:
```bash
npm run dev                # Vite em http://localhost:5173 (proxy /api -> :3000)
```

**4. Abrir** http://localhost:5173 e entrar com um dos perfis de demonstração
(mesmas credenciais dos seeds do `bd.sql` — funcionam com ou sem MySQL):

| Perfil | E-mail | Senha |
|---|---|---|
| Aluno | `aluno@unifei.edu.br` | `aluno123` |
| Orientador | `orientador@unifei.edu.br` | `orient123` |
| Coordenador | `coord@unifei.edu.br` | `coord123` |
| Banca | `banca@unifei.edu.br` | `banca123` |

### Veja a coreografia ao vivo
Como **Aluno**, em *Submeter Rascunhos*, escolha a etapa e envie um texto. O BFF injeta
`versao_recebida` na malha → **Documentos** versiona e publica `versao_submetida` →
**IA** analisa e publica `recomendacao_ia_gerada` → **Notificações** registra. As mensagens
reais da coreografia aparecem no feed de **Notificações** (atualiza a cada 3 s).

---

## 🛠️ Variações
- **LLM via HTTP** (fiel à seta "consulta HTTP/JSON" do diagrama): `set LLM_PROVIDER=http` antes do `npm run backend` (sobe o stub local).
- **MySQL real**: defina `DB_HOST`/`DB_USER`/`DB_PASSWORD`/`DB_NAME` e crie o schema em `backend/services/database/mysql/bd.sql`.
- **Build de produção (1 processo)**: `npm run build` e depois `npm run backend` — o BFF passa a servir o `dist` em http://localhost:3000.
- **Multi-máquina**: cada peer aceita `HOST_<SERVICO>` (ou `ZMQ_HOST_DEFAULT`) por env.
