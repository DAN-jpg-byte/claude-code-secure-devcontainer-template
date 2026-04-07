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
- UFW で外向き通信を最小限（DNS/HTTPS）に制限する

## 主要ファイル構成

```text
.devcontainer/
├── devcontainer.json      # DevContainer 本体設定
├── Dockerfile             # ベースイメージとツール導入
└── init-firewall.sh       # 起動時の UFW 設定

CLAUDE.md                  # Claude Code への共通ルール
requirements.txt           # Python 依存ライブラリ
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
- `postStartCommand` で `bash .devcontainer/init-firewall.sh` を毎回実行

### `.devcontainer/Dockerfile`

- ベース: `mcr.microsoft.com/devcontainers/javascript-node:20`
- 追加パッケージ: `git`, `curl`, `ufw`
- Claude Code を `npm install -g @anthropic-ai/claude-code` で導入
- `node` ユーザーに `ufw` のみ sudo 実行を許可（最小権限）
- 作業ディレクトリは `/workspace`

### `.devcontainer/init-firewall.sh`

- `ufw default deny outgoing`
- `53`（DNS）と `443`（HTTPS）だけ外向き許可
- `ufw --force enable` を適用
- `sudo -n` を使い、対話待ちでハングしない構成

### `requirements.txt`

現状の主要依存:

- `requests`
- `pandas`
- `numpy`
- `python-dotenv`

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

- 詳細な経緯とハマりどころ: `devcontainer-retrospective.md`
- 会話ベースの引き継ぎ要約: `conversation-summary.md`