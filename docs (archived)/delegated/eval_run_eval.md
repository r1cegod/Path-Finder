# eval/run_eval.py — How To Use

## What It Is

`eval/run_eval.py` is a generic evaluation runner for PathFinder's LangGraph stage agents.
Its job is simple: take a JSONL file of pre-written attack inputs, run each one through a
specified graph, and save the full input/output pair as a JSON trace file on disk.

It does not judge whether a result is correct. That is your job as the evaluator — you read
the trace files and decide whether the agent behaved correctly. The runner's only concern is
executing the graph and capturing everything that happened.

It exists because stage agents are isolated subgraphs — they don't have a live conversation
to test against. The JSONL files simulate what state would look like at the moment the agent
receives control, and the runner injects that state directly into the graph.

---

## The Whole Flow

```
ENTRY POINT: python eval/run_eval.py --mode multi --file eval/goals_attack.jsonl --graph goals
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  SETUP  (runs once)                                                                  │
│                                                                                     │
│  parse_args()         reads --mode, --file, --graph, --workers from CLI             │
│         │                                                                           │
│         ▼                                                                           │
│  resolve_input_file() validates the .jsonl path — must be inside eval/ folder      │
│         │                                                                           │
│         ▼                                                                           │
│  resolve_graph()      "goals" string → GraphSpec object (the graph's ID card)      │
│         │                                                                           │
│         ▼                                                                           │
│  load_jsonl_inputs()  reads file line by line → list of raw Python dicts           │
│         │                                                                           │
│         ▼                                                                           │
│  load_graph()         imports backend.goals_graph at runtime → goals_graph object  │
│                                                                                     │
│  You now have: a live graph object + a list of raw input dicts                     │
└──────────────────────────┬──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  DISPATCH  (decides single or parallel)                                             │
│                                                                                     │
│  mode=single ──► run_single_mode()                                                  │
│                   all inputs share ONE thread_id                                    │
│                   runs input[0] → input[1] → input[2] in order                    │
│                   LangGraph accumulates state across runs (like a real conversation)│
│                                                                                     │
│  mode=multi  ──► run_multi_mode()                                                   │
│                   each input gets its OWN thread_id                                 │
│                   runs all inputs in parallel threads                               │
│                   each run is isolated — no state bleeds between them              │
│                                                                                     │
│  For attack datasets: always use multi. Each attack is independent.                │
│  For conversation replay: use single. Inputs build on each other.                  │
└──────────────────────────┬──────────────────────────────────────────────────────────┘
                           │
                           │  both modes call this per input:
                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  CORE  run_one_input()                                                              │
│                                                                                     │
│  build_state_for_graph()   raw dict from JSONL → valid PathFinderState             │
│         │                                                                           │
│         ▼                                                                           │
│  graph.invoke(state, config)   LangGraph runs the agent, returns final state       │
│         │                                                                           │
│         ▼                                                                           │
│  write_trace()             dumps {input, normalized_input, output, status} to JSON │
│         │                                                                           │
│         ▼                                                                           │
│  RunOutcome(status, trace_path)  returned to dispatch layer                        │
└──────────────────────────┬──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  REPORT                                                                             │
│                                                                                     │
│  per run:   "[0001] ok   thread=abc123  trace=eval/threads/.../run_0001.json"      │
│  summary:   "Success: 4   Failed: 1"                                               │
│  exit code: SystemExit(1) if any failures — so CI tools can detect breaks          │
└─────────────────────────────────────────────────────────────────────────────────────┘

OUTPUT FILES:
  eval/threads/{thread_id}/traces/run_0001.json
                                  run_0002.json
                                  ...
```

---

## Each Feature Flow

### GraphSpec — the graph's ID card

```
GraphSpec is a frozen data container. It answers:
"Given the string 'goals' from the CLI — what exactly do I need to run it?"

┌──────────────────────────────────────────────────────────────────┐
│  GraphSpec                                                        │
│                                                                  │
│  key           = "goals"                ← dict lookup key        │
│  module_path   = "backend.goals_graph"  ← what to import        │
│  graph_attr    = "goals_graph"          ← what attr to grab      │
│  default_queue = "goals_message"        ← which queue gets msgs  │
│  current_stage = "goals"                ← injected into state    │
│                                           None for orchestrator  │
└──────────────────────────────────────────────────────────────────┘

Why current_stage is None for orchestrator:
  Stage agents are passive — they only run if current_stage matches.
  The runner injects current_stage so the agent thinks it's in the right stage.
  The orchestrator owns its own routing — the runner must not interfere.

New Python pattern:
  `@dataclass(frozen=True)` — auto-generates __init__ from class fields.
  frozen=True means the object is immutable after creation (like a tuple with names).
  Used here so no code accidentally mutates a spec mid-run.
```

