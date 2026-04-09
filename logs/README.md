# Repo Logs

This folder holds repo-local mirrors and durable logs that should stay outside `docs (archived)/`.

- `DEV_LOG.md`: human-readable navigation index for the mirrored project dev log
- `dev/days/*.md`: the actual daily dev-log files

## Two-Layer Rule

- the daily file is the log
- `DEV_LOG.md` is navigation only
- one line per day in the index
- one markdown file per day in the matching `days/` folder

## Dev Log

- canonical source: `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\DEV_LOG.md`
- canonical daily files: `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\dev-log\days\`
- repo mirror index: `logs/DEV_LOG.md`
- repo mirror daily files: `logs/dev/days/`

Workflow:

0. print the vault bootstrap packet if needed with `python scripts\pathfinder_ops.py bootstrap`
1. create the day file if needed with `python scripts\manage_dev_log.py ensure-day --date YYYY-MM-DD --summary "..."`
2. update the current day file in both repo and vault
3. keep the writing short and human-readable
4. run `python scripts\manage_dev_log.py rebuild`

Shortcut:

```powershell
python scripts\pathfinder_ops.py sync-dev-log --date YYYY-MM-DD --summary "..."
```

Validation:

```powershell
python scripts\manage_dev_log.py status
python scripts\manage_dev_log.py rebuild
python scripts\manage_dev_log.py validate
```
