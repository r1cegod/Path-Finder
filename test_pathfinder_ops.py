import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.pathfinder_ops import build_bootstrap_packet, sync_dev_log_day


class PathfinderOpsContractTest(unittest.TestCase):
    def test_build_bootstrap_packet_preserves_order_and_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "AGENTS.md"
            b = root / "briefing.md"
            c = root / "now.md"
            d = root / "README.md"
            a.write_text("# AGENTS\n", encoding="utf-8")
            b.write_text("Briefing line\n", encoding="utf-8")
            c.write_text("\n# Now\n", encoding="utf-8")
            d.write_text("PathFinder README\n", encoding="utf-8")

            packet = build_bootstrap_packet(
                (
                    ("A", a),
                    ("B", b),
                    ("C", c),
                    ("D", d),
                )
            )

            self.assertIn("1. A:", packet)
            self.assertIn("2. B:", packet)
            self.assertIn("3. C:", packet)
            self.assertIn("4. D:", packet)
            self.assertIn("Preview: # AGENTS", packet)
            self.assertIn("Preview: Briefing line", packet)

    def test_sync_dev_log_day_creates_and_validates_indexes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_days = root / "repo-days"
            vault_days = root / "vault-days"
            repo_index = root / "repo-index.md"
            vault_index = root / "vault-index.md"

            result = sync_dev_log_day(
                date(2026, 4, 9),
                "Fresh helper day",
                repo_index=repo_index,
                vault_index=vault_index,
                repo_days_dir=repo_days,
                vault_days_dir=vault_days,
            )

            self.assertIn("created=2026-04-09.md", result)
            self.assertIn("rebuilt=1", result)
            self.assertIn("ok", result)
            self.assertTrue((repo_days / "2026-04-09.md").exists())
            self.assertTrue((vault_days / "2026-04-09.md").exists())
            self.assertIn("2026-04-09", repo_index.read_text(encoding="utf-8"))
            self.assertIn("2026-04-09", vault_index.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
