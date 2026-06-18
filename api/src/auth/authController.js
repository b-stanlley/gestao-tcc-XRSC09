import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import db from '../shared/db.js';

const SECRET_KEY = process.env.JWT_SECRET || 'sintcc-secret-key';

export const login = async (req, res) => {
  const { email, password } = req.body;
  try {
    const [users] = await db.query('SELECT * FROM users WHERE email = ?', [email]);
    
    if (users.length === 0) {
      return res.status(401).json({ message: 'Credenciais inválidas' });
    }

    const user = users[0];
    let isPasswordCorrect = false;

    if (user.password_hash === password) {
      isPasswordCorrect = true;
    } else {
      try {
        isPasswordCorrect = await bcrypt.compare(password, user.password_hash);
      } catch (err) {
        isPasswordCorrect = false;
      }
    }

    if (!isPasswordCorrect) {
      return res.status(401).json({ message: 'Credenciais inválidas' });
    }

    const token = jwt.sign({ id: user.id, role: user.role }, SECRET_KEY, { expiresIn: '1h' });
    return res.json({ token, user: { id: user.id, name: user.name, role: user.role } });
  } catch (error) {
    console.error('[DB Error, using fallback credentials]:', error.message);
    
    // Fallback simulation credentials for smooth demo behavior when DB is not configured
    if (email === 'estudante@univ.edu' && password === '123') {
      const token = jwt.sign({ id: 1, role: 'student' }, SECRET_KEY, { expiresIn: '1h' });
      return res.json({ token, user: { id: 1, name: 'Estudante Teste', role: 'student' } });
    }
    if (email === 'coordenador@univ.edu' && password === '123') {
      const token = jwt.sign({ id: 2, role: 'coordinator' }, SECRET_KEY, { expiresIn: '1h' });
      return res.json({ token, user: { id: 2, name: 'Coordenador Teste', role: 'coordinator' } });
    }
    if (email === 'orientador@univ.edu' && password === '123') {
      const token = jwt.sign({ id: 3, role: 'advisor' }, SECRET_KEY, { expiresIn: '1h' });
      return res.json({ token, user: { id: 3, name: 'Orientador Teste', role: 'advisor' } });
    }
    
    return res.status(401).json({ message: 'Credenciais inválidas ou erro no banco.' });
  }
};
