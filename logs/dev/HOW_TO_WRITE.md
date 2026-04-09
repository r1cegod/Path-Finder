# How To Write A Dev Log

Write like a human who is trying to remember the day later, not like a report generator.

Rules:

- one file per day in `logs/dev/days/`
- one index line per day in `logs/DEV_LOG.md`
- if the same day changes again, update that same day file
- keep it short
- no quotes around normal words
- no excessive background
- no fake polish
- lead with what changed, why it mattered, and what is next

Recommended shape:

```md
# 2026-04-08

Summary: Short one-line day summary

## Updates

- changed:
- why:
- next:
```

Do:

- say what was actually changed
- name the files or system surface when useful
- keep verification as one short bullet if it matters
- create a missing day file with `python scripts\manage_dev_log.py ensure-day --date YYYY-MM-DD --summary "..."`
- rebuild the index with `python scripts\manage_dev_log.py rebuild`

Do not:

- write a mini essay
- restate project history
- explain obvious context the reader already knows
- create a second file for the same day
