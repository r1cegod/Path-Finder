import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.manage_vault_log import (
    add_hole,
    build_entry_block,
    build_log_index,
    close_hole,
    ensure_day,
    log_entry,
    read_daily_log,
    update_day_summary,
    validate,
)


DAY_FILE = """# 2026-04-08

Summary: Vault log moved to one file per day

## Activity

## [2026-04-08] FIX | Example

- changed something
"""


class ManageVaultLogContractTest(unittest.TestCase):
    def test_read_daily_log_requires_heading_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "2026-04-08.md"
            path.write_text(DAY_FILE, encoding="utf-8")

            daily = read_daily_log(path)

            self.assertEqual(daily.day.isoformat(), "2026-04-08")
            self.assertEqual(daily.summary, "Vault log moved to one file per day")

    def test_build_log_index_renders_navigation_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "2026-04-08.md"
            path.write_text(DAY_FILE, encoding="utf-8")
            daily = read_daily_log(path)

            index = build_log_index([daily])

            self.assertIn("Navigation only", index)
            self.assertIn("[sources/log/HOW_TO_WRITE.md]", index)
            self.assertIn(
                "- 2026-04-08 | Vault log moved to one file per day | [entry](./sources/log/days/2026-04-08.md)",
                index,
            )

    def test_validate_rejects_stale_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "log.md"
            days = root / "days"
            guide = root / "HOW_TO_WRITE.md"
            holes = root / "DATA_HOLES.md"
            days.mkdir(parents=True, exist_ok=True)
            (days / "2026-04-08.md").write_text(DAY_FILE, encoding="utf-8")
            guide.write_text("# Guide\n", encoding="utf-8")
            holes.write_text("# Data Holes\n", encoding="utf-8")
            index.write_text("# stale\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "stale"):
                validate(index, days, guide, holes)

    def test_ensure_day_creates_template_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            days = Path(tmp) / "days"

            result = ensure_day(days, date(2026, 4, 9), "Fresh day")

            created = days / "2026-04-09.md"
            self.assertIn("created=", result)
            self.assertTrue(created.exists())
            self.assertIn("Summary: Fresh day", created.read_text(encoding="utf-8"))

    # Fix 4 — update_day_summary
    def test_update_day_summary_rewrites_summary_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "2026-04-08.md"
            path.write_text(DAY_FILE, encoding="utf-8")

            update_day_summary(path, "Updated summary text")

            content = path.read_text(encoding="utf-8")
            self.assertIn("Summary: Updated summary text", content)
            self.assertNotIn("Vault log moved to one file per day", content)

    # Fix 1 — project tag in entry block
    def test_build_entry_block_includes_project_tag(self):
        block = build_entry_block(
            date(2026, 4, 8), "FIX", "Some subject", "pathfinder", ["- detail"]
        )
        self.assertIn("Project: pathfinder", block)
        self.assertIn("## [2026-04-08] FIX | Some subject", block)

    def test_build_entry_block_omits_project_tag_when_none(self):
        block = build_entry_block(
            date(2026, 4, 8), "FIX", "Some subject", None, ["- detail"]
        )
        self.assertNotIn("Project:", block)

    # Fix 2 — log_entry full pipeline
    def test_log_entry_full_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "log.md"
            days = root / "days"
            guide = root / "HOW_TO_WRITE.md"
            holes = root / "DATA_HOLES.md"
            days.mkdir(parents=True, exist_ok=True)
            guide.write_text("# Guide\n", encoding="utf-8")
            holes.write_text("# Data Holes\n", encoding="utf-8")

            result = log_entry(
                index,
                days,
                guide,
                holes,
                date(2026, 4, 9),
                "FIX",
                "Test entry",
                "pathfinder",
                ["- body line"],
                "Updated day summary",
            )

            self.assertIn("logged=2026-04-09", result)
            day_path = days / "2026-04-09.md"
            content = day_path.read_text(encoding="utf-8")
            self.assertIn("## [2026-04-09] FIX | Test entry", content)
            self.assertIn("Project: pathfinder", content)
            self.assertIn("Summary: Updated day summary", content)
            # index must be in sync
            index_content = index.read_text(encoding="utf-8")
            self.assertIn("2026-04-09", index_content)

    # Fix 3 — add_hole and close_hole
    def test_add_hole_appends_open_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            holes = Path(tmp) / "DATA_HOLES.md"
            holes.write_text("# Data Holes\n", encoding="utf-8")

            result = add_hole(holes, date(2026, 4, 8), "Missing auth docs", ["- no source yet"])

            self.assertIn("added:", result)
            content = holes.read_text(encoding="utf-8")
            self.assertIn("## [2026-04-08] OPEN | Missing auth docs", content)
            self.assertIn("- no source yet", content)

    def test_close_hole_marks_entry_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            holes = Path(tmp) / "DATA_HOLES.md"
            holes.write_text(
                "# Data Holes\n\n## [2026-04-07] OPEN | Missing auth docs\n- no source yet\n",
                encoding="utf-8",
            )

            result = close_hole(holes, "auth docs", "2026-04-08 vault log", date(2026, 4, 8))

            self.assertIn("closed:", result)
            content = holes.read_text(encoding="utf-8")
            self.assertIn("RESOLVED", content)
            self.assertIn("Resolved: 2026-04-08 by 2026-04-08 vault log", content)
            self.assertNotIn("## [2026-04-07] OPEN | Missing auth docs", content)

    def test_close_hole_raises_when_no_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            holes = Path(tmp) / "DATA_HOLES.md"
            holes.write_text("# Data Holes\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "No OPEN hole matching"):
                close_hole(holes, "nonexistent", "ref", date(2026, 4, 8))


if __name__ == "__main__":
    unittest.main()
