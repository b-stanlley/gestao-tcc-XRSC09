# SINTCC — Sistema Integrado de Gestão de TCC

Plataforma web de gestão de TCC com **arquitetura distribuída brokerless sobre ZeroMQ**.
A interface em React conversa com um **BFF em Python (pyzmq)** que faz a ponte HTTP↔ZeroMQ e
injeta comandos em uma **malha de serviços coreografados**, sem broker central: cada serviço
reage a eventos e publica novos eventos.

> **Por que Python no backend?** A malha brokerless roda sobre ZeroMQ por meio do binding
> **pyzmq**. O binding nativo de ZeroMQ para Node (`zeromq@6`) apresenta *abort* nativo no
> ambiente de desenvolvimento utilizado (Windows); por isso a borda (BFF) foi implementada em
> Python, mantendo a stack sobre ZeroMQ/brokerless e consistente com os diagramas do projeto.

---

## Arquitetura

```
  React (Vite, :5173)
        │  HTTP /api/*  (proxy do Vite → :3000)
        ▼
  BFF Python (pyzmq, :3000)  ── borda HTTP↔ZeroMQ (não faz parte da coreografia)
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
             MySQL (fonte da verdade)  ·  modo em memória quando ausente
```

Os três padrões ZeroMQ empregados: **PUB/SUB** (coreografia), **DEALER/ROUTER** (login) e
**PUSH/PULL** (relatórios distribuídos).

---

## Organização do repositório

- `/src` — interface React (Vite + Tailwind).
- `/backend` — backend distribuído (Python):
  - `backend/run.py` — inicia a malha (8 peers + 2 workers) e o BFF em um único comando.
  - `backend/bff.py` — BFF: ponte HTTP↔ZeroMQ (PUB/SUB/DEALER/PUSH) + REST + serve o `dist`.
  - `backend/bench.py` — benchmark da coreografia (latência e vazão) com LLM simulado.
  - `backend/common/` — configuração (portas ZeroMQ, `.env`), eventos, logger, DAO (MySQL com modo em memória) e provedor de LLM plugável.
  - `backend/services/` — os serviços coreografados (documentos, ia, avaliacao, notificacao, autenticacao, banca, propostas, relatorios + worker).
  - `backend/services/database/mysql/` — `bd.sql` (schema + seeds) e `setup_db.py` (cria o banco).
- `/docs` — relatório do projeto (PDF).

---

## Comandos rápidos

| Objetivo | Comando |
|---|---|
| Instalar dependências | `npm install` · `pip install -r backend/requirements.txt` |
| Backend (malha + BFF) | `npm run backend` |
| Interface (desenvolvimento) | `npm run dev` → http://localhost:5173 |
| Build + servir tudo em 1 processo | `npm run build` → `npm run backend` → http://localhost:3000 |
| Criar o banco MySQL | `python backend/services/database/mysql/setup_db.py` |
| Benchmark (LLM simulado) | `python backend/bench.py` |

> **Pré-requisitos:** Node 18+ e Python 3.11+. Sem MySQL e sem acesso à internet, o sistema
> executa em **modo local** (DAO em memória e LLM `simulado`).

---

## Configuração (`.env`)

As credenciais ficam apenas no `.env` (ignorado pelo Git). O `.env.example` contém somente
campos de exemplo, sem valores reais.

```powershell
Copy-Item .env.example .env      # em seguida, preencha
```
```
# Banco de dados (opcional — sem estes campos, executa em memória)
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=sua_senha_do_mysql
DB_NAME=tcc_db

# Provedor de IA: simulado (offline) | gemini | http | ollama
LLM_PROVIDER=simulado
GEMINI_API_KEY=sua_chave         # gerada em https://aistudio.google.com/apikey
GEMINI_MODEL=gemini-3.5-flash
```
O `.env` é carregado pela biblioteca padrão em `backend/common/config.py`
(`_carregar_env`, linhas 7–23). Variáveis já definidas no terminal têm prioridade sobre o `.env`.

---

# Guia de execução e verificação

