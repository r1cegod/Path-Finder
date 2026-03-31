import React from 'react';

export default function ProgressBar({ currentStage, completedStages }) {
  const stages = [
    { key: 'thinking', label: 'tư duy' },
    { key: 'purpose',  label: 'mục đích' },
    { key: 'goals',    label: 'mục tiêu' },
    { key: 'job',      label: 'công việc' },
    { key: 'major',    label: 'chuyên ngành' },
    { key: 'uni',      label: 'đại học' },
  ];

  return (
    <div className="w-full mb-8">
      <div className="flex justify-between items-center mb-4">
        <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-label">TIẾN ĐỘ</span>
        <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-accent-amber">
          GIAI ĐOẠN {(stages.find(s => s.key === currentStage)?.label ?? currentStage ?? '').toUpperCase()}
        </span>
      </div>
      <div className="relative flex justify-between px-[5px]">
        {/* Lines */}
        <div className="absolute top-[10px] left-[37px] right-[37px] flex z-0">
          {stages.slice(0, -1).map((stage, index) => {
            const isCurrentDone = completedStages.includes(stages[index].key);
            const isNextDone = completedStages.includes(stages[index + 1].key);
            const isNextActive = currentStage === stages[index + 1].key;

            // Đường nối chỉ sáng khi node hiện tại đã xong VÀ node tiếp theo đã xong hoặc đang active
            const isLineLit = isCurrentDone && (isNextDone || isNextActive);

            return (
              <div key={index} className={`h-px flex-1 ${isLineLit ? 'bg-accent-purple' : 'bg-subtle'}`} />
            );
          })}
        </div>

        {/* Orbs and text */}
        {stages.map((stage) => {
          const isDone = completedStages.includes(stage.key);
          const isActive = currentStage === stage.key;

          return (
            <div key={stage.key} className="flex flex-col items-center relative z-10 w-16">
              <div
                className={`w-3 h-3 rounded-full mt-[4px] ${
                  isDone ? 'bg-accent-purple border-2 border-accent-purple' :
                  isActive ? 'bg-base border-2 border-accent-purple ring-[3px] ring-accent-purple/25' :
                  'bg-base border-2 border-muted-line'
                }`}
              />
              <span
                className={`mt-2 font-mono text-[10px] uppercase tracking-[0.15em] text-center ${
                  isActive ? 'text-text-pri font-semibold' :
                  isDone ? 'text-text-sec' :
                  'text-text-muted'
                }`}
              >
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
