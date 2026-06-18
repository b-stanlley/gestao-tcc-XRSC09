import zmq from 'zeromq';

let pub = null;
let isZmqInitialized = false;

async function initPublisher() {
  try {
    pub = new zmq.Publisher();
    await pub.bind('tcp://127.0.0.1:5555');
    isZmqInitialized = true;
    console.log('[ZeroMQ] Publisher successfully bound to tcp://127.0.0.1:5555');
  } catch (err) {
    console.warn('[ZeroMQ] Error binding publisher. Event bus will run in fallback simulation mode:', err.message);
  }
}

// Lazy/safe run
initPublisher().catch(err => {
  console.error('[ZeroMQ] Initializer uncaught error:', err);
});

export async function publishEvent(eventName, data) {
  console.log(`Event Published: ${eventName}`, data);
  if (isZmqInitialized && pub) {
    try {
      await pub.send([eventName, JSON.stringify(data)]);
    } catch (err) {
      console.warn('[ZeroMQ] Failed to send event over zmq pub:', err.message);
    }
  } else {
    console.log(`[Event Fallback Sim] Broadcast: ${eventName}`);
  }
}
