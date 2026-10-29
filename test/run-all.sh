#!/bin/sh
# 本 repo 的整包閘。任何一項紅就整支紅。
# 內容：plugin manifest 嚴格驗證、工單格式檢查與其單元測試、gate.sh smoke、看守腳本 hook 單元測試。
set -e
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
echo "── claude plugin validate --strict ──"
# 兩份 manifest 都要逐檔驗。`validate .` 在兩者都存在時只驗 marketplace，plugin.json 會被跳過。
claude plugin validate .claude-plugin/plugin.json --strict
claude plugin validate .claude-plugin/marketplace.json --strict
echo "── check_change ──"
python3 tools/check_change.py .
# 管線退出碼取最後一段（sh 沒 pipefail），先存輸出再判退出碼，紅了才不會被 tail 吞掉。
out=$(python3 test/check_change.test.py 2>&1) || { echo "$out"; exit 1; }
echo "$out" | tail -1
echo "── gate ──"
sh test/gate.test.sh
echo "── guard-watch-script ──"
out=$(node test/guard-watch-script.test.mjs 2>&1) || { echo "$out"; exit 1; }
echo "$out" | grep -E "(tests|pass|fail) [0-9]"
echo "ALL GREEN"
