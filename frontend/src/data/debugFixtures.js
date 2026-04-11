const STAGES = ['thinking', 'purpose', 'goals', 'job', 'major', 'uni'];
const BACKEND_STAGE = { thinking: 'thinking', purpose: 'purpose', goals: 'goals', job: 'job', major: 'major', uni: 'university' };

const field = (content, confidence = 0.86) => ({ content, confidence });

const thinking = {
  done: true,
  learning_mode: field('hands-on'),
  env_constraint: field('campus'),
  social_battery: field('small-team'),
  personality_type: field('builder'),
  brain_type: ['logical', 'kinesthetic'],
  riasec_top: ['I', 'R'],
  riasec_scores: [],
};

const purpose = {
  done: true,
  core_desire: field('build useful tools with independence'),
  work_relationship: field('calling'),
  ai_stance: field('leverage'),
  location_vision: field('Vietnam first, global later'),
  risk_philosophy: field('calculated startup risk'),
  key_quote: field('I want proof that my work can stand on its own.'),
};

const goals = {
  done: true,
  long: {
    done: true,
    income_target: field('5000 USD/month by late twenties'),
    autonomy_level: field('high autonomy'),
    ownership_model: field('founder'),
    team_size: field('small team'),
  },
  short: {
    done: true,
    skill_targets: field('backend systems, AI agents, product shipping'),
    portfolio_goal: field('one deployed product with real users'),
    credential_needed: field('software engineering degree plus portfolio'),
  },
};

const job = {
  done: true,
  role_category: field('AI product engineer'),
  company_stage: field('startup'),
  day_to_day: field('build, test, deploy, talk to users'),
  autonomy_level: field('managed freedom'),
};

const major = {
  done: true,
  field: field('Software Engineering'),
  curriculum_style: field('project-based'),
  required_skills_coverage: field('covers fundamentals, portfolio fills gaps'),
};

const uni = {
  done: true,
  prestige_requirement: field('credible local program'),
  target_school: field('FPT University'),
  campus_format: field('domestic'),
  is_domestic: true,
};

const userTagAlerts = {
  parental_pressure: true,
  parental_pressure_reasoning: 'Family preference is strongly shaping the stated choice.',
  burnout_risk: true,
  burnout_risk_reasoning: 'Student describes chronic overload and low rest.',
  urgency: false,
  urgency_reasoning: '',
  core_tension: true,
  core_tension_reasoning: 'Independence goal conflicts with safe approval-seeking.',
  self_authorship: 'Student has some personal voice but still defaults to external validation.',
  reality_gap: true,
  reality_gap_reasoning: 'Ambition is ahead of current proof and needs a concrete artifact plan.',
  compliance_reasoning: '',
  disengagement_reasoning: '',
  avoidance_reasoning: '',
  vague_reasoning: '',
};

const longMessage = 'This is a deliberately long assistant message for overflow testing. '.repeat(24);

const baseState = {
  currentStage: 'thinking',
  forcedStage: '',
  completedStages: [],
  turn_count: 0,
  thinking: null,
  purpose: null,
  goals: null,
  job: null,
  major: null,
  uni: null,
  user_tag: null,
  escalationPending: false,
};

const profiles = { thinking, purpose, goals, job, major, uni };

const completedBefore = (stageName) => STAGES.filter(
  (stage) => STAGES.indexOf(stage) < STAGES.indexOf(stageName),
);

const backendProfilesThrough = (stageName, doneOverride = {}) => {
  const patch = {};
  STAGES.slice(0, STAGES.indexOf(stageName) + 1).forEach((stage) => {
    const profile = {
      ...profiles[stage],
      ...(doneOverride[stage] ?? {}),
    };
    patch[stage === 'uni' ? 'university' : stage] = profile;
  });
  return patch;
};

const stageState = (stageName) => ({
  ...baseState,
  currentStage: stageName,
  completedStages: completedBefore(stageName),
  thinking: stageName === 'thinking' ? { ...thinking, done: false } : thinking,
  purpose: ['goals', 'job', 'major', 'uni'].includes(stageName) ? purpose : null,
  goals: ['job', 'major', 'uni'].includes(stageName) ? goals : null,
  job: ['major', 'uni'].includes(stageName) ? job : null,
  major: stageName === 'uni' ? major : null,
  uni: null,
});

