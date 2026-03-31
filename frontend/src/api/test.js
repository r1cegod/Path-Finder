import { readSSEStream } from './stream.js';

const API_BASE = import.meta.env.VITE_API_URL || ''; // '' → Vite proxy in dev, Railway URL in prod

/** Submit MI or RIASEC results. payload = { brain_type? } or { riasec_top? } */
export async function submitTest(sessionId, payload, onStateUpdate) {
  const res = await fetch(`${API_BASE}/test/${sessionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  await readSSEStream(res, null, onStateUpdate);
}
