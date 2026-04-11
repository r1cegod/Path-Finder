import { useState } from 'react';
import { DEBUG_FIXTURES, createForcedStageFinishFixture, createForcedStageFixture } from '../../data/debugFixtures';

const STAGES = ['thinking', 'purpose', 'goals', 'job', 'major', 'uni'];

export default function DebugTab({ sessionId }) {
  const [status, setStatus] = useState('');
  const fixtureNames = Object.keys(DEBUG_FIXTURES);

  async function runDebugAction(label, action) {
    setStatus(`${label}...`);
    try {
      const result = await action();
      setStatus(`${label} ok${result?.trace_count != null ? ` (${result.trace_count} traces)` : ''}`);
    } catch (error) {
      setStatus(error instanceof Error ? `${label} failed: ${error.message}` : `${label} failed`);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="rounded-lg border border-subtle bg-surface p-4">
        <div className="mb-2 font-mono text-[10px] uppercase tracking-[0.15em] text-text-muted">
          DEV SESSION
        </div>
        <div className="break-all font-mono text-[12px] text-text-sec">{sessionId}</div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          className="rounded-lg border border-subtle bg-elevated px-4 py-3 text-left text-[12px] text-text-sec hover:text-text-pri"
          onClick={() => runDebugAction('start trace', () => window.__PF_DEBUG__.startTrace())}
        >
          START TRACE
        </button>
        <button
          type="button"
          className="rounded-lg border border-subtle bg-elevated px-4 py-3 text-left text-[12px] text-text-sec hover:text-text-pri"
          onClick={() => runDebugAction('stop trace', () => window.__PF_DEBUG__.stopTrace())}
        >
          STOP TRACE
        </button>
      </div>

      <div>
        <div className="mb-3 font-mono text-[10px] uppercase tracking-[0.15em] text-text-muted">
          STATE FIXTURES
        </div>
        <div className="grid grid-cols-2 gap-3">
          {fixtureNames.map((name) => (
            <button
              key={name}
              type="button"
              className="rounded-lg border border-subtle bg-elevated px-4 py-3 text-left font-mono text-[11px] text-text-sec hover:text-text-pri"
              onClick={() => runDebugAction(name, () => window.__PF_DEBUG__.applyFixture(name, { backend: false }))}
            >
              {name}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="mb-3 font-mono text-[10px] uppercase tracking-[0.15em] text-text-muted">
          FORCED STAGE CASE
        </div>
        <div className="grid grid-cols-3 gap-3">
          {STAGES.map((stage) => (
            <button
              key={`force-${stage}`}
              type="button"
              className="rounded-lg border border-accent-amber/30 bg-elevated px-3 py-3 text-left font-mono text-[10px] uppercase text-text-sec hover:text-text-pri"
              onClick={() => runDebugAction(`force ${stage}`, () => window.__PF_DEBUG__.applyDynamicFixture(createForcedStageFixture(stage), { backend: false }))}
            >
              force {stage}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="mb-3 font-mono text-[10px] uppercase tracking-[0.15em] text-text-muted">
          FORCED STAGE FINISH
        </div>
        <div className="grid grid-cols-3 gap-3">
          {STAGES.map((stage) => (
            <button
              key={`finish-${stage}`}
              type="button"
              className="rounded-lg border border-accent-green/30 bg-elevated px-3 py-3 text-left font-mono text-[10px] uppercase text-text-sec hover:text-text-pri"
              onClick={() => runDebugAction(`finish ${stage}`, () => window.__PF_DEBUG__.applyDynamicFixture(createForcedStageFinishFixture(stage), { backend: false }))}
            >
              finish {stage}
            </button>
          ))}
        </div>
      </div>

      {status && (
        <div className="rounded-lg border border-subtle bg-base px-4 py-3 font-mono text-[11px] text-text-muted">
          {status}
        </div>
      )}
    </div>
  );
}