To add a new graph to eval, add a new entry to `CANONICAL_GRAPHS` (line 52)
following the exact same shape as the existing entries.

---

### resolve_graph() — string → GraphSpec

```
CLI string "goals"
      │
      ▼
GRAPH_ALIASES.get("goals") → "goals"    ← handles "goals_graph", "g", etc.
      │
      ▼
CANONICAL_GRAPHS.get("goals") → GraphSpec(...)

If not found → ValueError listing all supported names
```

To add an alias (e.g. "g" → "goals"), add it to `GRAPH_ALIASES` (line 111).

---

### load_graph() — dynamic import

```
spec.module_path = "backend.goals_graph"
      │
      ▼
importlib.import_module("backend.goals_graph")   ← same as: import backend.goals_graph
      │
      ▼
getattr(module, "goals_graph")   ← same as: module.goals_graph
      │
      ▼
the compiled LangGraph object, ready to invoke

New Python pattern:
  `importlib.import_module(string)` — imports a module from a string at runtime.
  Used here because the graph name comes from the CLI — you can't hardcode the import.

New Python pattern:
  `getattr(obj, "attr_name")` — same as obj.attr_name but the name is a variable.
  Used here because graph_attr is a string from GraphSpec, not a hardcoded name.
```

---

### build_state_for_graph() — the most important function

This is the function you will touch most often. It converts a raw JSONL row into a
PathFinderState that graph.invoke() can actually run.

```
PROBLEM: your JSONL row is a plain dict with raw dicts and string-role messages.
         graph.invoke() needs a full PathFinderState with LangChain message objects.

SOLUTION in 3 steps:

STEP 1 — Fill defaults
───────────────────────
state = copy.deepcopy(DEFAULT_STATE)     ← start from a complete, clean state
for key, value in raw_input.items():     ← overlay only what the JSONL row provides
    state[key] = value

New Python pattern:
  `copy.deepcopy(x)` — creates a completely independent clone of x.
  Any mutation to the clone does NOT affect the original.
  Critical here: without deepcopy, every eval run would mutate the same DEFAULT_STATE
  dict and the second run would start with dirty state from the first run.


STEP 2 — Convert message lists → LangChain objects
────────────────────────────────────────────────────
Raw JSONL:         {"role": "user", "content": "I want money"}
LangChain object:  HumanMessage(content="I want money")

graph.invoke() crashes on plain dicts — it only speaks LangChain message objects.
Every key in QUEUE_KEYS gets this conversion:

  "user"      → HumanMessage(content=...)
  "assistant" → AIMessage(content=...)
  "system"    → SystemMessage(content=...)
  "tool"      → ToolMessage(content=..., tool_call_id=...)

QUEUE_KEYS (line 125) lists every queue that can hold messages:
  messages, thinking_style_message, purpose_message, goals_message,
  job_message, major_message, uni_message

If you add a new stage with a new queue, add its key to QUEUE_KEYS.


STEP 3 — Queue fallback + stage injection
──────────────────────────────────────────
Problem: what if your JSONL row uses "messages" but the graph expects "goals_message"?

  if target queue (goals_message) is missing from input:
      ┌── if "messages" key exists in input ────────────────────────────────────┐
      │   copy messages → goals_message                                         │
      ├── elif only one queue key exists in input ──────────────────────────────┤
      │   copy that queue → goals_message                                       │
      └── else: raise ValueError (no messages found) ───────────────────────────┘

This means you can write attack inputs using just "messages" and run them against
any stage graph without renaming the key in every row.

Stage injection:
  if spec.current_stage is not None:           ← stage graphs only, not orchestrator
      if input didn't already set current_stage:
          state["stage"]["current_stage"] = spec.current_stage
                                              ↑ forces the agent to think it's in goals
```

