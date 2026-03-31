import { readSSEStream } from './stream.js';

const API_BASE = import.meta.env.VITE_API_URL || ''; // '' → Vite proxy in dev, Railway URL in prod

export async function sendMessage(sessionId, message, onToken, onStateUpdate) {
  const res = await fetch(`${API_BASE}/chat/${sessionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  await readSSEStream(res, onToken, onStateUpdate);
}
