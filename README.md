# rr-dispatcher

照 `docs/changes/<slug>/tasks.md` 工單派工的 Claude Code plugin：派 Cursor／Claude 執行者、寫 PR body、
合併前跑閘＋獨立驗收、工單格式檢查。**獨立 plugin，不依賴其他 plugin。**
2026-10-29 從 `roylam-beep/cc-harness`（凍結在 0.5.2）拆出，決策見 `docs/decisions.md`。

| 指令 | 做什麼 |
|---|---|
| `/rr-dispatcher:cc-dispatch` | 照工單算波次、派執行者、跑閘＋獨立驗收、合進整合分支，全勾後歸檔 |
| `/rr-dispatcher:cc-cursor` | 派一個 Cursor cloud agent（要 cursor-cloud MCP） |
| `/rr-dispatcher:cc-claude` | 派一個背景 Claude 執行者 |
| `/rr-dispatcher:cc-pr` | 寫給人快速審的 PR body |

## 安裝

```bash
claude plugin marketplace add roylam-beep/rr-dispatcher
claude plugin install rr-dispatcher@rr-dispatcher
```

工單只在要拆給多個 agent 做時才開。repo 裡沒有 `docs/changes/README.md` 時，`/rr-dispatcher:cc-dispatch` 會從
`templates/changes-README.md` 鋪一份（cloud 執行者只讀得到 repo 裡的檔）。

被派工的 repo 建議在 `AGENTS.md` 的硬性規則寫：整合分支（預設 `claude/<slug>`）可直接 push；被派的 agent 只 push 自己的分支、
開 PR 到整合分支；閘＋獨立驗收過了才合併；合進 `main`、force-push、刪別人的分支要使用者當輪確認。

## 目錄

```
commands/                 派工 4 支
hooks/                    PreToolUse(Bash)：看守腳本 wait-for-run.js 只准背景跑（guard-watch-script.mjs）
tools/gate.sh             合併前閘：逐條跑 gate.env 的 GATE_n
tools/check_change.py     工單格式檢查（cc-dispatch 派工前從 plugin 直接跑）
templates/changes-README.md  工單格式本文，鋪進被派工 repo 的 docs/changes/README.md
test/run-all.sh           本 repo 的整包閘
docs/archive/changes/     歷來的工單（歷史）
```

## 改了要 bump

改了 `tools/` 或 `hooks/` 要 bump `.claude-plugin/plugin.json` 的 version，再
`claude plugin update rr-dispatcher@rr-dispatcher` 並重開 session（hook 從快取跑，版本在 session 開始時釘住）。

`main` 單線，remote 是 `roylam-beep/rr-dispatcher`。push 一律當輪問使用者。
