# Claude Code Secure DevContainer Template for Python

このテンプレートは、Claude Code を **Python 開発向け DevContainer 内で安全に運用**するための最小構成です。  
実ファイル（`.devcontainer/*`、`requirements.txt`、`env_check.py`、`requests_sample.py`）に合わせて説明しています。

## 最初に読む（コピー運用向け）

テンプレを複製して使う場合は、まず `TEMPLATE_SETUP_GUIDE.md` を読んでください。  
`.venv` をコピーしない運用と、`requirements.txt` の更新手順を短く整理しています。

## 目的

- DevContainer で作業領域を分離し、ホスト全体へのアクセス範囲を小さくする
- `.env` をコンテナ内に置かず、`--env-file` で環境変数だけ注入する
- Claude Code の設定/認証を `C:/Users/user/.claude` で永続化する
- Python 実行系を `.venv` に統一して、`pip` と実行インタープリタのズレを防ぐ
- UFW で外向き通信を最小限に制限し、noVNC 用の受信だけ追加する
- Chromium + Selenium でページを開き、noVNC でコンテナ内ディスプレイをブラウザから確認する

## Selenium + noVNC（最短手順）

初めての人向けの最小フローです。詳細・トラブル表は [`HANDOFF.md`](HANDOFF.md) を参照してください。

1. **Rebuild Container** またはコンテナを一度閉じて **Reopen in Container** する（`postCreate` / `postStart` が走る）。
2. ホストのブラウザで **`http://127.0.0.1:6080/vnc.html`** を開く（必要なら「接続」。自動接続例: `?autoconnect=true&resize=scale`）。
3. コンテナ内ターミナルで:

```bash
python /workspace/selenium_chrome_check.py
```

スクリーンショットは `/workspace/selenium_check.png` に保存されます。

### 毎回 noVNC が立っているか確認する（Step 4）

コンテナ起動直後、コンテナ内で次を実行します。

```bash
ss -ltn | grep -E '6080|5900'
```

`5900` と `6080` が **LISTEN** していれば、Xvfb→VNC→websockify まで到達しています。  
追加で、postStart 実行時刻付きの抜粋が **`~/.cache/novnc-logs/poststart-verify.log`** に追記されます。

**ダメなとき**: Dev Containers のログで `postStart` が **`post-start.sh`** / **`start-novnc.sh`** で失敗していないか確認してください。手動復旧:

```bash
bash /workspace/.devcontainer/init-firewall.sh
bash /workspace/.devcontainer/start-novnc.sh
```

各プロセスの詳細ログは `~/.cache/novnc-logs/`（`xvfb.log`, `x11vnc.log`, `websockify.log`）です。

### セキュリティの最終確認（Step 5）

- **6080**: エディタ（VS Code / Cursor）の**ポート転送**経由でホストから触る想定です。**ホスト側は localhost のまま**運用し、インターネットに裸で公開しないでください。
- **UFW**: 外向きは **53（DNS）/ 80（HTTP）/ 443（HTTPS）**、受信は **6080/tcp**、コンテナ内の **lo** の in/out を許可する構成です（実装は `init-firewall.sh`）。業務で追加が必要なら**最小限**に留めてください。
- **`.env`**: ワークスペース外に置き、`devcontainer.json` の `runArgs` の **`--env-file`** でだけ注入する運用を維持してください（ファイルをリポジトリに含めない）。

### 本番に近い確認（任意）

対象 URL が決まっている場合は環境変数で上書きします。

```bash
SELENIUM_TEST_URL='https://example.com' python /workspace/selenium_chrome_check.py
```

HTTPS で企業プロキシ等により証明書エラーになる場合は、**コンテナに企業ルート CA を追加**するのが正攻法です。検証専用としてのみ **`SELENIUM_INSECURE_TLS=1`** を検討してください（本番ターゲットでは使わない）。

## 主要ファイル構成

```text
.devcontainer/
├── devcontainer.json      # DevContainer 本体設定
├── Dockerfile             # ベースイメージ、Chromium/noVNC、UFW 用 sudo
├── init-firewall.sh       # 起動時の UFW 設定
├── post-start.sh          # postStart: UFW のあと noVNC 起動＋検証ログ追記
├── start-novnc.sh         # Xvfb / x11vnc / websockify（6080）

HANDOFF.md                 # 作業引き継ぎ・トラブル対応表（詳細）
CLAUDE.md                  # Claude Code への共通ルール
requirements.txt           # Python 依存ライブラリ（selenium 含む）
selenium_chrome_check.py   # Chromium + Selenium のスモークテスト（noVNC 表示可）
env_check.py               # 必須環境変数チェックサンプル
requests_sample.py         # requests 動作確認サンプル
devcontainer-retrospective.md  # トラブルと対策の記録
```

