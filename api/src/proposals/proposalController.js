import db from '../shared/db.js';
import { publishEvent } from '../shared/eventBus.js';

export const submitProposal = async (req, res) => {
  const { title, summary } = req.body;
  const student_id = req.user.id;

  try {
    const [result] = await db.query(
      'INSERT INTO proposals (student_id, title, summary) VALUES (?, ?, ?)',
      [student_id, title, summary]
    );

    await publishEvent('proposta_submetida', { proposal_id: result.insertId, student_id });
    res.status(201).json({ message: 'Proposta submetida', proposal_id: result.insertId });
  } catch (error) {
    res.status(500).json({ message: 'Erro ao submeter proposta', error });
  }
};
