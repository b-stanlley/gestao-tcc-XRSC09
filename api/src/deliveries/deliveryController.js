import db from '../shared/db.js';
import { publishEvent } from '../shared/eventBus.js';

export const createDelivery = async (req, res) => {
  const { name, description, deadline } = req.body;
  const coordinatorId = req.user.id;

  try {
    const [result] = await db.query(
      'INSERT INTO deliveries (coordinator_id, name, description, deadline) VALUES (?, ?, ?, ?)',
      [coordinatorId, name, description, deadline]
    );

    await publishEvent('entrega_criada', { delivery_id: result.insertId });
    res.status(201).json({ message: 'Entrega criada', delivery_id: result.insertId });
  } catch (error) {
    res.status(500).json({ message: 'Erro ao criar entrega', error });
  }
};
