# Documentação de Contexto de Desenvolvimento e Arquitetura do SINTCC

Este arquivo serve como o repositório central de contexto, arquitetura e instruções operacionais para Inteligências Artificiais e Desenvolvedores sobre o **SINTCC (Sistema Integrado de Gestão de TCC)**. Ele contempla toda a engenharia do projeto, desde a interface até as rotas do servidor de eventos para garantir continuidade perfeita no desenvolvimento.

---

## 📸 1. Resumo Executivo e Regras de Negócio

O **SINTCC** (Sistema Integrado de Gestão de TCC) é um ambiente acadêmico robusto desenvolvido para mediar as interações e gerenciar o fluxo de submissões e avaliações de Trabalho de Conclusão de Curso (TCC). O sistema provê três visões focadas em personas chave:

1. **Alunos Universitários:**
   - Cadastram propostas de temas iniciais contendo título, justificativa e metodologia detalhada.
   - Submetem rascunhos físicos e versões de andamento de monografias (arquivos do tipo `.pdf`) baseados nos cronogramas.
   - Solicitam e visualizam a **Análise Inteligente de IA** (através da integração direta do Gemini) que valida a consistência metodológica do trabalho.
   - Recebem e respondem aos pareceres emitidos por seus respectivos orientadores.

2. **Orientadores (Advisors):**
   - Acompanham seus alunos vinculados a propostas.
   - Revisam os rascunhos físicos submetidos (PDFs).
   - Emitem pareceres oficiais (Aprovado, Ajustes Necessários, ou Reprovado) que alteram o status da proposta na base de dados e programam alertas em tempo de execução.
   - **Criam novas tarefas/etapas de TCC personalizadas** atribuindo a data limite (Deadline), o tipo específico de documento requerido (ex: *Relatório Parcial*, *Versão Completa de Monografia*, *Slides de Apresentação de Banca*) e instruções detalhadas metodológicas.

3. **Coordenadores Gerais (Coordinators):**
   - Gerenciam o cronograma global de submissões e criam prazos globais de entrega.
   - Acompanham o status consolidado de todos os alunos e suas respectivas propostas e submissões atuais.

---

## 🛠️ 2. Novas Funcionalidades e Melhorias Implementadas Recentemente

### A. Criação de Tarefas Acadêmicas por Orientadores
- **Lógica e UI:** Implementado painel dedicado de criação de tarefas disponível aos Orientadores (`activeTab === 'create_task'`). O formulário permite selecionar o aluno orientado a partir de uma lista dinâmica vinculada a propostas, definir data limite utilizando input interativo, selecionar o tipo de documento desejado via dropdown, e detalhar as instruções em um campo de texto.
- **Mudança Arquitetural Segura no Servidor:** O endpoint POST `/api/deliveries` foi atualizado em `api/src/server.js` permitindo a autorização de orientadores para que consigam publicar prazos customizados, mantendo o controle de autenticação:
  ```js
  app.post('/api/deliveries', authenticate, authorize(['coordinator', 'advisor']), deliveryController.createDelivery);
  ```

### B. Sistema de Feedback e Notificações On-Screen (Toasts)
- **Fechamento do fluxo de Parecer:** Ao registrar o parecer de um rascunho de monografia, o sistema agora publica o evento no barramento, redireciona o orientador para a tela inicial de listagem e gera um alerta temporário flutuante em formato de **Toast** (`fixed bottom-6 right-6 z-[9999]`). 
- **Estética:** O popup possui fundo escuro, borda realçada em tons esmeralda (`border-l-4 border-l-emerald-500 bg-slate-950`), ícone de sucesso e some automaticamente após 5 segundos ou ao clicar em fechar.

---

## 📂 3. Visão Geral da Arquitetura do Software

O SINTCC adota uma arquitetura baseada em Clean Architecture moderada e desacoplada em duas camadas principais:

