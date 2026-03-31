/** Shared SSE reader — used by chat and test endpoints. */
export async function readSSEStream(res, onToken, onStateUpdate) {
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  const reader  = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer    = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop(); // hold incomplete trailing chunk

    for (const part of parts) {
      if (!part.startsWith('data: ')) continue;
      try {
        const event = JSON.parse(part.slice(6));
        if (event.type === 'token' && onToken)       onToken(event.content);
        if (event.type === 'state' && onStateUpdate) onStateUpdate(event.data);
      } catch { /* skip malformed chunk */ }
    }
  }
}
