# BACKLOG — 範圍外發現，一件一行

一行要能自己站住：**做什麼＋在哪個檔＋為什麼**，讀的人不需要回頭找對話。做完就整行刪掉，理由寫在 commit 訊息。

| # | 一行 | 日期 |
|---|---|---|
| 15 | `cc-dispatch.md` 三缺口：P0 直走 `/cc-cursor`、`sync` 標 `stale-base`、部署類「驗」須含 build；跑完一波再定 | 2026-09-23 |
| 16 | `tools/gate.sh` 本身被 TERM 時，GATE 指令的 process group 不會一起殺（只有逾時分支會）；trap 補 kill -pgid | 2026-09-27 |
| 18 | `commands/cc-claude.md` 第 4 步假設 `Agent` 有 `name` 參數；本環境沒有，`agent:<handle>` 追問必走重開備案 | 2026-10-04 |
| 21 | `cc-dispatch.md` 第 102、141 行用狀態 `blocked`，但第 76 行的狀態值清單沒有它；擇一補齊 | 2026-10-16 |
