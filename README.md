# SINTCC — Sistema Integrado de Gestão de TCC

Este é o **SINTCC (Sistema Integrado de TCC)**, uma plataforma web moderna desenvolvida para simplificar o fluxo de submissão, elegibilidade e acompanhamento de propostas e entregas de Monografias/TCC para alunos e coordenadores. 

A plataforma possui integração inteligente de IA para homologação e verificação preliminar das propostas de TCC, ajudando o colegiado de curso a atuar com maior agilidade e precisão.

---

## 🛠️ Tecnologias Utilizadas

O ecossistema do **SINTCC** foi projetado com uma arquitetura robusta e escalável:

- **Frontend:** React 19, Vite, Tailwind CSS v4, Lucide Icons, e Framer Motion (para transições dinâmicas de interface).
- **Backend (API):** Node.js com Express e `tsx`.
- **Banco de Dados:** MySQL 2 (integrando mapeamentos lógicos relacionais).
- **Processamento de Eventos (Barramento):** ZeroMQ (responsável pelo barramento de escuta e eventos locais).
- **Inteligência Artificial:** Integração direta com a API do **Gemini 3.5** (Google GenAI) para revisões automáticas, verificação de elegibilidade de temas e conformidade normativa.

---

## 📂 Organização de Diretórios

- `/src`: Contém a interface do usuário em React e Vite (painéis do aluno, orientador, coordenador geral e formulários interativos).
- `/api`: Servidor backend Node.js + Express que expõe os endpoints REST e gerencia o banco de dados e mensageria.
  - `api/src/server.js`: Ponto de entrada do backend.
  - `api/db_schema.sql`: Script estrutural SQL para criação e ativação do banco de dados MySQL de produção ou simulações locais.
- `/uploads`: Diretório reservado para armazenamento de relatórios e rascunhos de monografias enviados pelos alunos.

---

## 🚀 Passo a Passo para Inicialização Local

Siga as instruções abaixo para configurar o ambiente e executar o projeto em sua máquina:

### 1. Pré-Requisitos
Certifique-se de ter instalado em sua máquina:
- **Node.js** (Versão 18 ou superior recomendada)
- **MySQL Server** ativo e configurado
- Conexão com a Internet para chamadas dos modelos de linguagem da Google API.

### 2. Instalação de Dependências
Abra o terminal no diretório raiz do projeto e execute:
```bash
npm install
```

### 3. Configuração das Variáveis de Ambiente (`.env`)
Duplique o arquivo `.env.example` na raiz do projeto e renomeie-o para `.env`:
```bash
cp .env.example .env
```
Abra o arquivo `.env` e preencha com as suas chaves correspondentes:
```env
# Chave da API do Gemini obtida no Google AI Studio (Necessária para a IA Homologadora)
GEMINI_API_KEY="SUA_CHAVE_AQUI"

# URL de hospedagem da aplicação
APP_URL="http://localhost:3000"
```

### 4. Configuração do Banco de Dados
Acesse seu gerenciador do MySQL (como MySQL Workbench, phpMyAdmin ou terminal CLI) e execute o script contido em:
```path
/api/db_schema.sql
```
Este script inicializa todas as tabelas lógicas necessárias (`proposals`, `deliveries`, `submissions`, `feedbacks`, etc.) estruturando o banco relacional completo do SINTCC.

---

## 💻 Comandos e Scripts Disponíveis

Todos os comandos abaixo devem ser executados a partir do diretório raiz do projeto:

### Executar em Ambiente de Desenvolvimento
Executa o backend com recarregamento automático (hot reload) utilizando `tsx`, servindo tanto a API REST como servindo o frontend integrado via middleware Vite na porta `3000` (padrão de ambiente de nuvem):
```bash
npm run dev
```

### Compilar para Produção (Build)
Compila todo o código do frontend React otimizando os arquivos estáticos e gerando a pasta de distribuição `dist`:
```bash
npm run build
```

### Visualizar Build de Produção (Preview)
Inicia uma visualização local para testar o bundle estático gerado do frontend:
```bash
npm run preview
```

### Limpar Arquivos de Build
Remove a pasta `dist` gerada em execuções anteriores garantindo um build limpo:
```bash
npm run clean
```

---

## 🤝 Fluxo de Perfis de Usuário no Painel

1. **Aluno Universitário:** submete propostas de tema de TCC (Título, Justificativa e Metodologia) e envia relatórios/rascunhos em PDF.
2. **Coordenador Geral / Orientador:** visualiza estatísticas do colegiado em tempo real, gerencia o cronograma acadêmico de entregas do semestre, avalia pendências de temas enviados recebendo auxílio de insights de elegibilidade automáticos gerados pela IA do Gemini SINTCC.
