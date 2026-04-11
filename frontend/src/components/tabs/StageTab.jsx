import React from 'react';

const SkeletonBlock = ({ className }) => (
  <div className={`shimmer ${className}`} />
);

const getConfidenceColor = (val) => {
  if (val >= 0.8) return 'bg-[#10B981]';
  if (val >= 0.5) return 'bg-[#F59E0B]';
  return 'bg-[#EF4444]';
};

const StageCard = ({ title, stageKey, status, fields, twoColumn }) => {
  const isComplete = status === 'complete';
  const isActive = status === 'active';
  const isPending = status === 'pending';

  return (
    <div
      data-stage-card={stageKey ?? title}
      data-stage-status={status}
      className={`bg-surface border rounded-lg p-4 flex flex-col gap-3 ${
        isComplete ? 'border-subtle' : 
        isActive ? 'border-accent-purple/60 shadow-[0_0_0_1px_rgba(124,58,237,0.2)]' : 
        'border-subtle'
      }`}
    >
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <div 
            className={`w-2 h-2 rounded-full ${
              isComplete ? 'bg-accent-purple' : 
              isActive ? 'bg-accent-purple shadow-[0_0_0_3px_rgba(124,58,237,0.25)]' : 
              'bg-base border border-muted-line'
            }`} 
          />
          <span className="text-[11px] uppercase tracking-widest text-text-pri font-semibold">
            {title}
          </span>
        </div>
        <span 
          className={`text-[10px] uppercase tracking-wider font-mono ${
            isComplete ? 'text-text-muted' : 
            isActive ? 'text-accent-amber' : 
            'text-text-muted'
          }`}
        >
          {isComplete ? 'XONG' : isActive ? 'ĐANG LÀM' : 'CHỜ'}
        </span>
      </div>

      <div className={twoColumn ? "grid grid-cols-2 gap-x-8 gap-y-2" : "space-y-2"}>
        {fields.map((field, idx) => {
          const isEmpty = !field.value;
          const isLastInCol = twoColumn ? idx >= fields.length - 2 : idx === fields.length - 1;
          
          return (
            <div 
              key={field.label || idx} 
              className={`flex ${field.label === 'TRÍCH DẪN' ? 'items-start' : 'items-center'} gap-3 ${!isLastInCol && !twoColumn ? 'border-b border-subtle pb-1.5' : ''}`}
            >
              {field.label && (
                <span className={`w-28 text-[9px] uppercase tracking-wider text-text-muted truncate ${field.label === 'TRÍCH DẪN' ? 'pt-1' : ''}`}>
                  {field.label}
                </span>
              )}
              
              {isEmpty ? (
                <>
                  <span className="flex-1" />
                  <div className="flex items-center gap-2 w-28 flex-shrink-0">
                    <div className="w-12 h-[3px] bg-subtle rounded-full overflow-hidden">
                      <div className="h-full bg-subtle" style={{ width: '0%' }} />
                    </div>
                    <span className="text-[9px] font-mono text-text-muted ml-1.5">
                      0.00
                    </span>
                  </div>
                </>
              ) : (
                <>
                  {field.label === 'TRÍCH DẪN' ? (
                    <div className="flex-1 flex flex-col gap-0.5">
                      <span className="text-[13px] text-text-sec italic leading-tight line-clamp-2">
                        "{field.value}"
                      </span>
                      <div className="flex items-center gap-2 w-28 mt-1">
                        <div className="w-12 h-[3px] bg-subtle rounded-full overflow-hidden">
                          <div className={`h-full ${getConfidenceColor(field.confidence)}`} style={{ width: `${field.confidence * 100}%` }} />
                        </div>
                        <span className="text-[9px] font-mono text-text-muted ml-1.5">
                          {field.confidence.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <>
                      <span className="flex-1 text-[13px] text-text-sec truncate">
                        {field.value}
                      </span>
                      <div className="flex items-center gap-2 w-28 flex-shrink-0">
                        <div className="w-12 h-[3px] bg-subtle rounded-full overflow-hidden">
                          <div className={`h-full ${getConfidenceColor(field.confidence)}`} style={{ width: `${field.confidence * 100}%` }} />
                        </div>
                        <span className="text-[9px] font-mono text-text-muted ml-1.5">
                          {field.confidence.toFixed(2)}
                        </span>
                      </div>
                    </>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default function StageTab({ appState }) {
  const getStatus = (stageName) => {
    if (appState.forcedStage) {
      if (appState.forcedStage === stageName) return 'active';
      if (appState.completedStages?.includes(stageName)) return 'complete';
      return 'pending';
    }
    if (appState.completedStages?.includes(stageName)) return 'complete';
    if (appState.currentStage === stageName) return 'active';
    return 'pending';
  };

  const thinkingFields = [
    { label: 'PHƯƠNG PHÁP',   value: appState.thinking?.learning_mode?.content,    confidence: appState.thinking?.learning_mode?.confidence    ?? 0 },
    { label: 'MÔI TRƯỜNG',   value: appState.thinking?.env_constraint?.content,   confidence: appState.thinking?.env_constraint?.confidence   ?? 0 },
    { label: 'XÃ HỘI',       value: appState.thinking?.social_battery?.content,   confidence: appState.thinking?.social_battery?.confidence   ?? 0 },
    { label: 'TÍNH CÁCH',    value: appState.thinking?.personality_type?.content, confidence: appState.thinking?.personality_type?.confidence ?? 0 },
  ];

  const jobFields = [
    { label: 'LOẠI VAI TRÒ',  value: appState.job?.role_category?.content,  confidence: appState.job?.role_category?.confidence  ?? 0 },
    { label: 'GĐ CÔNG TY',   value: appState.job?.company_stage?.content,  confidence: appState.job?.company_stage?.confidence  ?? 0 },
    { label: 'HÀNG NGÀY',    value: appState.job?.day_to_day?.content,     confidence: appState.job?.day_to_day?.confidence     ?? 0 },
    { label: 'MỨC TỰ CHỦ',  value: appState.job?.autonomy_level?.content, confidence: appState.job?.autonomy_level?.confidence ?? 0 },
  ];

  const purposeFields = [
    { label: 'CỐT LÕI',      value: appState.purpose?.core_desire?.content,       confidence: appState.purpose?.core_desire?.confidence       ?? 0 },
    { label: 'QH CÔNG VIỆC', value: appState.purpose?.work_relationship?.content, confidence: appState.purpose?.work_relationship?.confidence ?? 0 },
    { label: 'QUAN ĐIỂM AI', value: appState.purpose?.ai_stance?.content,         confidence: appState.purpose?.ai_stance?.confidence         ?? 0 },
    { label: 'VỊ TRÍ',       value: appState.purpose?.location_vision?.content,   confidence: appState.purpose?.location_vision?.confidence   ?? 0 },
    { label: 'TRIẾT LÝ RR',  value: appState.purpose?.risk_philosophy?.content,   confidence: appState.purpose?.risk_philosophy?.confidence   ?? 0 },
    { label: 'TRÍCH DẪN',    value: appState.purpose?.key_quote?.content,         confidence: appState.purpose?.key_quote?.confidence         ?? 0 },
  ];

  const goalsFields = [
    { label: 'THU NHẬP',    value: appState.goals?.long?.income_target?.content,    confidence: appState.goals?.long?.income_target?.confidence    ?? 0 },
    { label: 'MỨC TỰ CHỦ', value: appState.goals?.long?.autonomy_level?.content,   confidence: appState.goals?.long?.autonomy_level?.confidence   ?? 0 },
    { label: 'SỞ HỮU',     value: appState.goals?.long?.ownership_model?.content,  confidence: appState.goals?.long?.ownership_model?.confidence  ?? 0 },
    { label: 'QUY MÔ ĐỘI', value: appState.goals?.long?.team_size?.content,        confidence: appState.goals?.long?.team_size?.confidence        ?? 0 },
    { label: 'KỸ NĂNG',    value: appState.goals?.short?.skill_targets?.content,   confidence: appState.goals?.short?.skill_targets?.confidence   ?? 0 },
    { label: 'HỒ SƠ',      value: appState.goals?.short?.portfolio_goal?.content,  confidence: appState.goals?.short?.portfolio_goal?.confidence  ?? 0 },
    { label: 'BẰNG CẤP',   value: appState.goals?.short?.credential_needed?.content, confidence: appState.goals?.short?.credential_needed?.confidence ?? 0 },
  ];

  const majorFields = [
    { label: 'LĨNH VỰC',       value: appState.major?.field?.content,                    confidence: appState.major?.field?.confidence                    ?? 0 },
    { label: 'PHONG CÁCH CT',  value: appState.major?.curriculum_style?.content,         confidence: appState.major?.curriculum_style?.confidence         ?? 0 },
    { label: 'ĐỘ PHỦ KN',     value: appState.major?.required_skills_coverage?.content, confidence: appState.major?.required_skills_coverage?.confidence ?? 0 },
  ];

  const uniFields = [
    { label: 'TRƯỜNG', value: appState.uni?.target_school?.content, confidence: appState.uni?.target_school?.confidence ?? 0 },
    { label: 'UY TÍN', value: appState.uni?.prestige_requirement?.content, confidence: appState.uni?.prestige_requirement?.confidence ?? 0 },
    { label: 'HÌNH THỨC', value: appState.uni?.campus_format?.content, confidence: appState.uni?.campus_format?.confidence ?? 0 },
  ];

  return (
    <div className="grid grid-cols-2 gap-3">
      <StageCard title="TƯ DUY" status={getStatus('thinking')} fields={thinkingFields} twoColumn={false} />
      <StageCard title="CÔNG VIỆC" status={getStatus('job')} fields={jobFields} twoColumn={false} />
      <div className="col-span-2">
        <StageCard title="MỤC ĐÍCH" status={getStatus('purpose')} fields={purposeFields} twoColumn={true} />
      </div>
      <div className="col-span-2">
        <StageCard title="MỤC TIÊU" status={getStatus('goals')} fields={goalsFields} twoColumn={true} />
      </div>
      <StageCard title="CHUYÊN NGÀNH" status={getStatus('major')} fields={majorFields} twoColumn={false} />
      <StageCard title="ĐẠI HỌC" status={getStatus('uni')} fields={uniFields} twoColumn={false} />
    </div>
  );
}
