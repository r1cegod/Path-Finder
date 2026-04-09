import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.manage_dev_log import (
    build_dev_index,
    ensure_day,
    ensure_repo_vault_days_match,
    read_daily_log,
    validate,
)


DAY_FILE = """# 2026-04-08

Summary: Two-layer dev-log architecture and human writing rule

## Updates

- Moved the dev log to one file per day.
"""


class ManageDevLogContractTest(unittest.TestCase):
    def test_read_daily_log_requires_heading_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "2026-04-08.md"
            path.write_text(DAY_FILE, encoding="utf-8")

            daily = read_daily_log(path)

            self.assertEqual(daily.day.isoformat(), "2026-04-08")
            self.assertEqual(
                daily.summary,
                "Two-layer dev-log architecture and human writing rule",
            )

    def test_ensure_repo_vault_days_match_rejects_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_days = root / "repo"
            vault_days = root / "vault"
            repo_days.mkdir(parents=True, exist_ok=True)
            vault_days.mkdir(parents=True, exist_ok=True)

            (repo_days / "2026-04-08.md").write_text(DAY_FILE, encoding="utf-8")
            (vault_days / "2026-04-08.md").write_text(
                DAY_FILE.replace("human writing rule", "other summary"),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "differ"):
                ensure_repo_vault_days_match(repo_days, vault_days)

    def test_build_dev_index_renders_one_line_per_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            day_path = Path(tmp) / "2026-04-08.md"
            day_path.write_text(DAY_FILE, encoding="utf-8")
            daily = read_daily_log(day_path)

            index = build_dev_index(
                [daily],
                title="PathFinder - Dev Log",
                link_prefix="./dev/days",
            )

            self.assertIn("Navigation only", index)
            self.assertIn(
                "- 2026-04-08 | Two-layer dev-log architecture and human writing rule | [entry](./dev/days/2026-04-08.md)",
                index,
            )

    def test_validate_rejects_stale_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_days = root / "repo-days"
            vault_days = root / "vault-days"
            repo_index = root / "repo-index.md"
            vault_index = root / "vault-index.md"
            repo_days.mkdir(parents=True, exist_ok=True)
            vault_days.mkdir(parents=True, exist_ok=True)
            (repo_days / "2026-04-08.md").write_text(DAY_FILE, encoding="utf-8")
            (vault_days / "2026-04-08.md").write_text(DAY_FILE, encoding="utf-8")
            repo_index.write_text("# stale\n", encoding="utf-8")
            vault_index.write_text("# stale\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "stale"):
                validate(repo_index, vault_index, repo_days, vault_days)

    def test_ensure_day_creates_both_repo_and_vault_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_days = root / "repo-days"
            vault_days = root / "vault-days"

            result = ensure_day(repo_days, vault_days, date(2026, 4, 9), "Fresh dev day")

            self.assertIn("created=", result)
            self.assertTrue((repo_days / "2026-04-09.md").exists())
            self.assertTrue((vault_days / "2026-04-09.md").exists())


if __name__ == "__main__":
    unittest.main()
