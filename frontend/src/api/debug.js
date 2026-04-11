const API_BASE = import.meta.env.VITE_API_URL || '';

async function readJson(res) {
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export async function startTrace(sessionId) {
  const res = await fetch(`${API_BASE}/debug/trace/${sessionId}/start`, {
    method: 'POST',
  });
  return readJson(res);
}

export async function stopTrace(sessionId) {
  const res = await fetch(`${API_BASE}/debug/trace/${sessionId}/stop`, {
    method: 'POST',
  });
  return readJson(res);
}

export async function getBackendState(sessionId) {
  const res = await fetch(`${API_BASE}/debug/state/${sessionId}`);
  return readJson(res);
}

export async function patchBackendState(sessionId, patch) {
  const res = await fetch(`${API_BASE}/debug/state/${sessionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ patch }),
  });
  return readJson(res);
}