## 現在の実装内容

### `.devcontainer/devcontainer.json`

- Python Feature を有効化（`ghcr.io/devcontainers/features/python:1` / `version: "os-provided"`）
- ワークスペースを `/workspace` にマウント
- `runArgs` で外部 `.env` を注入し、`NET_ADMIN` を付与
- `mounts` で `C:/Users/user/.claude` を `/home/node/.claude` にバインド
- `containerEnv.CLAUDE_CONFIG_DIR` を `/home/node/.claude` に設定
- `remoteEnv` で `.venv` を優先（`VIRTUAL_ENV` と `PATH`）
- `postCreateCommand` で `.venv` 作成 + `requirements.txt` インストール
- `DISPLAY: ":99"`（`containerEnv` / `remoteEnv`）— Selenium のウィンドウを Xvfb 上に表示
- `forwardPorts`: `[6080]`、`portsAttributes` で noVNC ラベル
- `postStartCommand` で **`bash .devcontainer/post-start.sh`**（UFW のあと `start-novnc.sh`。検証ログを `~/.cache/novnc-logs/poststart-verify.log` に追記）

### `.devcontainer/Dockerfile`

- ベース: `mcr.microsoft.com/devcontainers/javascript-node:20`
- 追加パッケージ: `git`, `curl`, `ufw`
- **Chromium 系**: `chromium`, `chromium-driver`, `ca-certificates`, `fonts-liberation` など（HTTPS まわりのため recommends を落とさない方針）
- **noVNC 系**: `xvfb`, `x11vnc`, `novnc`, `websockify`, `iproute2`
- Claude Code を `npm install -g @anthropic-ai/claude-code` で導入
- `node` ユーザーに **`ufw` のみ** sudo 実行を許可（最小権限）
- 作業ディレクトリは `/workspace`

### `.devcontainer/init-firewall.sh`

- `ufw default deny outgoing`
- **ループバック `lo`**: in / out 許可（websockify → `127.0.0.1:5900` など）
- 外向き: **`53`（DNS）**, **`80`（HTTP）**, **`443`（HTTPS）**
- 受信: **`6080/tcp`**（noVNC / websockify。エディタのポート転送先）
- `ufw --force enable` を適用
- `sudo -n` を使い、対話待ちでハングしない構成

### `requirements.txt`

現状の主要依存:

- `requests`
- `pandas`
- `numpy`
- `python-dotenv`
- `selenium`

### `env_check.py`

- 必須環境変数 `PASSWORD` の存在確認
- 値は先頭のみマスク表示してフル値を出力しない
- 不足時は終了コード `1`、成功時は `0`

### `requests_sample.py`

- `https://httpbin.org/get` へ GET リクエスト
- `timeout=10` 付き、例外を捕捉して失敗を表示
- 成功時にステータスコード、URL、クエリ内容を表示

## セットアップ手順（Windows + DevContainer）

1. このフォルダを VS Code / Cursor で開く
2. `.devcontainer/devcontainer.json` の `runArgs` にある `--env-file` のパスを自分の環境に合わせる
3. 「Reopen in Container」または「Rebuild Container」を実行
4. コンテナ内ターミナルで確認:

```bash
which python
python -c "import sys; print(sys.executable)"
python -c "import requests; print(requests.__version__)"
python /workspace/requests_sample.py
python /workspace/env_check.py
```

期待値:

- `sys.executable` が `/workspace/.venv/bin/python`
- `requests` のバージョンが表示される
- `requests_sample.py` が成功する
- `env_check.py` は `PASSWORD` 未設定時に不足メッセージを出す

## セキュリティ運用ルール

- `.env` はワークスペースに置かない（外部配置 + `--env-file` のみ）
- API キー/パスワードをコードへハードコードしない
- 必須環境変数は起動時に明示的にバリデーションする
- `CLAUDE.md` のルール（日本語コメント、英語の識別子命名）に従う

## よく調整するポイント

- **`.env` の場所変更**: `devcontainer.json` の `runArgs` を更新
- **ユーザー変更**: `remoteUser` を変える場合は `.claude` マウント先と `CLAUDE_CONFIG_DIR` を合わせて変更
- **依存追加**: `requirements.txt` に追記後、Rebuild かコンテナ内で再インストール

## 補足ドキュメント

- Selenium / noVNC / UFW の引き継ぎとトラブル表: [`HANDOFF.md`](HANDOFF.md)
- 詳細な経緯とハマりどころ: `devcontainer-retrospective.md`
- 会話ベースの引き継ぎ要約: `conversation-summary.md`