---

### run_one_input() — invoke + capture

```
Build a trace dict (metadata shell):
  {graph_name, input_file, mode, run_index, thread_id, timestamp, ...}
        │
        ▼
build_state_for_graph() → normalized state
        │
        ▼
graph.invoke(normalized_state, config={"configurable": {"thread_id": thread_id}})
        │                                                    ↑
        │                              LangGraph needs this to track conversation
        │                              Each thread_id = isolated conversation
        ▼
result_state = the full PathFinderState after the agent ran
        │
        ▼
trace["output"] = serialize_value(result_state)   ← convert to JSON-safe format
        │
        ▼
write_trace() → eval/threads/{thread_id}/traces/run_{index}.json

If anything crashes between invoke and write:
  trace["status"] = "error"
  trace["output"] = {error_type, error_message}
  trace["error_traceback"] = full stack trace
  → still writes the trace (so you can debug)
  → RunOutcome.status = "error"
```

---

### serialize_value() — make any Python value JSON-safe

```
Python has types JSON doesn't understand: Pydantic models, Path objects,
LangChain messages, datetime objects.

serialize_value() handles all of them recursively:

  Pydantic model   → .model_dump() → dict → recurse
  LangChain msg    → serialize_message() → {type, content, ...}
  dict             → recurse on every value
  list/tuple/set   → recurse on every item
  Path             → str(path)
  datetime         → .isoformat() string
  None/bool/int/   → pass through unchanged
  float/str

New Python pattern:
  `hasattr(obj, "model_dump")` — checks if an object has a model_dump method.
  Used here to detect Pydantic models without importing every model class.
  If it has model_dump, it's a Pydantic model. Call it and recurse.
```

---

### run_multi_mode() — parallel execution

```
inputs = [row0, row1, row2, row3, row4]   ← 5 attack rows
                │
                ▼
ThreadPoolExecutor(max_workers=5)
  ├── thread 1: run_one_input(row0, thread_id="abc")
  ├── thread 2: run_one_input(row1, thread_id="def")
  ├── thread 3: run_one_input(row2, thread_id="ghi")
  ├── thread 4: run_one_input(row3, thread_id="jkl")
  └── thread 5: run_one_input(row4, thread_id="mno")
                │
                ▼
as_completed(futures)   ← collect results as each thread finishes (not in order)
                │
                ▼
outcomes.sort(key=run_index)   ← re-sort by run index before returning

New Python pattern:
  `ThreadPoolExecutor` — runs functions in parallel using a thread pool.
  `as_completed(futures)` — yields futures in completion order (fastest first).
  Used here so 5 LLM calls run simultaneously instead of waiting one-by-one.
  Result: 5-run eval takes ~same time as 1-run eval.

New Python pattern:
  `uuid4()` — generates a random unique string like "a3f2c1d4-...".
  Each run needs its own thread_id so LangGraph doesn't mix up their state.
```

---

## How To Use

```bash
# activate venv first
source venv/Scripts/activate

# run goals attack dataset (independent attacks, parallel)
python eval/run_eval.py --mode multi --file eval/goals_attack.jsonl --graph goals

# run purpose attack dataset
python eval/run_eval.py --mode multi --file eval/purpose_attack.jsonl --graph purpose

# run a conversation thread (inputs build on each other, sequential)
python eval/run_eval.py --mode single --file eval/thread_1_drifter.jsonl --graph orchestrator

# limit parallel workers (default = min(8, number of inputs))
python eval/run_eval.py --mode multi --file eval/goals_attack.jsonl --graph goals --workers 3

# traces land here — open any to read the result
eval/threads/{thread_id}/traces/run_0001.json

# what to look for in a trace:
#   trace["status"]           → "success" or "error"
#   trace["output"]["goals"]  → the GoalsProfile after the agent ran
#   trace["output"]["stage_reasoning"]["goals"]  → the analyst's reasoning text
#   trace["error_traceback"]  → full stack trace if status=error
```

**Supported graph names:**
```
thinking, purpose, goals, job, major, uni, output, orchestrator
(aliases: thinking_graph, purpose_graph, goals_graph, ... also accepted)
```

**Environment requirement:**
```
.env file at project root must contain OPENAI_API_KEY
load_dotenv() is called automatically at startup
```