export function createForcedStageFixture(stageName) {
  if (!STAGES.includes(stageName)) throw new Error(`Unknown stage: ${stageName}`);
  return {
    appState: {
      ...stageState('thinking'),
      forcedStage: stageName,
      completedStages: [],
      thinking: { ...thinking, done: false },
    },
    backendPatch: {
      stage: {
        current_stage: 'thinking',
        anchor_stage: BACKEND_STAGE[stageName],
        anchor_mode: 'forced',
        stage_related: [BACKEND_STAGE[stageName]],
        requested_anchor_stage: '',
        contradict: false,
        contradict_target: [],
      },
      ...backendProfilesThrough(stageName, {
        [stageName]: { done: false },
      }),
    },
  };
}

export function createForcedStageFinishFixture(stageName) {
  if (!STAGES.includes(stageName)) throw new Error(`Unknown stage: ${stageName}`);
  const nextStage = STAGES[STAGES.indexOf(stageName) + 1] ?? stageName;
  return {
    appState: {
      ...baseState,
      currentStage: nextStage,
      forcedStage: '',
      completedStages: STAGES.slice(0, STAGES.indexOf(stageName) + 1),
      thinking,
      purpose: STAGES.indexOf(stageName) >= STAGES.indexOf('purpose') ? purpose : null,
      goals: STAGES.indexOf(stageName) >= STAGES.indexOf('goals') ? goals : null,
      job: STAGES.indexOf(stageName) >= STAGES.indexOf('job') ? job : null,
      major: STAGES.indexOf(stageName) >= STAGES.indexOf('major') ? major : null,
      uni: STAGES.indexOf(stageName) >= STAGES.indexOf('uni') ? uni : null,
    },
    backendPatch: {
      stage: {
        current_stage: BACKEND_STAGE[nextStage],
        anchor_stage: BACKEND_STAGE[nextStage],
        anchor_mode: 'normal',
        stage_related: [BACKEND_STAGE[nextStage]],
        requested_anchor_stage: '',
        contradict: false,
        contradict_target: [],
      },
      ...backendProfilesThrough(stageName),
      stage_transitioned: nextStage !== stageName,
    },
  };
}

export const DEBUG_FIXTURES = {
  empty: {
    appState: baseState,
    messages: [],
    backendPatch: {},
  },
  quizSeeded: {
    appState: {
      ...baseState,
      thinking: {
        ...thinking,
        done: false,
        learning_mode: field('', 0),
        env_constraint: field('', 0),
        social_battery: field('', 0),
        personality_type: field('', 0),
      },
    },
    backendPatch: {
      thinking: {
        ...thinking,
        done: false,
        learning_mode: field('', 0),
        env_constraint: field('', 0),
        social_battery: field('', 0),
        personality_type: field('', 0),
      },
    },
  },
  activeThinking: { appState: stageState('thinking') },
  activePurpose: { appState: stageState('purpose') },
  activeGoals: { appState: stageState('goals') },
  activeJob: { appState: stageState('job') },
  activeMajor: { appState: stageState('major') },
  activeUni: { appState: stageState('uni') },
  allComplete: {
    appState: {
      ...baseState,
      currentStage: 'uni',
      completedStages: ['thinking', 'purpose', 'goals', 'job', 'major', 'uni'],
      turn_count: 18,
      thinking,
      purpose,
      goals,
      job,
      major,
      uni,
    },
  },
  pathDebateReady: {
    appState: {
      ...baseState,
      currentStage: 'uni',
      completedStages: ['thinking', 'purpose', 'goals', 'job', 'major', 'uni'],
      turn_count: 20,
      thinking,
      purpose,
      goals,
      job,
      major,
      uni,
    },
    backendPatch: {
      stage: { current_stage: 'university', anchor_stage: 'university', anchor_mode: 'normal' },
      thinking,
      purpose,
      goals,
      job,
      major,
      university: uni,
      path_debate_ready: true,
      bypass_stage: true,
    },
  },
  userTagAlerts: {
    appState: {
      ...stageState('purpose'),
      user_tag: userTagAlerts,
    },
    backendPatch: {
      user_tag: userTagAlerts,
    },
  },
  escalationLock: {
    appState: {
      ...stageState('purpose'),
      escalationPending: true,
    },
    backendPatch: {
      escalation_pending: true,
      escalation_reason: 'debug: forced escalation lock fixture',
    },
  },
  longText: {
    appState: {
      ...stageState('major'),
      major: {
        ...major,
        required_skills_coverage: field('A very long field value for layout overflow checks. '.repeat(8)),
      },
    },
    messages: [
      { id: 'debug-user-long', role: 'user', content: 'Stress the chat layout with a long message.', timestamp: new Date() },
      { id: 'debug-assistant-long', role: 'assistant', content: longMessage, timestamp: new Date() },
    ],
  },
};