Cada seção traz um bloco **Onde está no código**, indicando o arquivo e as linhas que
implementam o comportamento descrito, para que o leitor possa localizá-lo e verificá-lo
diretamente no repositório.

---

## 1) Executar em um único computador

**Terminal 1 — backend (malha brokerless + BFF):**
```bash
npm run backend
```
Aguarde as linhas `no ar | ...` de cada serviço e `BFF HTTP em http://localhost:3000`.

**Terminal 2 — interface:**
```bash
npm run dev
```
Acesse **http://localhost:5173** e entre com um dos perfis (tabela ao final).

**Onde está no código**
- `backend/run.py` (linhas 22–47) — inicia os consumidores primeiro e o BFF por último
  (evita o *slow joiner* do PUB/SUB). Não há processo de broker: apenas peers e BFF.
- `vite.config.ts` (linhas 22–27) — o Vite faz *proxy* de `/api` para o BFF em `:3000`.
- `backend/bff.py` (linha 579) — o BFF serve HTTP; a API está sob `/api/*`.

---

## 2) Executar em dois computadores (interface em cada um)

O servidor completo é executado em **uma** máquina; a outra apenas acessa a interface pelo
navegador. Não é necessário alterar o código nem configurar IP no código: a malha ZeroMQ
permanece no servidor.

**Na máquina que atua como servidor:**
```bash
npm run build          # gera o dist (interface estática)
npm run backend        # o BFF passa a servir o dist e a API na porta 3000
```
- Identifique o IP: `ipconfig` → **IPv4** (ex.: `192.168.0.10`).
- Libere a porta 3000 no Firewall do Windows (na primeira execução, permitir em redes privadas).

**Na outra máquina, na mesma rede local:**
- Acesse `http://ENDERECO_DO_SERVIDOR:3000` (ex.: `http://192.168.0.10:3000`) e faça login.

Ambas as telas operam sobre a mesma malha em execução no servidor.

**Onde está no código**
- `backend/bff.py` (linha 579) — `ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), ...)`: o BFF
  escuta em todas as interfaces de rede, o que permite o acesso a partir de outra máquina.
- `backend/bff.py` (`_serve_static`, linhas 522–538) — com o `dist` presente, o BFF serve a
  interface React (SPA), sendo suficiente a porta 3000 na outra máquina.
- Para distribuir também a malha entre máquinas, cada peer aceita `HOST_<SERVICO>` ou
  `ZMQ_HOST_DEFAULT`: ver `backend/common/config.py`, `get_host` (linhas 71–76) e
  `get_zmq_address` (linhas 78–82), que usam `tcp://*` no bind e `tcp://host:porta` no connect.

---

## 3) Executar o benchmark (LLM simulado)

Mede, sobre o mesmo transporte (ZeroMQ), o mesmo formato de mensagem (`Evento`) e o mesmo
provedor de IA do sistema: latência ponta-a-ponta, latência por salto e vazão da cadeia
Documentos → IA → Notificações.

```bash
python backend/bench.py
```
> Execute-o isoladamente (encerre o `npm run backend` antes): ele faz *bind* nas portas
> 5570/5555/5562 e entraria em conflito com a malha em execução. A saída é uma tabela de
> latência e vazão.

**Onde está no código**
- `backend/bench.py` (linha 18) — `os.environ.setdefault("LLM_PROVIDER", "simulado")`: por
  padrão o benchmark é offline e reprodutível.
- `backend/bench.py` (linhas 41–62) — reproduz a cadeia Documentos → IA → Notificações em
  threads sobre ZeroMQ, com a mesma classe `Evento` e o mesmo provedor de LLM do sistema.
- `backend/bench.py` (linhas 89–122) — Run 1 mede latência (cadência controlada) e Run 2 mede
  vazão (rajada de 3000 eventos).

---

## 4) Verificação funcional ponta a ponta (Aluno ↔ Orientador)