```
├── .env.example              # Variáveis de ambiente padrão (GEMINI_API_KEY, etc.)
├── package.json              # Metadados de dependência e scripts de inicialização
├── GEMINI.md                 # [ESTE ARQUIVO] Documento mestre de contexto da IA
├── API_DOCUMENTATION.md      # Detalhes de endpoints e contratos JSON
├── api/                      # Camada de Servidor (Node.js + Express)
│   ├── src/
│   │   ├── server.js         # Entrada do backend, registro de rotas mundiais e middleware Vite
│   │   ├── auth/             # Emissão de JWTs e validação de credenciais
│   │   ├── deliveries/       # Criação e sincronização de prazos e tarefas
│   │   ├── feedback/         # Criação de pareceres e notas do orientador
│   │   ├── ia/               # Integração direta com a API do Gemini
│   │   ├── notifications/    # Armazenamento e entrega de histórico de alertas
│   │   ├── proposals/        # Registro e checagem de propostas de temas
│   │   ├── shared/           # Database mock, middlwares de auth / autorização e EventBus 
│   │   └── submissions/      # Gerenciamento de Upload de rascunhos físicos via Multer
│   ├── db_schema.sql         # Esquema analítico e estrutural do banco de dados relacional
│   └── DOCUMENTATION.md      # Documento técnico original da API
├── src/                      # Camada de Interface de Usuário (React + Vite SPA)
│   ├── App.jsx               # Ponto centralizador de estados React e fluxo de navegação condicional
│   ├── main.jsx              # Inicializador global do React
│   └── index.css             # Estilização utilitária moderna do Tailwind v4
└── uploads/                  # Armazenamento em disco das monografias (PDFs) submetidas pela API
```

---

## 🗄️ 4. Esquema Estrutural do Banco de Dados

As relações estão mapeadas conforme representação lógica do arquivo `api/db_schema.sql`:

```sql
-- Usuários do SINTCC (student, advisor, coordinator)
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL
);

-- Propostas enviadas pelos discentes
CREATE TABLE IF NOT EXISTS proposals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  title VARCHAR(255) NOT NULL,
  justification TEXT,
  methodology TEXT,
  status VARCHAR(50) DEFAULT 'pending',
  ai_feedback TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (student_id) REFERENCES users(id)
);

-- Etapas e Cronogramas Globais ou Individuais
CREATE TABLE IF NOT EXISTS deliveries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  deadline DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Submissões físicas das versões de andamento de TCC
CREATE TABLE IF NOT EXISTS submissions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  delivery_id INT NOT NULL,
  student_id INT NOT NULL,
  file_path VARCHAR(255) NOT NULL,
  version VARCHAR(55) DEFAULT '1.0',
  submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (delivery_id) REFERENCES deliveries(id),
  FOREIGN KEY (student_id) REFERENCES users(id)
);
```

---

## ⚡ 5. Subsistema Crítico: Barramento de Eventos SINTCC

O fluxo de dados e comunicação assíncrona entre papéis baseia-se em um Barramento de Eventos estruturado com padrão **Pub/Sub** utilizando a biblioteca **ZeroMQ** do Node.js:
- **Editor/Publicador (`api/src/shared/eventBus.js`):** Inicializa e vincula o socket ZeroMQ na porta local `tcp://127.0.0.1:5555`. Quando é feito um envio ou alterado um parecer, invoca `publishEvent(eventName, payload)`. Caso o módulo nativo não esteja compilado de forma limpa, o sistema ativa uma simulação em memória (`Event Fallback Sim`) transparente para evitar quebras.
- **Consumidor/Escritor (`api/src/shared/eventConsumer.js`):** Escuta o barramento nos canais correspondentes. Ao capturar eventos como `versao_submetida` ou `feedback_enviado`, encaminha as notificações automaticamente para a base do respectivo destinatário.

**Principais tópicos do barramento:**
- `"proposta_submetida"`: Publicada quando um aluno registra uma nova proposta de tema de TCC.
- `"versao_submetida"`: Publicada quando um arquivo de rascunho de TCC é enviado.
- `"feedback_enviado"`: Publicada quando o orientador emite um parecer final sobre a entrega.

---

## 🤖 6. Inteligência Artificial: Integração com Gemini SDK

