import { User, LayoutList, FlaskConical, Radio } from 'lucide-react';
import ProgressBar from './ProgressBar';
import ProfileTab from './tabs/ProfileTab';
import StageTab from './tabs/StageTab';
import TestTab from './tabs/TestTab';

export default function Shell({ activeTab, setActiveTab, appState, sessionId, onStateUpdate }) {
  return (
    <div className="flex-1 flex flex-col h-screen mr-[340px]">
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

      <div className="flex flex-1 overflow-hidden">
        {/* LEFT SIDEBAR */}
        <div className="w-16 bg-base border-r border-subtle flex flex-col items-center py-4 gap-6 flex-shrink-0">
          
          <div 
            onClick={() => setActiveTab('profile')}
            className={`p-2 rounded-lg cursor-pointer ${activeTab === 'profile' ? 'bg-elevated text-text-pri' : 'text-text-muted hover:text-text-sec'}`}
          >
            <User className="w-4 h-4" />
          </div>
          
          <div 
            onClick={() => setActiveTab('stage')}
            className={`p-2 rounded-lg cursor-pointer ${activeTab === 'stage' ? 'bg-elevated text-text-pri' : 'text-text-muted hover:text-text-sec'}`}
          >
            <LayoutList className="w-4 h-4" />
          </div>
          
          <div 
            onClick={() => setActiveTab('test')}
            className={`p-2 rounded-lg cursor-pointer ${activeTab === 'test' ? 'bg-elevated text-text-pri' : 'text-text-muted hover:text-text-sec'}`}
          >
            <FlaskConical className="w-4 h-4" />
          </div>
        </div>

        {/* MAIN CONTENT */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col">
          <ProgressBar currentStage={appState.currentStage} completedStages={appState.completedStages} />
          
          <div className="flex-1">
            {activeTab === 'profile' && <ProfileTab appState={appState} />}
            {activeTab === 'stage' && <StageTab appState={appState} />}
            {activeTab === 'test' && <TestTab sessionId={sessionId} onStateUpdate={onStateUpdate} appState={appState} />}
          </div>
        </div>
      </div>
    </div>
  );
}
