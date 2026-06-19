CREATE DATABASE IF NOT EXISTS tcc_db;
USE tcc_db;

-- Usuarios e perfis (RBAC) — usados pela Autenticacao (DEALER/ROUTER)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(160) NOT NULL UNIQUE,
    senha_hash CHAR(64) NOT NULL,                          -- SHA2(senha, 256)
    role ENUM('aluno','orientador','coordenador','banca') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Usuarios de demonstracao (senhas: aluno123 / orient123 / coord123 / banca123)
INSERT IGNORE INTO usuarios (nome, email, senha_hash, role) VALUES
 ('Larissa (Aluno)',     'aluno@unifei.edu.br',      SHA2('aluno123', 256),  'aluno'),
 ('Bruno (Orientador)',  'orientador@unifei.edu.br', SHA2('orient123', 256), 'orientador'),
 ('Coordenacao de TCC',  'coord@unifei.edu.br',      SHA2('coord123', 256),  'coordenador'),
 ('Membro da Banca',     'banca@unifei.edu.br',      SHA2('banca123', 256),  'banca');

CREATE TABLE IF NOT EXISTS cursos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(120) NOT NULL
);

CREATE TABLE IF NOT EXISTS turmas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    curso_id INT,
    nome VARCHAR(120) NOT NULL,
    FOREIGN KEY (curso_id) REFERENCES cursos(id)
);

CREATE TABLE IF NOT EXISTS propostas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    orientador_id INT,
    titulo VARCHAR(255),
    resumo TEXT,
    objetivos TEXT,
    area VARCHAR(120),
    palavras_chave VARCHAR(255),
    arquivo VARCHAR(255),
    status ENUM('pendente','aprovada','rejeitada','ajustes') DEFAULT 'pendente',
    avaliador_id INT,
    observacao TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_propostas_aluno (aluno_id)
);

-- Versoes dos documentos do TCC (fonte da verdade do versionamento)
CREATE TABLE IF NOT EXISTS versoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    entrega_id INT,                                        -- entrega dinamica (opcional)
    numero INT NOT NULL,
    tipo VARCHAR(50) DEFAULT 'desenvolvimento',            -- proposta | parcial | final | desenvolvimento
    texto MEDIUMTEXT,
    autor VARCHAR(120),
    observacoes TEXT,
    vigente BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_versoes_vigente (aluno_id, vigente)
);

CREATE TABLE IF NOT EXISTS feedbacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    feedback TEXT,
    secoes_criticas JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trilha de eventos da coreografia (idempotencia + relatorios + evidencia)
CREATE TABLE IF NOT EXISTS historico_eventos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    evento_id VARCHAR(64) UNIQUE,
    tipo_evento VARCHAR(64),
    aluno_id INT,
    dados JSON,
    data_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Entregas DINAMICAS: o coordenador cria; nomes totalmente configuraveis — RF (entregas)
CREATE TABLE IF NOT EXISTS entregas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(160) NOT NULL,
    descricao TEXT,
    curso_id INT,
    turma_id INT,
    prazo DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pareceres PADRONIZADOS (formulario: criterios + nota + decisao) — RF04 / JEMS
CREATE TABLE IF NOT EXISTS pareceres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    versao_id INT,
    avaliador_id INT,
    nota DECIMAL(4,2),
    decisao ENUM('aprovado','correcoes','reprovado') DEFAULT 'correcoes',
    criterios JSON,                                        -- {originalidade, metodologia, escrita, ...}
    comentario TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pareceres_aluno (aluno_id)
);

-- Bancas e defesas — RF06 / RF07 (Cenario 2)
CREATE TABLE IF NOT EXISTS bancas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    orientador_id INT,
    data_defesa DATETIME,
    status ENUM('definida','agendada','realizada') DEFAULT 'definida',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS banca_membros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    banca_id INT NOT NULL,
    avaliador_id INT,
    nome VARCHAR(120),
    confirmado BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (banca_id) REFERENCES bancas(id)
);

CREATE TABLE IF NOT EXISTS defesas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    banca_id INT NOT NULL,
    aluno_id INT NOT NULL,
    nota_final DECIMAL(4,2),
    resultado ENUM('aprovado','reprovado'),
    parecer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (banca_id) REFERENCES bancas(id)
);

-- Notificacoes persistidas — RF05
CREATE TABLE IF NOT EXISTS notificacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    destino_role VARCHAR(20),                              -- aluno|orientador|coordenador|banca
    aluno_id INT,
    tipo VARCHAR(64),
    mensagem VARCHAR(255),
    lida BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notif_role (destino_role, lida)
);