O SINTCC utiliza a biblioteca oficial **`@google/genai`** em nível de servidor. 
- **Lógica (`api/src/ia/aiService.js`):** Instancia a classe `GoogleGenAI` injetando de maneira segura a variável de ambiente `process.env.GEMINI_API_KEY` (nunca exposta para a interface cliente).
- **Parâmetros:** Configura o modelo de linguagem rápida de última geração **`gemini-3.5-flash`** combinada com instruções de sistema estritas:
  > *"Você é um experiente orientador acadêmico brasileiro. Ajude a avaliar propostas e revisar documentos de TCC com críticas construtivas e sugestões práticas de aprimoramento em português brasileiro."*
- **Análise Metodológica:** O corretor automático analisa a justificativa, metodologia de pesquisa e estrutura gramatical do texto, retornando recomendações diretamente para o painel de "Revisão Estendida do Aluno".

---

## 💡 7. Guia de Estados Interativos e UI (`src/App.jsx`)

Para atuar na interface de forma concisa, compreenda os principais controladores e seus estados reativos declarados:

1. **`user` e `token`:** Armazenam as informações da sessão do usuário autenticado no sistema. É avaliado em tempo de carregamento com persistência padrão.
2. **`activeTab` (Controle de Visão do Painel):**
   - **Aluno:** 
     * `'dashboard'`: Visão geral do andamento e tarefas.
     * `'proposal'`: Submissão de novos temas com editor dinâmico.
     * `'submissions'`: Dashboard de upload físico de arquivos PDF.
     * `'ai_review'`: Histórico de feedbacks emitidos pelo Gemini.
   - **Orientador:**
     * `'dashboard'`: Histórico e andamento de propostas de seus alunos.
     * `'advisor_feedback'`: Formulário de avaliação de PDFs submetidos.
     * `'create_task'`: Nova tela de criação de tarefas parametrizadas.
   - **Coordenador:**
     * `'dashboard'`: Controle e panorama dos resultados do corpo discente.
     * `'coordinator_schedule'`: Gestão e modificações do cronograma global do colegiado.
3. **`toast` e `triggerToast`:** Sistema unificado de alertas sem bloqueio de thread. Chamando `triggerToast("mensagem", "success" | "error" | "info")` renderiza a caixa animada inferior imediatamente por 5 segundos.
4. **`deliveries` e `setDeliveries`:** Array dinâmico populado da API de prazos acadêmicos. Quando alterado pela criação do orientador ou do coordenador, a listagem reage imediatamente, atualizando o progresso das pendências dos discentes.

---

## ⚙️ 8. Regras Metodológicas Essenciais para Manutenções Futuras

Toda nova inteligência artificial ou desenvolvedor que for ler este contexto deve seguir e manter as seguintes diretrizes intactas recomendadas para o SINTCC:

1. **Sem Popups Nativos:** É terminantemente proibido reintroduzir o método `window.alert()` ou `confirm()` para notificações operacionais do sistema. Use consistentemente a função `triggerToast(...)` para manter o visual limpo, moderno e eye-safe.
2. **Consistência de Enums e Roles:** Toda lógica de validação baseia-se estritamente nas roles `"student"`, `"advisor"` e `"coordinator"`. Não instancie roles intermediárias sem registrar as devidas permissões correspondentes na API.
3. **Padrão Estético de Paleta:** Manter o tema **Dark Slate UI** presente no projeto. As classes utilitárias baseiam-se em fundos profundamente contrastados em cinza/azul escuro (`bg-slate-900`/`bg-slate-950`), linhas finas em tom grafite escuro (`border-slate-850`/`border-slate-800`), e realces suaves na paleta esmeralda (`emerald-500`, `emerald-600` e fundos em `emerald-500/10` para estados ativos) para feedback e botões de chamada primária à ação.
4. **Resoluções e Responsividade:** Use classes do Tailwind de forma que todas as tabelas em dispositivos menores apresentem overflow horizontal limpo ou colapso fluido, sem quebrar o alinhamento da grade principal ou o visual imersivo dos painéis gerenciais.
