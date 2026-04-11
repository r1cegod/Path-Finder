import { Bug, User, LayoutList, FlaskConical, Radio } from 'lucide-react';
import ProgressBar from './ProgressBar';
import ProfileTab from './tabs/ProfileTab';
import StageTab from './tabs/StageTab';
import TestTab from './tabs/TestTab';
import DebugTab from './tabs/DebugTab';

export default function Shell({ activeTab, setActiveTab, appState, sessionId, onStateUpdate }) {
  const tabs = [
    { key: 'profile', label: 'Profile', icon: User },
    { key: 'stage', label: 'Stage', icon: LayoutList },
    { key: 'test', label: 'Test', icon: FlaskConical },
    ...(import.meta.env.DEV ? [{ key: 'debug', label: 'Debug', icon: Bug }] : []),
  ];

  return (
    <div className="flex min-h-0 flex-1 flex-col md:mr-[340px] md:h-dvh">
      {/* TOPBAR */}
      <div className="h-11 px-4 flex items-center justify-between border-b border-subtle bg-base flex-shrink-0">
        <div className="font-sans text-[13px] font-bold uppercase tracking-[0.2em] text-text-pri">
          PATHFINDER
        </div>
        <div className="border border-subtle rounded px-3 py-1 flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse" />
          <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-sec">HỆ THỐNG ĐANG HOẠT ĐỘNG</span>
          <Radio className="w-[14px] h-[14px] text-text-pri" />
        </div>
      </div>

      <div className="flex min-h-0 flex-1 overflow-hidden">
        {/* LEFT SIDEBAR */}
        <div className="w-16 bg-base border-r border-subtle flex flex-col items-center py-4 gap-6 flex-shrink-0">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              type="button"
              aria-label={label}
              title={label}
              onClick={() => setActiveTab(key)}
              className={`p-2 rounded-lg ${activeTab === key ? 'bg-elevated text-text-pri' : 'text-text-muted hover:text-text-sec'}`}
            >
              <Icon className="w-4 h-4" />
            </button>
          ))}
        </div>

        {/* MAIN CONTENT */}
        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto p-6">
          <ProgressBar
            currentStage={appState.currentStage}
            forcedStage={appState.forcedStage}
            completedStages={appState.completedStages}
          />
          
          <div className="flex-1">
            {activeTab === 'profile' && <ProfileTab appState={appState} />}
            {activeTab === 'stage' && <StageTab appState={appState} />}
            {activeTab === 'test' && <TestTab sessionId={sessionId} onStateUpdate={onStateUpdate} appState={appState} />}
            {activeTab === 'debug' && import.meta.env.DEV && <DebugTab sessionId={sessionId} />}
          </div>
        </div>
      </div>
    </div>
  );
}
