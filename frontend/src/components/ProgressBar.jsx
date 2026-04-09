import React from 'react';

export default function ProgressBar({ currentStage, forcedStage, completedStages }) {
  const stages = [
    { key: 'thinking', label: 'tư duy' },
    { key: 'purpose', label: 'mục đích' },
    { key: 'goals', label: 'mục tiêu' },
    { key: 'job', label: 'công việc' },
    { key: 'major', label: 'chuyên ngành' },
    { key: 'uni', label: 'đại học' },
  ];

  return (
    <div className="mb-8 w-full">
      <div className="mb-4 flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-label">TIẾN ĐỘ</span>
        <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-accent-amber">
          GIAI ĐOẠN {(stages.find(s => s.key === currentStage)?.label ?? currentStage ?? '').toUpperCase()}
        </span>
      </div>

      <div className="relative flex justify-between px-[5px]">
        <div className="absolute left-[37px] right-[37px] top-[10px] z-0 flex">
          {stages.slice(0, -1).map((_, index) => {
            const leftDone = completedStages.includes(stages[index].key);
            const rightDone = completedStages.includes(stages[index + 1].key);
            const isLineLit = leftDone && rightDone;

            return (
              <div key={stages[index + 1].key} className={`h-px flex-1 ${isLineLit ? 'bg-accent-purple' : 'bg-subtle'}`} />
            );
          })}
        </div>

        {stages.map((stage) => {
          const isDone = completedStages.includes(stage.key);
          const isCurrent = currentStage === stage.key;
          const isForced = forcedStage === stage.key;
          const isLit = isCurrent || isForced;

          return (
            <div key={stage.key} className="relative z-10 flex w-16 flex-col items-center">
              <div
                className={`mt-[4px] h-3 w-3 rounded-full ${
                  isDone
                    ? 'border-2 border-accent-purple bg-accent-purple'
                    : isLit
                      ? 'border-2 border-accent-purple bg-base ring-[3px] ring-accent-purple/25'
                      : 'border-2 border-muted-line bg-base'
                }`}
              />
              <span
                className={`mt-2 text-center font-mono text-[10px] uppercase tracking-[0.15em] ${
                  isLit
                    ? 'font-semibold text-text-pri'
                    : isDone
                      ? 'text-text-sec'
                      : 'text-text-muted'
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
