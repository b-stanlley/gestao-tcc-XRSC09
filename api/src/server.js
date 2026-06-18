console.log('[DEBUG] Starting server.js, NODE_ENV:', process.env.NODE_ENV);

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import path from 'path';
import { fileURLToPath } from 'url';
import { createServer as createViteServer } from 'vite';
import * as authController from './auth/authController.js';
import * as proposalController from './proposals/proposalController.js';
import * as aiController from './ia/aiController.js';
import * as deliveryController from './deliveries/deliveryController.js';
import * as submissionController from './submissions/submissionController.js';
import * as feedbackController from './feedback/feedbackController.js';
import * as notificationController from './notifications/notificationController.js';
import { authenticate, authorize } from './shared/authMiddleware.js';
import './shared/eventConsumer.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(helmet({
    contentSecurityPolicy: false,
    frameguard: false
  }));
  app.use(cors());
  app.use(express.json());

  // Rotas da API
  app.post('/api/auth/login', authController.login);
  app.post('/api/proposals', authenticate, proposalController.submitProposal);
  app.post('/api/ai/analyze', authenticate, aiController.analyzeDocument);
  app.post('/api/deliveries', authenticate, authorize(['coordinator', 'advisor']), deliveryController.createDelivery);
  app.post('/api/submissions', authenticate, submissionController.upload.single('file'), submissionController.submitDocument);
  app.post('/api/feedback', authenticate, authorize(['advisor']), feedbackController.submitFeedback);
  app.get('/api/notifications', authenticate, notificationController.getNotifications);
  app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', message: 'SINTCC API rodando' });
  });

  // Vite ou estático
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.join(__dirname, '../../dist')));
    app.get('*', (req, res) => {
      res.sendFile(path.join(__dirname, '../../dist/index.html'));
    });
  }

  try {
    app.listen(PORT, '0.0.0.0', () => {
      console.log(`Servidor rodando em 0.0.0.0:${PORT}`);
    });
  } catch (err) {
    console.error('[DEBUG] Failed to start server:', err);
  }
}

startServer();
