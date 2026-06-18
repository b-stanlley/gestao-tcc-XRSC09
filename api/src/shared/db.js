import mysql from 'mysql2/promise';

const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'sintcc_db',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

// In-Memory Database Store for robust preview without database dependencies
const memoryDb = {
  users: [
    { id: 1, name: 'Estudante Teste', email: 'estudante@univ.edu', password_hash: '123', role: 'student' },
    { id: 2, name: 'Coordenador Teste', email: 'coordenador@univ.edu', password_hash: '123', role: 'coordinator' },
    { id: 3, name: 'Orientador Teste', email: 'orientador@univ.edu', password_hash: '123', role: 'advisor' },
    { id: 4, name: 'Mariana Costa Santana', email: 'mariana@univ.edu', password_hash: '123', role: 'student' },
    { id: 5, name: 'Rodrigo Medeiros Souza', email: 'rodrigo@univ.edu', password_hash: '123', role: 'student' }
  ],
  proposals: [
    { id: 1, student_id: 1, title: 'IA Generativa na Avaliação Escolar', summary: 'Pesquisa sobre grandes modelos de linguagem aplicados ao ensino brasileiro.', status: 'pending' },
    { id: 2, student_id: 4, title: 'IoT no Monitoramento de Barragens de Rejeito', summary: 'Desenvolvimento de sensores de Internet das Coisas para detectar movimentos em barragens de rejeitos de mineração em tempo real.', status: 'pending' },
    { id: 3, student_id: 5, title: 'Blockchain aplicado à Rastreabilidade Logística', summary: 'Uso de contratos inteligentes na blockchain para garantir integridade e transparência em cadeias de suprimentos farmacêuticas.', status: 'approved' }
  ],
  deliveries: [
    { id: 1, name: 'Entrega 1: Proposta de TCC', description: 'Cadastrar o título, justificativa e o resumo da proposta do seu TCC para aprovação do orientador.', deadline: '2026-06-30' }
  ],
  submissions: [
    { id: 1, delivery_id: 1, student_id: 1, file_path: 'uploads/monografia_v1.pdf', version: 1.0, created_at: new Date() },
    { id: 2, delivery_id: 1, student_id: 4, file_path: 'uploads/iot_sensor_relatorio_v1.pdf', version: 1.0, created_at: new Date() }
  ],
  feedbacks: [
    { id: 1, submission_id: 1, advisor_id: 3, comment: 'Interessante proposta inicial! Lembre-se de mapear as referências da ABNT.', status: 'approved', created_at: new Date() }
  ],
  notifications: [
    { id: 1, user_id: 1, message: 'Parabéns, você completou o cadastro no SINTCC!', is_read: false, created_at: new Date() },
    { id: 2, user_id: 1, message: 'Novo feedback recebido de Orientador Teste!', is_read: false, created_at: new Date() }
  ]
};

const emulatedQuery = async (sql, params) => {
  const sqlClean = sql.trim().toUpperCase();
  console.log(`[Emulated DB Query]: ${sqlClean}`, params);

  // Users
  if (sqlClean.includes('USERS WHERE EMAIL =') || sqlClean.includes('FROM USERS WHERE EMAIL =') || sqlClean.includes('FROM USERS WHERE EMAIL=?')) {
    const email = params[0];
    const found = memoryDb.users.filter(u => u.email === email);
    return [found];
  }

  // Proposals
  if (sqlClean.includes('INSERT INTO PROPOSALS')) {
    const [student_id, title, summary] = params;
    const newProp = {
      id: Math.max(...memoryDb.proposals.map(p => p.id), 0) + 1,
      student_id: Number(student_id),
      title,
      summary,
      status: 'pending'
    };
    memoryDb.proposals.push(newProp);
    return [{ insertId: newProp.id }];
  }

  if (sqlClean.includes('SELECT * FROM PROPOSALS') || sqlClean.includes('SELECT * FROM PROPOSAL')) {
    return [memoryDb.proposals];
  }

  // Deliveries
  if (sqlClean.includes('INSERT INTO DELIVERIES')) {
    const [coordinator_id, name, description, deadline] = params;
    const newDel = {
      id: Math.max(...memoryDb.deliveries.map(d => d.id), 0) + 1,
      coordinator_id: Number(coordinator_id),
      name,
      description,
      deadline
    };
    memoryDb.deliveries.push(newDel);
    return [{ insertId: newDel.id }];
  }

  if (sqlClean.includes('SELECT * FROM DELIVERIES')) {
    return [memoryDb.deliveries];
  }

  // Submissions
  if (sqlClean.includes('INSERT INTO SUBMISSIONS')) {
    const [delivery_id, student_id, file_path, version] = params;
    const newSub = {
      id: Math.max(...memoryDb.submissions.map(s => s.id), 0) + 1,
      delivery_id: Number(delivery_id),
      student_id: Number(student_id),
      file_path,
      version: Number(version) || 1.0,
      created_at: new Date()
    };
    memoryDb.submissions.push(newSub);
    return [{ insertId: newSub.id }];
  }

  if (sqlClean.includes('SELECT * FROM SUBMISSIONS')) {
    return [memoryDb.submissions];
  }

  // Feedbacks
  if (sqlClean.includes('INSERT INTO FEEDBACKS')) {
    const [submission_id, advisor_id, comment, status] = params;
    const newFb = {
      id: Math.max(...memoryDb.feedbacks.map(f => f.id), 0) + 1,
      submission_id: Number(submission_id),
      advisor_id: Number(advisor_id),
      comment,
      status,
      created_at: new Date()
    };
    memoryDb.feedbacks.push(newFb);
    
    // Auto-update proposal status or submission status
    const submission = memoryDb.submissions.find(s => s.id === Number(submission_id));
    if (submission) {
      const proposal = memoryDb.proposals.find(p => p.student_id === submission.student_id);
      if (proposal) {
        proposal.status = status === 'approved' ? 'approved' : 'adjustments';
      }
    }
    
    return [{ insertId: newFb.id }];
  }

  if (sqlClean.includes('SELECT * FROM FEEDBACKS')) {
    return [memoryDb.feedbacks];
  }

  // Notifications
  if (sqlClean.includes('INSERT INTO NOTIFICATIONS')) {
    const [user_id, message] = params;
    const newNotif = {
      id: Math.max(...memoryDb.notifications.map(n => n.id), 0) + 1,
      user_id: Number(user_id),
      message,
      is_read: false,
      created_at: new Date()
    };
    memoryDb.notifications.push(newNotif);
    return [{ insertId: newNotif.id }];
  }

  if (sqlClean.includes('SELECT * FROM NOTIFICATIONS')) {
    const userId = Number(params[0]);
    const filtered = memoryDb.notifications.filter(n => n.user_id === userId);
    return [filtered];
  }

  return [[]]; // Default
};

const safePool = {
  query: async (sql, params) => {
    try {
      // Only do real query if configured with full external DB credentials
      if (process.env.DB_HOST && process.env.DB_HOST !== 'localhost') {
        return await pool.query(sql, params);
      }
      return await emulatedQuery(sql, params);
    } catch (err) {
      console.warn('[DB Query failed, using robust memory emulator]:', err.message);
      return await emulatedQuery(sql, params);
    }
  }
};

export default safePool;

