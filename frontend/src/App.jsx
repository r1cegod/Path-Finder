import { useEffect, useState } from 'react';
import Shell from './components/Shell';
import NeuralInterface from './components/chat/NeuralInterface';
import { DEFAULT_APP_STATE, INITIAL_MESSAGES } from './data/mockState';
import { sendMessage } from './api/chat';
import { getBackendState, patchBackendState, startTrace, stopTrace } from './api/debug';
import { DEBUG_FIXTURES, createForcedStageFinishFixture, createForcedStageFixture } from './data/debugFixtures';

function deepMerge(base, patch) {
  if (!patch || typeof patch !== 'object' || Array.isArray(patch)) return patch;
  const merged = { ...(base ?? {}) };
  Object.entries(patch).forEach(([key, value]) => {
    if (value && typeof value === 'object' && !Array.isArray(value) && !(value instanceof Date)) {
      merged[key] = deepMerge(merged[key], value);
    } else {
      merged[key] = value;
    }
  });
  return merged;
}

export default function App() {
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID());
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
      if (newState.testStatus) {
        merged.testStatus = {
          ...(prev.testStatus ?? {}),
          ...newState.testStatus,
          miSubmitted: Boolean(prev.testStatus?.miSubmitted || newState.testStatus.miSubmitted),
          riasecSubmitted: Boolean(prev.testStatus?.riasecSubmitted || newState.testStatus.riasecSubmitted),
        };
      }
      return merged;
    });
  }

  function patchAppState(patch) {
    setAppState(prev => deepMerge(prev, patch));
  }

  function replaceSession(nextSessionId = crypto.randomUUID()) {
    setSessionId(nextSessionId);
    setMessages(INITIAL_MESSAGES);
    setAppState(DEFAULT_APP_STATE);
    return nextSessionId;
  }

  async function applyFixture(name, options = {}) {
    const fixture = DEBUG_FIXTURES[name];
    if (!fixture) {
      throw new Error(`Unknown debug fixture: ${name}`);
    }

    return applyDynamicFixture(fixture, options);
  }

  async function applyDynamicFixture(fixture, options = {}) {
    if (fixture.appState) setAppState(deepMerge(DEFAULT_APP_STATE, fixture.appState));
    if (fixture.messages) setMessages(fixture.messages);
    if (fixture.backendPatch && options.backend !== false) {
      const result = await patchBackendState(sessionId, fixture.backendPatch);
      if (result.frontendState) mergeState(result.frontendState);
      return result;
    }
    return { appState: fixture.appState ?? appState };
  }

  function forceStage(stageName, options = {}) {
    return applyDynamicFixture(createForcedStageFixture(stageName), options);
  }

  function finishForcedStage(stageName, options = {}) {
    return applyDynamicFixture(createForcedStageFinishFixture(stageName), options);
  }

  useEffect(() => {
    if (!import.meta.env.DEV) return undefined;

    window.__PF_DEBUG__ = {
      fixtures: Object.keys(DEBUG_FIXTURES),
      getSessionId: () => sessionId,
      getAppState: () => appState,
      getMessages: () => messages,
      patchAppState,
      setMessages,
      newSession: replaceSession,
      applyFixture,
      applyDynamicFixture,
      forceStage,
      finishForcedStage,
      startTrace: () => startTrace(sessionId),
      stopTrace: () => stopTrace(sessionId),
      getBackendState: () => getBackendState(sessionId),
      patchBackendState: async (patch) => {
        const result = await patchBackendState(sessionId, patch);
        if (result.frontendState) mergeState(result.frontendState);
        return result;
      },
    };

    return () => {
      if (window.__PF_DEBUG__?.getSessionId?.() === sessionId) {
        delete window.__PF_DEBUG__;
      }
    };
  }, [sessionId, appState, messages]);

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
    } catch (error) {
      const fallback = error instanceof Error
        ? `Hệ thống gặp lỗi khi xử lý tin nhắn. ${error.message}`
        : 'Hệ thống gặp lỗi khi xử lý tin nhắn.';

      setMessages(m => m.map(msg => {
        if (msg.id !== asstId) return msg;

        const content = msg.content
          ? `${msg.content}\n\n${fallback}`
          : fallback;

        return { ...msg, content, isError: true };
      }));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex h-dvh min-h-dvh w-full flex-col overflow-hidden bg-base md:flex-row">
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