Roteiro que percorre o Cenário 1 entre os dois perfis. Não há suíte de testes automatizada; a
verificação funcional é feita por este roteiro, e a de desempenho, pelo benchmark (item 3).
Execute na ordem, acompanhando o terminal do backend:

| # | Perfil | Ação na interface | Evento na malha | O que ocorre |
|---|---|---|---|---|
| 1 | Aluno | *Submeter Rascunhos* → seleciona etapa → envia texto | `versao_recebida` → `versao_submetida` | o BFF injeta; **Documentos** versiona e publica |
| 2 | (automático) | — | `recomendacao_ia_gerada` | **IA** reage ao evento, consulta o LLM e publica |
| 3 | Aluno | visualiza o parecer da IA | — | correlação por `submission_id` (sem sobreposição) |
| 4 | Orientador | abre a submissão e registra um parecer | `parecer_recebido` → `feedback_enviado` | **Avaliação** publica; a IA reavalia |
| 5 | (automático) | — | `feedback_atendido` **ou** `pendencias_identificadas` | **IA** reavalia a versão vigente |
| 6 | Aluno | visualiza o feedback do orientador | — | fluxo Aluno ↔ Orientador concluído |

**Onde está no código**
- Passo 1: `backend/bff.py` `submeter_versao` (linhas 289–313) gera um `submission_id` único
  (`int(time.time()*1000)`) e injeta `versao_recebida`; `backend/services/documentos/service.py`
  `consumir` (linhas 87–101) versiona e publica `versao_submetida`.
- Passo 2: `backend/services/ia/service.py` `on_versao` (linhas 25–42) — a IA assina
  `versao_submetida`, monta o prompt, consulta o provedor e publica `recomendacao_ia_gerada`.
- Passo 3: o `submission_id` acompanha a mensagem por toda a malha, de modo que cada parecer
  corresponde à submissão correspondente: `backend/bff.py` (linhas 163–214).
- Passo 4: `backend/bff.py` `enviar_parecer` (linhas 337–377) publica `parecer_recebido`.
- Passo 5: `backend/services/ia/service.py` `on_feedback` (linhas 44–57) reavalia e publica
  `feedback_atendido`/`pendencias_identificadas`.

> **Etapa (cronograma) é opcional:** o Aluno pode submeter sem selecionar uma etapa. A criação
> de etapas cabe ao Orientador e não bloqueia a submissão — ver `App.jsx` (opção "sem etapa" no
> seletor) e `backend/bff.py` `registrar_cronograma` (linhas 330–334), separado da submissão.

### Disparar uma submissão pela linha de comando (PowerShell)

Permite injetar um evento na malha sem utilizar a interface — por exemplo, para acompanhar os
logs da coreografia no terminal do backend:

```powershell
Invoke-RestMethod -Uri http://localhost:3000/api/submissions -Method Post `
  -ContentType "application/json" `
  -Body '{"student_id":1,"text":"Introducao do TCC sobre sistemas distribuidos com ZeroMQ brokerless e coreografia de eventos."}'
```
A resposta contém o `submission_id`; no terminal do backend surge a sequência
`versao_recebida → versao_submetida → recomendacao_ia_gerada`.

Outros endpoints seguem o mesmo padrão (por exemplo, relatórios, perfil Coordenador):
```powershell
Invoke-RestMethod -Uri http://localhost:3000/api/relatorios/gerar -Method Post `
  -ContentType "application/json" -Body '{"tipo":"panorama"}'
