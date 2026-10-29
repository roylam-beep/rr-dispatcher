#!/usr/bin/env python3
"""tools/check_change.py 的單元測試：每條格式規則各一個案例，用子程序驗真實退出碼。
負向案例必須真的紅——證明檢查會咬人，不是只證明綠燈會亮。
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "tools", "check_change.py")

REQ_A = """### Requirement: Export CSV
The system SHALL export user data as CSV.

#### Scenario: Click export
- **WHEN** the user clicks Export
- **THEN** a CSV downloads
"""
DONE = "## 1. Wave\n- [x] 1.1 做完 ｜驗：pytest\n"
OPEN = "## 1. Wave\n- [ ] 1.1 沒做 ｜驗：pytest\n"


def spec(reqs=REQ_A, heading="Requirements", extra=""):
    return f"## Purpose\nDemo.\n\n## {heading}\n\n{reqs}\n{extra}"


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)

    def change(self, spec_text, tasks=OPEN, slug="s"):
        self.put(f"docs/changes/{slug}/spec.md", spec_text)
        if tasks is not None:
            self.put(f"docs/changes/{slug}/tasks.md", tasks)

    def run_tool(self, *args, env=None):
        r = subprocess.run([sys.executable, TOOL, *args], cwd=self.root, capture_output=True, text=True,
                           env={**os.environ, **(env or {})})
        return r.returncode, r.stdout + r.stderr

    def test_01_no_changes_dir_is_green(self):
        rc, out = self.run_tool(".")
        self.assertEqual(rc, 0, out)
        self.assertIn("不存在，跳過", out)

    def test_02_requirements_section_green(self):
        self.change(spec())
        rc, out = self.run_tool(".")
        self.assertEqual(rc, 0, out)
        self.assertIn("進行中工單 1/3", out)

    def test_03_legacy_delta_headings_accepted(self):
        self.change(spec(heading="ADDED Requirements") + "## REMOVED Requirements\n\n### Requirement: Old\n")
        self.assertEqual(self.run_tool(".")[0], 0)

    def test_04_zero_scenario_fails(self):
        self.change(spec(reqs="### Requirement: Bare\nno scenario\n"))
        rc, out = self.run_tool(".")
        self.assertEqual(rc, 1)
        self.assertIn("沒有 Scenario", out)

    def test_05_missing_when_or_then_fails(self):
        self.change(spec(reqs=REQ_A.replace("- **THEN** a CSV downloads", "- a CSV downloads")))
        rc, out = self.run_tool(".")
        self.assertEqual(rc, 1)
        self.assertIn("WHEN", out)

    def test_06_duplicate_requirement_fails(self):
        self.change(spec(reqs=REQ_A + "\n" + REQ_A))
        rc, out = self.run_tool(".")
        self.assertEqual(rc, 1)
        self.assertIn("重複", out)

    def test_07_illegal_heading_and_empty_spec_fail(self):
        self.change(spec(extra="## Design\nx\n"))
        self.assertEqual(self.run_tool(".")[0], 1)
        self.change("## Purpose\nOnly purpose.\n", slug="t")
        rc, out = self.run_tool(".")
        self.assertEqual(rc, 1)
        self.assertIn("沒有任何", out)

    def test_08_bad_task_line_and_no_tasks_fail(self):
        self.change(spec(), tasks="## 1. W\n- [~] 1.1 weird ｜驗：x\n")
        rc, out = self.run_tool(".")
        self.assertEqual(rc, 1)
        self.assertIn("tasks.md L2", out)
        self.change(spec(), tasks="## 1. W\nno tasks here\n")
        rc, out = self.run_tool(".")
        self.assertEqual(rc, 1)
        self.assertIn("沒有任何 task", out)

    def test_09_warnings_do_not_fail(self):
        for s in ("a", "b", "c"):
            self.change(spec(), tasks=DONE, slug=s)
        self.change(spec(), tasks="## 1. W\n- [ ] 1.1 no verify phrase\n", slug="d")
        rc, out = self.run_tool(".")
        self.assertEqual(rc, 0, out)
        self.assertIn("進行中 4 > 3", out)
        self.assertIn("任務全勾 → 歸檔", out)
        self.assertIn("沒寫「驗：」", out)

    def test_10_english_aliases(self):
        self.change(spec(extra="## Non-goals\n- nothing\n"), tasks="## 1. W\n- [ ] 1.1 ship it | Verify: pytest\n")
        rc, out = self.run_tool(".")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("沒寫「驗：」", out)
        self.change(spec(extra="## Nongoals\n- x\n"), slug="u")
        self.assertEqual(self.run_tool(".")[0], 1, "不是別名的標題照樣紅")

    def test_11_threshold_from_env_and_bad_path(self):
        for s in ("a", "b"):
            self.change(spec(), slug=s)
        rc, out = self.run_tool(".", env={"CHECK_CHANGE_MAX_ACTIVE": "1"})
        self.assertEqual(rc, 0, out)
        self.assertIn("進行中 2 > 1", out)
        self.assertEqual(self.run_tool("no-such-dir")[0], 2)


if __name__ == "__main__":
    r = unittest.main(exit=False, verbosity=0).result
    n = r.testsRun
    ok = r.wasSuccessful()
    print(f"CHECK_CHANGE_TEST {'OK' if ok else 'FAIL'}（{n} 項{'' if ok else f'，失敗 {len(r.failures) + len(r.errors)}'}）")
    sys.exit(0 if ok else 1)
