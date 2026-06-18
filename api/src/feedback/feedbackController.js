import db from '../shared/db.js';
import { publishEvent } from '../shared/eventBus.js';

export const submitFeedback = async (req, res) => {
  const { submission_id, comment, status } = req.body;
  const advisor_id = req.user.id;

  try {
    const [result] = await db.query(
      'INSERT INTO feedbacks (submission_id, advisor_id, comment, status) VALUES (?, ?, ?, ?)',
      [submission_id, advisor_id, comment, status]
    );

    await publishEvent('feedback_enviado', { feedback_id: result.insertId, submission_id });
    res.status(201).json({ message: 'Feedback enviado', feedback_id: result.insertId });
  } catch (error) {
    res.status(500).json({ message: 'Erro ao enviar feedback', error });
  }
};
