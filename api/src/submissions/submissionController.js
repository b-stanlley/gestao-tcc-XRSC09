import db from '../shared/db.js';
import { publishEvent } from '../shared/eventBus.js';
import multer from 'multer';

const upload = multer({ dest: 'uploads/' });

export const submitDocument = async (req, res) => {
  const { delivery_id, version } = req.body;
  const student_id = req.user.id;
  const file_path = req.file.path;

  try {
    const [result] = await db.query(
      'INSERT INTO submissions (delivery_id, student_id, file_path, version) VALUES (?, ?, ?, ?)',
      [delivery_id, student_id, file_path, version]
    );

    await publishEvent('versao_submetida', { submission_id: result.insertId });
    res.status(201).json({ message: 'Documento submetido', submission_id: result.insertId });
  } catch (error) {
    res.status(500).json({ message: 'Erro ao submeter documento', error });
  }
};

export { upload };
