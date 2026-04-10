/** Shared SSE reader used by chat and test endpoints. */
export async function readSSEStream(res, onToken, onStateUpdate) {
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }

  if (!res.body) {
    throw new Error('Response body is missing');
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  const processEvent = (part) => {
    const dataLines = part
      .split(/\r?\n/)
      .filter(line => line.startsWith('data:'))
      .map(line => line.slice(5).trimStart());

    if (dataLines.length === 0) return;

    let event;
    try {
      event = JSON.parse(dataLines.join('\n'));
    } catch {
      return;
    }

    if (event.type === 'token' && onToken) onToken(event.content);
    if (event.type === 'state' && onStateUpdate) onStateUpdate(event.data);
    if (event.type === 'error') throw new Error(event.content || 'Stream error');
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split(/\r?\n\r?\n/);
    buffer = parts.pop() ?? '';

    for (const part of parts) {
      processEvent(part);
    }
  }

  buffer += decoder.decode();
  if (buffer.trim()) {
    processEvent(buffer);
  }
}
