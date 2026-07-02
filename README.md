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
        │  HTTP /api/*  (proxy do Vite → :3000)
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
                    │ persiste / relê estado
                    ▼
             MySQL (fonte da verdade)  ·  fallback em memória se ausente
```

Os **3 padrões ZeroMQ** do relatório: **PUB/SUB** (coreografia), **DEALER/ROUTER**
(login), **PUSH/PULL** (relatórios distribuídos).

---

## 📂 Organização

- `/src` — interface React (Vite + Tailwind).
- `/backend` — **backend distribuído (Python)**:
  - `backend/run.py` — sobe a malha (8 peers + 2 workers) e o BFF, num comando.
  - `backend/bff.py` — BFF: ponte HTTP↔ZeroMQ (PUB/SUB/DEALER/PUSH) + REST + serve o `dist`.
  - `backend/bench.py` — benchmark da coreografia (latência e vazão) com LLM simulado.
  - `backend/common/` — config (portas ZeroMQ, `.env`), eventos, logger, DAO (MySQL + fallback), provedor de LLM plugável.
  - `backend/services/` — os serviços coreografados (documentos, ia, avaliacao, notificacao, autenticacao, banca, propostas, relatorios + worker).
  - `backend/services/database/mysql/` — `bd.sql` (schema + seeds) e `setup_db.py` (cria o banco).

---

## ⚡ Comandos rápidos

| Objetivo | Comando |
|---|---|
| Instalar dependências | `npm install` · `pip install -r backend/requirements.txt` |
| Backend (malha + BFF) | `npm run backend` |
| Interface (dev) | `npm run dev` → http://localhost:5173 |
| Build + servir tudo em 1 processo | `npm run build` → `npm run backend` → http://localhost:3000 |
| Criar o banco MySQL | `python backend/services/database/mysql/setup_db.py` |
| Benchmark (LLM simulado) | `python backend/bench.py` |

> **Pré-requisitos:** Node 18+, Python 3.11+. Sem MySQL e sem internet o sistema roda em
> **modo demo** (DAO em memória + LLM `simulado`) — nada quebra.

---

## 🔐 Configuração (`.env`)

Segredos ficam **só** no `.env` (ignorado pelo Git); nunca no README nem no `.env.example`.

```powershell
Copy-Item .env.example .env      # depois preencha
```
```
# Banco (opcional — sem isto, roda em memória)
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=sua_senha_do_mysql
DB_NAME=tcc_db

# IA plugável: simulado (offline) | gemini | http | ollama
LLM_PROVIDER=simulado
GEMINI_API_KEY=sua_chave         # gere em https://aistudio.google.com/apikey
GEMINI_MODEL=gemini-3.5-flash
```
O `.env` é carregado pela stdlib em `backend/common/config.py` (`_carregar_env`, linhas 7–23).
Variáveis já definidas no terminal têm prioridade sobre o `.env`.

---

# 🎬 Guia de execução e demonstração

Cada demonstração abaixo vem com **🔎 Comprovação no código** — onde exatamente aquilo está
implementado, para mostrar à banca que o comportamento é real (não encenado).

---

## 1) Rodar o sistema em um só PC

**Terminal 1 — backend (malha brokerless + BFF):**
```bash
npm run backend
```
Espere as linhas `no ar | ...` de cada serviço e `BFF HTTP em http://localhost:3000`.

**Terminal 2 — interface:**
```bash
npm run dev
```
Abra **http://localhost:5173** e entre com um perfil de demonstração (tabela no fim).

**🔎 Comprovação no código**
- `backend/run.py` (linhas 22–47) — sobe **consumidores primeiro** e o BFF por último
  (evita o *slow joiner* do PUB/SUB). Não há nenhum processo de broker: só peers + BFF.
- `vite.config.ts` (linhas 22–27) — o Vite faz **proxy** de `/api` para o BFF em `:3000`.
- `backend/bff.py` (linha 579) — o BFF serve HTTP; a API vive em `/api/*`.

---

## 2) Rodar em dois computadores (Aluno e Orientador) — só a interface

Conforme combinado: **o servidor inteiro roda em UMA máquina**; a outra só abre o navegador.
Nenhuma mudança de código e nenhum IP a configurar no código — a malha ZeroMQ toda fica no servidor.

**Na máquina-servidor (a sua):**
```bash
npm run build          # gera o dist (interface estática)
npm run backend        # o BFF passa a servir o dist + a API na porta 3000
```
- Descubra o IP: `ipconfig` → **IPv4** (ex.: `192.168.0.10`).
- **Libere a porta 3000** no Firewall do Windows (na 1ª vez ele pergunta → permitir em redes privadas).

**Na outra máquina (Orientador), mesma rede Wi-Fi/LAN:**
- Abrir no navegador: **`http://192.168.0.10:3000`** e logar como Orientador.
- Você, no servidor, abre `http://localhost:3000` e loga como Aluno.

As duas telas conversam pela **mesma malha** rodando no servidor.

**🔎 Comprovação no código**
- `backend/bff.py` (linha 579) — `ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), ...)`: o BFF
  escuta em **todas as interfaces de rede**, por isso outra máquina alcança `http://IP:3000`.
- `backend/bff.py` (`_serve_static`, linhas 522–538) — com o `dist` presente, o próprio BFF
  serve a interface React (SPA), então basta a porta 3000 na outra máquina.
- *(Para distribuir também a malha entre máquinas — não é o nosso plano da demo — cada peer
  aceita `HOST_<SERVICO>`/`ZMQ_HOST_DEFAULT`: veja `backend/common/config.py`, `get_host`
  linhas 71–76 e `get_zmq_address` linhas 78–82, que usam `tcp://*` no bind e `tcp://host:porta`
  no connect.)*

---

## 3) Rodar o benchmark (LLM simulado) — caso o professor peça na hora

Mede, sobre o **mesmo** transporte (ZeroMQ), formato de mensagem (`Evento`) e provedor de IA
do sistema: **latência ponta-a-ponta, latência por salto e vazão** da coreografia
Documentos → IA → Notificações.

```bash
python backend/bench.py
```
> Rode-o **sozinho** (feche o `npm run backend` antes): ele faz *bind* nas portas 5570/5555/5562
> e conflitaria com a malha. Sai em ~poucos segundos com uma tabela de latência e vazão.

**🔎 Comprovação no código**
- `backend/bench.py` (linha 18) — `os.environ.setdefault("LLM_PROVIDER", "simulado")`: por
  padrão o benchmark é **offline e reprodutível** (não gasta cota do Gemini).
- `backend/bench.py` (linhas 41–62) — reproduz a cadeia real **Documentos → IA → Notificações**
  em threads sobre ZeroMQ; usa a **mesma** classe `Evento` e o **mesmo** provedor de LLM do sistema.
- `backend/bench.py` (linhas 89–122) — Run 1 mede latência (cadência controlada) e Run 2 mede
  vazão (rajada de 3000 eventos).

---

## 4) Roteiro de teste ponta a ponta (Aluno ↔ Orientador) para a demo

Este é o **teste funcional completo** da coreografia — o roteiro que valida todos os fluxos do
Cenário 1 entre os dois perfis. (Não há suíte automatizada de testes; a validação é este
walkthrough + o benchmark do item 3.) Faça na ordem, olhando o **terminal do backend**:

| # | Quem | Ação na interface | Evento na malha | O que comprova |
|---|---|---|---|---|
| 1 | Aluno | *Submeter Rascunhos* → escolhe etapa → envia texto | `versao_recebida` → `versao_submetida` | BFF injeta; **Documentos** versiona e publica |
| 2 | (auto) | — | `recomendacao_ia_gerada` | **IA** reage sozinha, consulta o LLM e publica |
| 3 | Aluno | vê o **parecer da IA** na tela | — | correlação por `submission_id` (não sobrepõe) |
| 4 | Orientador | abre a submissão do aluno e envia **parecer** | `parecer_recebido` → `feedback_enviado` | **Avaliação** publica; a IA reavalia |
| 5 | (auto) | — | `feedback_atendido` **ou** `pendencias_identificadas` | **IA** reavalia a versão vigente |
| 6 | Aluno | vê o feedback do orientador | — | fluxo aluno↔orientador fechado |

**🔎 Comprovação no código**
- Passo 1: `backend/bff.py` `submeter_versao` (linhas 289–313) cria um `submission_id` **único**
  (`int(time.time()*1000)`) e injeta `versao_recebida`; `backend/services/documentos/service.py`
  `consumir` (linhas 87–101) versiona e publica `versao_submetida`.
- Passo 2: `backend/services/ia/service.py` `on_versao` (linhas 25–42) — a IA assina
  `versao_submetida`, monta o prompt, consulta o provedor e publica `recomendacao_ia_gerada`.
- Passo 3: o `submission_id` viaja pela malha inteira, então cada parecer casa com a submissão
  certa (correção da sobreposição): `backend/bff.py` (linhas 163–214).
- Passo 4: `backend/bff.py` `enviar_parecer` (linhas 337–377) publica `parecer_recebido`.
- Passo 5: `backend/services/ia/service.py` `on_feedback` (linhas 44–57) reavalia e publica
  `feedback_atendido`/`pendencias_identificadas`.

> **Cronograma é opcional:** o Aluno consegue submeter **sem** escolher etapa. Isso é intencional
> (a criação de etapas é do Orientador e não bloqueia a submissão) — ver `App.jsx` (dropdown com
> opção "sem etapa") e `backend/bff.py` `registrar_cronograma` (linhas 330–334), separado da submissão.

### Disparar uma submissão pela linha de comando (PowerShell)

Útil para **injetar um evento na malha sem usar a interface** (ex.: dispara e olha os logs da
coreografia no terminal do backend, sem sujar a tela):

```powershell
Invoke-RestMethod -Uri http://localhost:3000/api/submissions -Method Post `
  -ContentType "application/json" `
  -Body '{"student_id":1,"text":"Introducao do TCC sobre sistemas distribuidos com ZeroMQ brokerless e coreografia de eventos."}'
```
A resposta traz `submission_id`; no terminal do backend aparece a trilha
`versao_recebida → versao_submetida → recomendacao_ia_gerada`.

Outros endpoints seguem o mesmo padrão (ex.: relatórios como Coordenador):
```powershell
Invoke-RestMethod -Uri http://localhost:3000/api/relatorios/gerar -Method Post `
  -ContentType "application/json" -Body '{"tipo":"panorama"}'
```

**🔎 Comprovação no código**
- As rotas HTTP ficam em `backend/bff.py` `do_POST` (linhas 489–520): `/api/submissions` →
  `submeter_versao`, `/api/relatorios/gerar` → `gerar_relatorio`, etc.
- `POST /api/submissions` executa exatamente o mesmo caminho da interface — `submeter_versao`
  (linhas 289–313) —, então o teste por terminal e o teste pela tela são o **mesmo fluxo**.

---

## 5) Ver a coreografia / ZeroMQ / brokerless nos logs — e comprovar no código

Com `npm run backend` rodando, **cada ação gera uma trilha de logs no terminal**, uma linha por
serviço, no formato `HH:MM:SS [Serviço] INFO: ...`. Submeta uma versão (passo 1 acima) e observe:

```
[BFF]         injetado na malha: [versao_recebida] aluno=1 op=submeter id=1a2b3c4d
[Documentos]  versao v1 persistida; publicado [versao_submetida] aluno=1 ...
[IA]          recomendacao gerada p/ aluno 1; publicado [recomendacao_ia_gerada] ...
[Notificacao] ... (registra o evento)
```
Essa sequência **é** a coreografia: ninguém orquestra; cada serviço reage ao evento que assina.

**🔎 Comprovação no código (por que é brokerless e coreografado)**
- **Não existe broker:** `backend/run.py` (linhas 23–34) sobe **apenas** os peers e o BFF —
  nenhum processo intermediário de mensageria.
- **Malha direta (bind/connect):** cada serviço faz `bind` do **seu** PUB e `connect` direto aos
  PUBs que consome — sem encaminhador central:
  - `backend/services/documentos/service.py` (linhas 67–71) — `SUB.connect(gateway)` +
    `PUB.bind(documentos)`.
  - `backend/services/ia/service.py` (linhas 12–19) — assina `versao_submetida` e
    `feedback_enviado`, publica no canal `ia`.
- **Endereços TCP diretos:** `backend/common/config.py` `get_zmq_address` (linhas 78–82) —
  `tcp://*:porta` no bind e `tcp://host:porta` no connect (peer-to-peer, sem broker).
- **As linhas de log** que aparecem no terminal:
  - injeção na malha: `backend/bff.py` `_publicar` (linha 268).
  - Documentos publicando: `backend/services/documentos/service.py` (linha 101).
  - IA publicando: `backend/services/ia/service.py` (linha 42).
  - formato do log: `backend/common/logger.py` (linhas 8–9).
- **Os três padrões, na borda:** `backend/bff.py` (linhas 46–57) — `PUB` (5570), `DEALER` (5561)
  e `PUSH` (5567) instanciados lado a lado.

---

## 6) Ver os logs do MySQL e comprovar a persistência no código

**Criar o banco (uma vez):**
```bash
python backend/services/database/mysql/setup_db.py
```
**Rodar com o `.env` apontando para o MySQL** (`DB_PASSWORD` etc.). No terminal do backend,
a prova de que o banco está ativo é a linha:
```
[DB] INFO: MySQL conectado (fonte da verdade).
```
Se aparecer `MySQL indisponivel (...); usando memoria (fallback ...)`, o sistema roda em memória
(ok para demo, mas **sem** persistência real).

**Comprovar a persistência de verdade (SQL):** submeta uma versão pela interface e depois:
```sql
USE tcc_db;
SELECT id, aluno_id, numero, tipo, vigente, created_at FROM versoes ORDER BY id DESC;
SELECT evento_id, tipo_evento, aluno_id, data_evento FROM historico_eventos ORDER BY id DESC;
```
Reinicie o backend e confira: os dados **continuam lá** (sobrevivem ao restart).

**🔎 Comprovação no código**
- **Conexão / fonte da verdade:** `backend/common/db.py` `Repositorio.__init__` (linhas 33–39) —
  conecta e loga `MySQL conectado (fonte da verdade).`; se falhar, cai no fallback de memória.
- **Grava a versão:** `backend/common/db.py` `salvar_versao` (linhas 120–135) — `INSERT INTO versoes`,
  marcando a nova como `vigente` e as anteriores como não-vigentes.
- **Grava proposta / parecer:** `salvar_proposta` (linhas 62–77), `salvar_parecer` (linhas 160–171).
- **IA lê do banco (não da memória):** `texto_versao_vigente` (linhas 137–148) — a IA reavalia a
  versão vigente **lida do MySQL**.
- **Idempotência persistida:** `registrar_evento` (linhas 211–229) — `INSERT IGNORE` na tabela
  `historico_eventos`, cujo `evento_id` é **UNIQUE** (`bd.sql`, linhas 74–81); reprocessar o mesmo
  evento não duplica efeito.
- **Sobrevive ao restart:** `backend/bff.py` `_rehidratar` (linhas 541–573) — ao subir, o BFF
  **relê** propostas/versões/pareceres do MySQL para o read-model da interface.

---

## 7) Gerar relatórios (perfil Coordenador) — PUSH/PULL

Logue como **Coordenador** e use a ação de **gerar relatório** (panorama de TCCs). O pedido vai
por **PUSH/PULL**: o coordenador de relatórios divide o trabalho, ventila subtarefas aos *workers*,
coleta os parciais e consolida o panorama, publicando `relatorio_gerado`.

No terminal, observe:
```
[Relatorios]        solicitacao '...' : 4 subtarefas ventiladas aos workers
[Relatorios-Worker] chunk 0 agregado: N registros
[Relatorios-Worker] chunk 1 agregado: N registros
[Relatorios]        parcial recebido do sink (x/4) ... panorama consolidado e publicado
```

**🔎 Comprovação no código**
- **Pedido (borda):** `backend/bff.py` `gerar_relatorio` (linhas 396–400) — envia por `PUSH`
  para `relatorio_req`.
- **Pipeline PUSH/PULL:** `backend/services/relatorios/service.py` (linhas 24–27) — sockets
  `req`(PULL) / `vent`(PUSH) / `sink`(PULL) / `pub`; `gerar` (linhas 47–69) ventila 4 subtarefas,
  coleta os parciais e publica `relatorio_gerado`.
- **Workers em paralelo:** `backend/services/relatorios/worker.py` (linhas 15–16, 31–38) —
  `PULL.connect(vent)` + `PUSH.connect(sink)`; o `run.py` sobe **2 workers** (linhas 32–33), então
  o *round-robin* do PULL distribui as subtarefas (cada uma vai a exatamente um worker).
- **Resultado na interface:** o BFF guarda o último panorama — `backend/bff.py` (linhas 146–147)
  e o expõe em `GET /api/relatorios/ultimo` (linhas 475–476).

---

## 👤 Credenciais de demonstração

Funcionam **com ou sem** MySQL (os seeds do `bd.sql` espelham os usuários de fallback):

| Perfil | E-mail | Senha |
|---|---|---|
| Aluno | `aluno@unifei.edu.br` | `aluno123` |
| Orientador | `orientador@unifei.edu.br` | `orient123` |
| Coordenador | `coord@unifei.edu.br` | `coord123` |
| Banca | `banca@unifei.edu.br` | `banca123` |

Seeds: `backend/services/database/mysql/bd.sql` (linhas 15–19) · fallback: `backend/common/db.py`
(`USUARIOS_DEMO`, linhas 19–24).

---

## 🔌 Portas

| Porta | Uso |
|---|---|
| 3000 | BFF (API REST) e, com `npm run build`, a interface |
| 5173 | Vite (interface, modo dev) |
| 5561 | Autenticação (ROUTER) |
| 5555 / 5562 / 5563 / 5566 | Documentos / IA / Avaliação / Notificações (PUB) |
| 5556 / 5564 | Propostas / Bancas & Defesas (PUB) |
| 5565 / 5567 / 5568 / 5569 | Relatórios (PUB / req / ventilador / sink) |
| 5570 | BFF (PUB na malha) |
| 5571 | Provedor de LLM (stub HTTP, se `LLM_PROVIDER=http`) |

Definição: `backend/common/config.py` (`PORTAS`, linhas 26–43).

---

## 🩹 Problemas comuns

- **Porta 3000 ocupada:** feche um BFF/Node antigo (Gerenciador de Tarefas) ou reinicie.
- **2ª máquina não abre a interface:** mesma rede? IP certo? **porta 3000 liberada no firewall**?
- **`MySQL indisponivel ... using password: NO`:** falta `DB_PASSWORD` no `.env` (ou MySQL parado).
  Sem ele, roda em memória — ok para a demo, mas sem persistência.
- **`Gemini indisponível`:** chave/modelo inválidos → cai no `simulado` automaticamente (não quebra).
- **Benchmark trava / erro de porta:** feche o `npm run backend` antes (conflito de portas 5570/5555/5562).
- **`npm`/PowerShell bloqueado:** `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.
