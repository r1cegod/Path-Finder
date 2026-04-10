import SkeletonBlock from '../shared/SkeletonBlock';
import ConfidenceBar from '../shared/ConfidenceBar';
import Card from '../shared/Card';
import { AlertTriangle } from 'lucide-react';

export default function ProfileTab({ appState }) {
  const { turn_count, purpose, thinking, job, goals, user_tag } = appState;

  return (
    <div className="flex flex-col gap-4">
      {/* HERO BLOCK */}
      <div className="bg-elevated border border-subtle rounded-lg px-5 py-4">
        <div className="flex justify-between items-center mb-3">
          <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-muted">← TRÍCH DẪN CHÍNH</span>
          <span className="font-mono text-[10px] text-text-muted tracking-[0.05em]">
            LƯỢT {turn_count.toString().padStart(2, '0')}
          </span>
        </div>
        <div className="font-sans text-[14px] text-text-sec italic leading-[1.6]">
          {purpose?.key_quote?.content ? (
            purpose.key_quote.content
          ) : (
            <SkeletonBlock className="h-10 w-full" />
          )}
        </div>
      </div>

      {/* CARD 1 — IDENTITY */}
      <Card title="BẢN SẮC">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-label mb-1">KHAO KHÁT CỐT LÕI</div>
            {purpose?.core_desire?.content ? (
              <div className="font-sans text-[20px] font-bold text-text-pri">
                {purpose.core_desire.content}
              </div>
            ) : (
              <SkeletonBlock className="h-7 w-48" />
            )}
          </div>
          <div className="flex flex-col items-end">
            <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-label mb-2 text-right">ĐỘ TỰ TIN</div>
            {purpose?.core_desire?.confidence != null ? (
              <div className="w-24">
                <ConfidenceBar value={purpose.core_desire.confidence} />
              </div>
            ) : (
              <SkeletonBlock className="h-4 w-24" />
            )}
          </div>
        </div>
        <div className="flex gap-2 flex-wrap">
          {thinking ? (
            <>
              {thinking.personality_type?.content && (
                <div className="border border-subtle bg-elevated rounded px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-text-sec">
                  {thinking.personality_type.content}
                </div>
              )}
              {thinking.learning_mode?.content && (
                <div className="border border-subtle bg-elevated rounded px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-text-sec">
                  {thinking.learning_mode.content}
                </div>
              )}
              {thinking.social_battery?.content && (
                <div className="border border-subtle bg-elevated rounded px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-text-sec">
                  {thinking.social_battery.content}
                </div>
              )}
            </>
          ) : (
            <>
              <SkeletonBlock className="h-6 w-20 rounded" />
              <SkeletonBlock className="h-6 w-20 rounded" />
              <SkeletonBlock className="h-6 w-20 rounded" />
            </>
          )}
        </div>
      </Card>

      {/* CARD 2 — TRAJECTORY */}
      <Card title="QUỸ ĐẠO">
        <div className="flex justify-between items-start mb-4">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-label mb-1">VAI TRÒ</div>
            {job?.role_category?.content ? (
              <div className="font-sans text-[24px] font-bold text-text-pri uppercase">
                {job.role_category.content}
              </div>
            ) : (
              <SkeletonBlock className="h-8 w-32" />
            )}
          </div>
          <div className="text-right">
            <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-label mb-1">GIAI ĐOẠN CÔNG TY</div>
            {job?.company_stage?.content ? (
              <div className="font-sans text-[24px] font-bold text-text-pri uppercase">
                {job.company_stage.content}
              </div>
            ) : (
              <SkeletonBlock className="h-8 w-32" />
            )}
          </div>
        </div>

        <div className="border-t border-subtle my-4" />

        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-label mb-1">MỤC TIÊU THU NHẬP</div>
            {goals?.long?.income_target?.content ? (
              <div className="font-sans text-[14px] text-text-sec">{goals.long.income_target.content}</div>
            ) : (
              <SkeletonBlock className="h-5 w-full" />
            )}
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-label mb-1">QUYỀN TỰ CHỦ</div>
            {goals?.long?.autonomy_level?.content ? (
              <div className="font-sans text-[14px] text-text-sec">{goals.long.autonomy_level.content}</div>
            ) : (
              <SkeletonBlock className="h-5 w-full" />
            )}
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-label mb-1">MÔ HÌNH SỞ HỮU</div>
            {goals?.long?.ownership_model?.content ? (
              <div className="font-sans text-[14px] text-text-sec">{goals.long.ownership_model.content}</div>
            ) : (
              <SkeletonBlock className="h-5 w-full" />
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-label">QUAN ĐIỂM VỀ AI</span>
          {purpose?.ai_stance?.content ? (
            <div className={`border border-subtle bg-elevated rounded px-3 py-1 font-mono text-[11px] uppercase tracking-wider ${purpose.ai_stance.content === 'leverage' ? 'text-accent-green' : 'text-text-sec'}`}>
              {purpose.ai_stance.content}
            </div>
          ) : (
            <SkeletonBlock className="h-6 w-20 rounded" />
          )}
        </div>
      </Card>

      {/* CARD 3 — ALERTS */}
      <Card title="CẢNH BÁO">
        {(!user_tag || (!user_tag.parental_pressure && !user_tag.core_tension && !user_tag.burnout_risk)) ? (
          <div className="text-[12px] italic text-text-muted">Không phát hiện cờ cảnh báo</div>
        ) : (
          <div className="flex flex-col">
            {[
              { id: 'parental_pressure', label: 'ÁP LỰC GIA ĐÌNH', active: user_tag.parental_pressure, reasoning: user_tag.parental_pressure_reasoning, color: 'text-accent-amber' },
              { id: 'core_tension', label: 'CĂNG THẲNG CỐT LÕI', active: user_tag.core_tension, reasoning: user_tag.core_tension_reasoning, color: 'text-accent-amber' },
              { id: 'burnout_risk', label: 'NGUY CƠ KIỆT SỨC', active: user_tag.burnout_risk, reasoning: user_tag.burnout_risk_reasoning, color: 'text-accent-red' }
            ].filter(flag => flag.active).map((flag, index, arr) => (
              <div key={flag.id} className={`flex items-start gap-3 py-2 ${index < arr.length - 1 ? 'border-b border-subtle' : ''}`}>
                <AlertTriangle className={`w-[14px] h-[14px] mt-0.5 ${flag.color}`} />
                <div>
                  <div className={`text-[12px] uppercase tracking-wide font-semibold ${flag.color}`}>
                    {flag.label}
                  </div>
                  <div className="text-[12px] italic text-text-sec mt-0.5">
                    {flag.reasoning}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