```

**Onde está no código**
- As rotas HTTP estão em `backend/bff.py` `do_POST` (linhas 489–520): `/api/submissions` →
  `submeter_versao`, `/api/relatorios/gerar` → `gerar_relatorio`, entre outras.
- `POST /api/submissions` percorre o mesmo caminho da interface — `submeter_versao`
  (linhas 289–313) —, de modo que a chamada por terminal e a ação pela tela correspondem ao
  mesmo fluxo.

---

## 5) Acompanhar a coreografia (ZeroMQ, brokerless) nos logs

Com o `npm run backend` em execução, cada ação gera uma sequência de logs no terminal, uma linha
por serviço, no formato `HH:MM:SS [Serviço] INFO: ...`. Ao submeter uma versão (passo 1 acima),
observa-se:

```
[BFF]         injetado na malha: [versao_recebida] aluno=1 op=submeter id=1a2b3c4d
[Documentos]  versao v1 persistida; publicado [versao_submetida] aluno=1 ...
[IA]          recomendacao gerada p/ aluno 1; publicado [recomendacao_ia_gerada] ...
[Notificacao] ... (registra o evento)
```
A sequência corresponde à coreografia: não há orquestrador; cada serviço reage ao evento que
assina.

**Onde está no código (elementos brokerless e coreografados)**
- Ausência de broker: `backend/run.py` (linhas 23–34) inicia apenas os peers e o BFF, sem
  processo intermediário de mensageria.
- Malha direta (bind/connect): cada serviço faz `bind` do próprio PUB e `connect` direto aos
  PUBs que consome, sem encaminhador central:
  - `backend/services/documentos/service.py` (linhas 67–71) — `SUB.connect(gateway)` +
    `PUB.bind(documentos)`.
  - `backend/services/ia/service.py` (linhas 12–19) — assina `versao_submetida` e
    `feedback_enviado`, publica no canal `ia`.
- Endereços TCP diretos: `backend/common/config.py` `get_zmq_address` (linhas 78–82) —
  `tcp://*:porta` no bind e `tcp://host:porta` no connect (comunicação entre pares).
- Linhas de log correspondentes:
  - injeção na malha: `backend/bff.py` `_publicar` (linha 268).
  - Documentos publicando: `backend/services/documentos/service.py` (linha 101).
  - IA publicando: `backend/services/ia/service.py` (linha 42).
  - formato do log: `backend/common/logger.py` (linhas 8–9).
- Os três padrões, na borda: `backend/bff.py` (linhas 46–57) — `PUB` (5570), `DEALER` (5561)
  e `PUSH` (5567) instanciados no mesmo módulo.

---

## 6) Persistência no MySQL

**Criar o banco (uma vez):**
```bash
python backend/services/database/mysql/setup_db.py
```
Com o `.env` apontando para o MySQL (`DB_PASSWORD` etc.), o terminal do backend exibe a linha
que indica a conexão ativa:
```
[DB] INFO: MySQL conectado (fonte da verdade).
```
Caso apareça `MySQL indisponivel (...); usando memoria (fallback ...)`, o sistema executa em
memória (sem persistência).

**Consultar os dados persistidos (SQL):** após submeter uma versão pela interface:
```sql
USE tcc_db;
SELECT id, aluno_id, numero, tipo, vigente, created_at FROM versoes ORDER BY id DESC;
SELECT evento_id, tipo_evento, aluno_id, data_evento FROM historico_eventos ORDER BY id DESC;
```
Após reiniciar o backend, os registros permanecem no banco.

**Onde está no código**
- Conexão / fonte da verdade: `backend/common/db.py` `Repositorio.__init__` (linhas 33–39) —
  conecta e registra `MySQL conectado (fonte da verdade).`; em caso de falha, usa o modo em memória.
- Gravação da versão: `backend/common/db.py` `salvar_versao` (linhas 120–135) — `INSERT INTO
  versoes`, marcando a nova como `vigente` e as anteriores como não vigentes.
- Gravação de proposta / parecer: `salvar_proposta` (linhas 62–77), `salvar_parecer` (linhas 160–171).
- Leitura pela IA a partir do banco: `texto_versao_vigente` (linhas 137–148) — a IA reavalia a
  versão vigente lida do MySQL.
- Idempotência persistida: `registrar_evento` (linhas 211–229) — `INSERT IGNORE` na tabela
  `historico_eventos`, cujo `evento_id` é `UNIQUE` (`bd.sql`, linhas 74–81); um evento repetido
  não produz efeito duplicado.
- Recuperação do estado ao reiniciar: `backend/bff.py` `_rehidratar` (linhas 541–573) — ao
  iniciar, o BFF relê propostas/versões/pareceres do MySQL para o modelo de leitura da interface.

