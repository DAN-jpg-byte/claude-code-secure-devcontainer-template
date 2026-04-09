# Dev Container / Python 環境まとめ（振り返り用）

## 1. 最初に起きていたこと

- `requests_sample.py` を実行すると  
  `ModuleNotFoundError: No module named 'requests'` になった。
- `requirements.txt` には `requests` が書いてあったが、**実行している Python とパッケージが入っている Python が一致していなかった**。

## 2. 原因の整理

### 2.1 システム Python と仮想環境の取り違え

- `/usr/bin/python3` や `/usr/local/python/current/bin/python` で実行すると、**`.venv` に入れた `requests` は見えない**。
- パッケージは `.venv` に入っているのに、別のインタープリタで動かしていたのが直接原因。

### 2.2 旧 `devcontainer.json` のハマりどころ

- `postCreateCommand` が `pip install -r requirements.txt` だけだと、**どの `pip` に入るかが曖昧**になりやすい。
- `postCreateCommand` は**コンテナ初回作成時に主に1回**なので、失敗に気づきにくい。

### 2.3 エディタの通知

- 「仮想環境が選ばれていない」という通知は、**このプロジェクトで使う Python の「道具箱」が未確定**という意味。  
  実行先と `pip install` 先のズレとつながる。

## 3. 実施した対策（devcontainer まわり）

### 3.1 `.venv` を明示し、そこにだけ入れる

- `postCreateCommand` を概ね次の方針に変更した（内容のイメージ）:
  - `python3 -m venv /workspace/.venv`
  - `/workspace/.venv/bin/python -m pip install --upgrade pip`
  - `/workspace/.venv/bin/python -m pip install -r /workspace/requirements.txt`

### 3.2 VS Code / Cursor 側のデフォルトインタープリタ

- `customizations.vscode.settings` に例えば次を追加:
  - `python.defaultInterpreterPath`: `/workspace/.venv/bin/python`
  - `python.terminal.activateEnvironment`: `true`

### 3.3 ターミナルでも `python` が `.venv` を向くようにする

- `remoteEnv` を追加:
  - `VIRTUAL_ENV=/workspace/.venv`
  - `PATH` の先頭に `/workspace/.venv/bin` を足す（`${containerEnv:PATH}` と連結）

### 3.4 `os-provided` について

- Python feature の `version: "os-provided"` は**起動が速い**一方、環境差は出やすい。  
  その代わり **`.venv` + `python -m pip` + `remoteEnv`** で実用上は揃えやすい。

### 3.5 Claude Code 向け設定は維持

- `runArgs`（`--env-file`）、`mounts`（`.claude`）、`containerEnv`（`CLAUDE_CONFIG_DIR`）は、Claude Code 利用のため**残す前提**。

## 4. 動作確認の目安

次が揃えば Python 周りは OK:

```bash
which python
python -c "import sys; print(sys.executable)"
python -c "import requests; print(requests.__version__)"
python /workspace/requests_sample.py
```

- `sys.executable` が `/workspace/.venv/bin/python`
- `requests` のバージョンが表示され、サンプルが HTTP 200 などで成功

## 5. デモ・再発防止

- **普段**: `python /workspace/requests_sample.py`
- **避ける**: `/usr/bin/python3 ...` のような**別インタープリタの直指定**（`.venv` を必ずバイパスする）
- **確実性最優先のデモ**:  
  `/workspace/.venv/bin/python /workspace/requests_sample.py`

## 6. ファイアウォール（`init-firewall.sh`）

### 6.1 一度あった問題

- `postStartCommand` で `node` ユーザーから `ufw` / `iptables` を触ろうとして **`Permission denied (you must be root)`** になるケースがあった。  
  → サンドボックスとしての通信制限が**効いていない**可能性。

### 6.2 CRLF 問題

- ログに `$'\r': command not found` が出る場合、**スクリプトが Windows 改行（CRLF）**のまま。  
  - `ufw` に渡る引数が壊れ、`Bad port` や `Invalid syntax` のように見える。
- 対処の方向性: **シェルは LF で保存**する。必要なら `.gitattributes` で `.devcontainer/*.sh` を `eol=lf` に固定。

### 6.3 成功時のログの目安

- `Default outgoing policy changed to 'deny'`
- `Rules updated` が続く
- `Firewall is active and enabled on system startup`
- `✅ 設定完了`  
  （かつ CRLF 由来の `$'\r'` エラーがないこと）

追加で中身を確認するなら（コンテナ内）: `sudo ufw status verbose` など。

## 7. 用語の超短い対応表

| 用語 | ざっくり意味 |
|------|----------------|
| `.venv` | このプロジェクト専用の Python とライブラリの置き場 |
| `python -m pip` | 「今の `python`」に確実にパッケージを入れる |
| `remoteEnv` | リモート（コンテナ）シェルに渡す環境変数（PATH など） |
| `postCreateCommand` | コンテナ作成直後に1回走るセットアップ |
| `postStartCommand` | 起動のたびに走るコマンド（今回はファイアウォール） |

## 8. このドキュメントの位置づけ

- **Python + requests**: `.venv` と PATH / インタープリタを揃えれば解決。
- **ファイアウォール**: 権限（root/sudo）と **CRLF** の2系統を切り分けると追いやすい。

## 関連ファイル

- 短い引き継ぎメモ: `devcontainer-issue-note.md`
- 本ドキュメント（振り返り用）: `devcontainer-retrospective.md`
