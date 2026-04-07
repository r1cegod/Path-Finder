import { useState } from 'react';
import Shell from './components/Shell';
import NeuralInterface from './components/chat/NeuralInterface';
import { DEFAULT_APP_STATE, INITIAL_MESSAGES } from './data/mockState';
import { sendMessage } from './api/chat';

export default function App() {
  const [sessionId]               = useState(() => crypto.randomUUID());
  const [activeTab, setActiveTab] = useState('profile');
  const [messages, setMessages]   = useState(INITIAL_MESSAGES);
  const [appState, setAppState]   = useState(DEFAULT_APP_STATE);
  const [isLoading, setIsLoading] = useState(false);

  // Deep-merge: thinking patches (brain_type, riasec_top) come in as partial objects
  function mergeState(newState) {
    setAppState(prev => {
      const merged = { ...prev, ...newState };
      if (newState.thinking) {
        merged.thinking = { ...(prev.thinking ?? {}), ...newState.thinking };
      }
      return merged;
    });
  }

  async function handleSend(text) {
    const userMsg = { id: Date.now() + '', role: 'user', content: text, timestamp: new Date() };
    setMessages(m => [...m, userMsg]);
    setIsLoading(true);

    const asstId = Date.now() + 'a';
    setMessages(m => [...m, { id: asstId, role: 'assistant', content: '', timestamp: new Date() }]);

    try {
      await sendMessage(
        sessionId,
        text,
        (token) => {
          setMessages(m => m.map(msg =>
            msg.id === asstId ? { ...msg, content: msg.content + token } : msg
          ));
        },
        mergeState,
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex h-screen w-full bg-base overflow-hidden">
      <Shell
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        appState={appState}
        sessionId={sessionId}
        onStateUpdate={mergeState}
      />
      <NeuralInterface
        messages={messages}
        isLoading={isLoading}
        onSend={handleSend}
        locked={appState.escalationPending ?? false}
      />
    </div>
  );
}
