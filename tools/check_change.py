#!/usr/bin/env python3
"""check_change — 工單格式檢查（單檔、只用標準庫）。cc-dispatch 派工前跑，不複製進 repo。

用法：
  check_change.py [<root>]   驗 <root>/docs/changes/*/{spec,tasks}.md 的結構；不寫檔

spec.md 只准 `## Purpose`、`## 不做`（別名 `## Non-goals`／`## Out of scope`）、`## Requirements`；
舊工單的 `## ADDED／MODIFIED／REMOVED Requirements` 也認（REMOVED 不必有 Scenario）。
每條 `### Requirement:` 至少一個 `#### Scenario:`，每個 Scenario 要有 `- **WHEN**` 與 `- **THEN**`。
task 行固定 `- [ ] N.M <結果> ｜驗：<怎麼驗>`（`驗:`／`Verify:` 也認）。標題比對：trim 後大小寫敏感。
警告門檻可用環境變數改：`CHECK_CHANGE_MAX_ACTIVE`（預設 3）、`CHECK_CHANGE_WARN_CHARS`（預設 6000）。
沒有 docs/changes/ 整支綠。退出碼：0 綠／1 格式錯（一次收齊）／2 用法或路徑錯。
"""
import os
import re
import sys

H2 = re.compile(r"^##\s+(.+?)\s*$")
REQ = re.compile(r"^###\s+Requirement:\s*(.+?)\s*$")
SCN = re.compile(r"^####\s+Scenario:\s*(.+?)\s*$")
WHEN = re.compile(r"^\s*-\s+\*\*WHEN\*\*")
THEN = re.compile(r"^\s*-\s+\*\*THEN\*\*")
TASK_ANY = re.compile(r"^\s*-\s*\[")
TASK_OK = re.compile(r"^\s*-\s*\[( |[xX])\]\s*\d+\.\d+\s+\S")
TASK_DONE = re.compile(r"^\s*-\s*\[[xX]\]")
VERIFY = re.compile(r"驗[：:]|\bverify:", re.I)
NOT_DOING = ("不做", "Non-goals", "Out of scope")
REQ_SECTIONS = ("Requirements", "ADDED Requirements", "MODIFIED Requirements", "REMOVED Requirements")
ALLOWED = ("Purpose", *NOT_DOING, *REQ_SECTIONS)
MAX_ACTIVE = int(os.environ.get("CHECK_CHANGE_MAX_ACTIVE") or 3)          # 進行中工單超過就警告：先收一張再開
WARN_CHARS = int(os.environ.get("CHECK_CHANGE_WARN_CHARS") or 6_000)      # 單份 spec 超過就警告：只寫可觀察行為


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def check_spec(text, where, fails):
    """回 Requirement 條數；格式錯進 fails。"""
    seen, sec, req, scn, stray = {}, None, None, None, False
    reqs = []  # (節, 名, [(scenario 名, 行)])

    for line in text.splitlines():
        m = H2.match(line)
        if m:
            sec, req, scn = m.group(1), None, None
            if sec not in ALLOWED:
                fails.append(f"{where}：不允許的節「## {sec}」（只准 {'／'.join(ALLOWED)}）")
            continue
        if sec not in REQ_SECTIONS:
            continue
        m = REQ.match(line)
        if m:
            name = m.group(1)
            if name in seen:
                fails.append(f"{where}：Requirement「{name}」重複（{seen[name]} 與 {sec}）")
            seen[name] = sec
            req = (sec, name, [])
            reqs.append(req)
            continue
        if req is None:
            stray = stray or bool(line.strip())
            continue
        m = SCN.match(line)
        if m:
            req[2].append((m.group(1), []))
        elif req[2]:
            req[2][-1][1].append(line)
    if stray:
        fails.append(f"{where}：`### Requirement:` 之前有雜文，要求節只能放 Requirement 區塊")
    for sec, name, scns in reqs:
        if sec == "REMOVED Requirements":
            continue
        if not scns:
            fails.append(f"{where}：Requirement「{name}」沒有 Scenario（每條至少一個 `#### Scenario:`）")
        for sn, lines in scns:
            if not any(WHEN.match(l) for l in lines) or not any(THEN.match(l) for l in lines):
                fails.append(f"{where}：Scenario「{sn}」缺 `- **WHEN**` 或 `- **THEN**`")
    if not reqs:
        fails.append(f"{where}：沒有任何 `### Requirement:`")
    return len(reqs)


def tasks_stats(text):
    """回 (總數, 已勾, 格式錯的行號, 沒寫「驗：」的條數)。"""
    total = done = noverify = 0
    bad = []
    for i, line in enumerate(text.splitlines(), 1):
        if not TASK_ANY.match(line):
            continue
        if not TASK_OK.match(line):
            bad.append(i)
            continue
        total += 1
        done += bool(TASK_DONE.match(line))
        noverify += not VERIFY.search(line)
    return total, done, bad, noverify


def run(root):
    if not os.path.isdir(root):
        print(f"CHECK_CHANGE 用法錯：{root} 不是目錄")
        return 2
    cdir = os.path.join(os.path.abspath(root), "docs", "changes")
    if not os.path.isdir(cdir):
        print("CHECK_CHANGE OK（docs/changes/ 不存在，跳過）")
        return 0
    slugs = sorted(d for d in os.listdir(cdir) if os.path.isdir(os.path.join(cdir, d)) and not d.startswith("."))
    fails, warns = [], []
    for s in slugs:
        d, rel = os.path.join(cdir, s), f"docs/changes/{s}"
        if os.path.isfile(os.path.join(d, "spec.md")):
            text = read(os.path.join(d, "spec.md"))
            check_spec(text, f"{rel}/spec.md", fails)
            if len(text) > WARN_CHARS:
                warns.append(f"{rel}/spec.md {len(text):,} 字 > {WARN_CHARS:,}：spec 只寫可觀察行為，設計與步驟不進來")
        if os.path.isfile(os.path.join(d, "tasks.md")):
            total, done, bad, noverify = tasks_stats(read(os.path.join(d, "tasks.md")))
            for i in bad:
                fails.append(f"{rel}/tasks.md L{i}：task 行格式錯，應為 `- [ ] N.M <結果> ｜驗：<怎麼驗>`")
            if total == 0 and not bad:
                fails.append(f"{rel}/tasks.md 沒有任何 task")
            if noverify:
                warns.append(f"{rel}/tasks.md 有 {noverify} 條沒寫「驗：」")
            if total and done == total:
                warns.append(f"{rel} 任務全勾 → 歸檔：mkdir -p docs/archive/changes && "
                             f"git mv {rel} docs/archive/changes/<YYYY-MM-DD>-{s}")
    if len(slugs) > MAX_ACTIVE:
        warns.append(f"docs/changes/ 進行中 {len(slugs)} > {MAX_ACTIVE}（{'、'.join(slugs)}）——先收一張再開")
    for w in warns:
        print("⚠️ ", w)
    if fails:
        print("CHECK_CHANGE FAIL:")
        for x in fails:
            print(" -", x)
        return 1
    print(f"CHECK_CHANGE OK（進行中工單 {len(slugs)}/{MAX_ACTIVE}）")
    return 0


def main(argv):
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 2
    return run(argv[0] if argv else ".")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