---

## 7) Relatórios gerenciais (perfil Coordenador) — PUSH/PULL

Com o perfil Coordenador, utilize a ação de gerar relatório (panorama de TCCs). O pedido segue
pelo padrão PUSH/PULL: o serviço de relatórios divide o trabalho, distribui subtarefas aos
*workers*, coleta os resultados parciais, consolida o panorama e publica `relatorio_gerado`.

No terminal, observa-se:
```
[Relatorios]        solicitacao '...' : 4 subtarefas ventiladas aos workers
[Relatorios-Worker] chunk 0 agregado: N registros
[Relatorios-Worker] chunk 1 agregado: N registros
[Relatorios]        parcial recebido do sink (x/4) ... panorama consolidado e publicado
```

**Onde está no código**
- Pedido (borda): `backend/bff.py` `gerar_relatorio` (linhas 396–400) — envia por `PUSH` para
  `relatorio_req`.
- Pipeline PUSH/PULL: `backend/services/relatorios/service.py` (linhas 24–27) — sockets
  `req`(PULL) / `vent`(PUSH) / `sink`(PULL) / `pub`; `gerar` (linhas 47–69) distribui 4 subtarefas,
  coleta os parciais e publica `relatorio_gerado`.
- Workers em paralelo: `backend/services/relatorios/worker.py` (linhas 15–16, 31–38) —
  `PULL.connect(vent)` + `PUSH.connect(sink)`; o `run.py` inicia 2 workers (linhas 32–33), e o
  *round-robin* do PULL distribui cada subtarefa a um único worker.
- Resultado na interface: `backend/bff.py` (linhas 146–147) mantém o último panorama, exposto em
  `GET /api/relatorios/ultimo` (linhas 475–476).

---

## Credenciais de demonstração

Correspondem aos seeds do banco (`bd.sql`) e funcionam com ou sem MySQL:

| Perfil | E-mail | Senha |
|---|---|---|
| Aluno | `aluno@unifei.edu.br` | `aluno123` |
| Orientador | `orientador@unifei.edu.br` | `orient123` |
| Coordenador | `coord@unifei.edu.br` | `coord123` |
| Banca | `banca@unifei.edu.br` | `banca123` |

Seeds: `backend/services/database/mysql/bd.sql` (linhas 15–19); modo em memória:
`backend/common/db.py` (`USUARIOS_DEMO`, linhas 19–24).

---

## Portas

| Porta | Uso |
|---|---|
| 3000 | BFF (API REST) e, após `npm run build`, a interface |
| 5173 | Vite (interface, modo desenvolvimento) |
| 5561 | Autenticação (ROUTER) |
| 5555 / 5562 / 5563 / 5566 | Documentos / IA / Avaliação / Notificações (PUB) |
| 5556 / 5564 | Propostas / Bancas & Defesas (PUB) |
| 5565 / 5567 / 5568 / 5569 | Relatórios (PUB / req / ventilador / sink) |
| 5570 | BFF (PUB na malha) |
| 5571 | Provedor de LLM (stub HTTP, quando `LLM_PROVIDER=http`) |

Definição: `backend/common/config.py` (`PORTAS`, linhas 26–43).

---

## Solução de problemas

- **Porta 3000 ocupada:** encerre um processo BFF/Node anterior ou reinicie a máquina.
- **A segunda máquina não abre a interface:** verifique a rede, o IP e a liberação da porta 3000 no firewall.
- **`MySQL indisponivel ... using password: NO`:** falta o `DB_PASSWORD` no `.env` (ou o MySQL não está em execução). Sem ele, o sistema executa em memória, sem persistência.
- **`Gemini indisponível`:** chave ou modelo inválidos; o sistema retorna automaticamente ao provedor `simulado`.
- **Benchmark com erro de porta:** encerre o `npm run backend` antes de executá-lo (conflito nas portas 5570/5555/5562).
- **`npm`/PowerShell bloqueado:** `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.
