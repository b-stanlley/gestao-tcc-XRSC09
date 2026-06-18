# Documentação Técnica SINTCC

## 1. Arquitetura
Sistema baseado em arquitetura desacoplada (Clean Architecture base):
- **Camada de Apresentação**: React SPA + Tailwind + Shadcn.
- **Camada de Aplicação/Serviço**: Node.js + Express (regras de negócio).
- **Camada de Infraestrutura/Dados**: MySQL (Relacional) e ZeroMQ (Eventos).

## 2. Estrutura de Pastas (API)
- `api/src/auth/`: Lógica de autenticação.
- `api/src/deliveries/`: Gestão de entregas.
- `api/src/feedback/`: Feedback do orientador.
- `api/src/ia/`: Integração Ollama.
- `api/src/notifications/`: Sistema de avisos.
- `api/src/proposals/`: Propostas TCC.
- `api/src/shared/`: Database, Auth Middleware, EventBus.
- `api/src/submissions/`: Gestão de documentos.

## 3. Modelo de Banco de Dados
- `users`: (id, name, email, password_hash, role)
- `proposals`: (id, student_id, title, summary, status)
- `deliveries`: (id, coordinator_id, name, description, deadline)
- `submissions`: (id, delivery_id, student_id, file_path, version)
- `feedbacks`: (id, submission_id, advisor_id, comment, status)
- `notifications`: (id, user_id, message, is_read)

## 4. Integração IA (Ollama)
- Módulo `ia/aiService.js` consome a API oficial do Ollama (/api/generate).
- Configuração dinâmica de modelos (ex: qwen3, llama).

## 5. Eventos (ZeroMQ)
- Subsistema assíncrono via `src/shared/eventBus.js` (Publisher) e `src/shared/eventConsumer.js` (Subscriber).
