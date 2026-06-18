import db from '../shared/db.js';

export const getNotifications = async (req, res) => {
  try {
    const [notifications] = await db.query(
      'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC',
      [req.user.id]
    );
    res.json(notifications);
  } catch (error) {
    res.status(500).json({ message: 'Erro ao buscar notificações', error });
  }
};

export const createNotification = async (user_id, message) => {
  await db.query(
    'INSERT INTO notifications (user_id, message) VALUES (?, ?)',
    [user_id, message]
  );
};
