# Dev Container 問題メモ（引き継ぎ用）

## 1. 発生していた問題
- `requests_sample.py` 実行時に `ModuleNotFoundError: No module named 'requests'`
- 原因は、`.venv` ではなく `/usr/bin/python3`（システムPython）で実行していたため

## 2. 対応済み
- `devcontainer.json` を修正し、`.venv` を自動構築するようにした
- `postCreateCommand` で以下を実行するように変更済み
  - `.venv` 作成
  - `pip` 更新
  - `requirements.txt` インストール
- `remoteEnv` を追加し、ターミナルの `python` が `.venv` 優先になるようにした
- 実行確認済み:
  - `which python` → `/workspace/.venv/bin/python`
  - `python -c "import requests"` 成功
  - `python /workspace/requests_sample.py` 成功（ステータス200）

## 3. 未解決（明日やる）
- `postStartCommand` の `init-firewall.sh` が権限不足で失敗
- エラーログ:
  - `you must be root`
  - `iptables / ufw / sysctl permission denied`
- 影響:
  - Python実行には影響なし
  - ただし「通信制限サンドボックス」としては不完全

## 4. 当面の運用ルール（再発防止）
- `python /workspace/requests_sample.py` を使う
- `/usr/bin/python3 /workspace/requests_sample.py` は使わない
- デモで確実性重視なら:
  - `/workspace/.venv/bin/python /workspace/requests_sample.py`

## 5. 明日のToDo
- `init-firewall.sh` を root 権限で安全に実行できる設計に変更
- `remoteUser=node` を維持したまま必要箇所だけ昇格（sudo/実行タイミング見直し）
- 変更後に以下を確認
  - ファイアウォール適用成功ログ
  - Python/Claude Code の通常動作に影響がないこと
