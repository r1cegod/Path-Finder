# Eval Runner

`eval/run_eval.py` runs one JSONL dataset through a selected PathFinder graph and writes one trace file per input run.

## Requirements

- Run from the repo root: `D:/ANHDUC/Path_finder`
- Activate the existing virtual environment first:

```powershell
venv\Scripts\activate
```

- Make sure `.env` contains the keys required by the graph you want to run

## CLI

```powershell
python eval/run_eval.py --mode single --file eval/purpose_attack.jsonl --graph purpose
python eval/run_eval.py --mode multi --file eval/purpose_attack.jsonl --graph purpose
python eval/run_eval.py --mode multi --file eval/thinking_attack_v2.jsonl --graph thinking --workers 4
```

## Arguments

- `--mode single|multi`
  - `single`: one shared `thread_id` for the whole dataset, inputs run sequentially
  - `multi`: one `thread_id` per input, inputs run concurrently
- `--file <jsonl_path>`
  - Must point to a `.jsonl` file inside `eval/`
- `--graph <graph_name>`
  - Supported canonical names: `thinking`, `purpose`, `goals`, `job`, `major`, `uni`, `output`, `orchestrator`
  - Supported aliases: `thinking_graph`, `purpose_graph`, `goals_graph`, `job_graph`, `major_graph`, `uni_graph`, `university`, `output_graph`, `input_orchestrator`
- `--workers <int>`
  - Optional, only relevant for `multi`
  - Defaults to `min(8, number_of_inputs)`

## Input Shape

Each JSONL line is one independent input object.

Current datasets in `eval/` already follow this pattern. Examples:

- `eval/purpose_attack.jsonl`
  - carries profile state such as `thinking` and `purpose`
  - carries the stage conversation in `purpose_message`
- `eval/thinking_attack_v2.jsonl`
  - carries the stage conversation in `thinking_style_message`

The runner starts from `backend.data.state.DEFAULT_STATE`, then overlays each JSON object onto that state.

Normalization rules:

- If the target graph queue is missing but the row contains exactly one conversation queue, that queue is mirrored into the target queue.
- If the row has `messages` only and the target graph is stage-specific, `messages` is mirrored into the stage queue.
- If `stage.current_stage` is missing, the runner sets it from the selected graph.

## Trace Output

Trace files are written to:

```text
eval/threads/<thread_id>/traces/run_0001.json
```

Single mode:

- one `thread_id` for the entire dataset
- multiple trace files under the same `eval/threads/<thread_id>/traces/`

Multi mode:

- one `thread_id` per input row
- one trace file in each thread directory

Each trace JSON contains:

- `input`
- `output`
- `thread_id`
- `timestamp`
- `graph_name`
- `run_index`

Additional fields are also included for debugging:

- `graph_key`
- `graph_module`
- `input_file`
- `mode`
- `status`
- `normalized_input`
- `error_traceback` on failures

## Output Semantics

- `output` stores the full graph result state serialized into JSON-friendly data
- LangChain messages are serialized as objects with `type`, `content`, and any available metadata
- Failures still produce a trace file with `status: "error"` and an error payload in `output`

## Notes

- The runner only reads datasets from `eval/` and only writes traces under `eval/threads/`
- It does not modify backend code or backend state definitions
- If any input run fails, the script exits with status code `1` after writing all trace files it completed
