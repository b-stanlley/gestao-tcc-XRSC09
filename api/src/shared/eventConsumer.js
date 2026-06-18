import zmq from 'zeromq';
import * as notificationController from '../notifications/notificationController.js';

async function startConsumer() {
  try {
    const sub = new zmq.Subscriber();
    sub.connect('tcp://127.0.0.1:5555');
    sub.subscribe('');

    console.log('ZeroMQ Consumer rodando...');

    for await (const [topic, msg] of sub) {
      try {
        const eventName = topic.toString();
        const data = JSON.parse(msg.toString());
        
        console.log(`Evento Recebido: ${eventName}`, data);

        if (eventName === 'versao_submetida') {
            // Ex: Notificar o orientador baseado na entrega
            await notificationController.createNotification(1, 'Nova submissão de documento recebida.');
        } else if (eventName === 'feedback_enviado') {
            // Ex: Notificar o aluno
            await notificationController.createNotification(2, 'Novo feedback recebido sobre seu TCC.');
        }
      } catch (innerErr) {
        console.error('[ZeroMQ Consumer] Error handling message:', innerErr.message);
      }
    }
  } catch (err) {
    console.warn('[ZeroMQ Consumer] Failed to connect or subscribe. Consumer is running in inactive state:', err.message);
  }
}

startConsumer().catch(err => {
  console.warn('[ZeroMQ Consumer] Top-level handler warning:', err.message);
});
