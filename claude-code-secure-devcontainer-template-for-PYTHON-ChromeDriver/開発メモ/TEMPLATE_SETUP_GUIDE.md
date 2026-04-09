# テンプレートのコピー手順（最短版）

このファイルは「このフォルダをコピーして新規案件を作る」ための手順書です。

## 0. 先に結論

- コピー時に `.venv` は **含めない**（削除してからコピー、またはコピー対象から除外）
- 新規案件のライブラリは `requirements.txt` に追記する
- 依存変更後はコンテナ内で `python -m pip install -r requirements.txt` を実行する

## 1. テンプレをコピーする前にやること

### `.venv` を除外する理由

- `.venv` は環境依存（OS/パス/ビルド済みバイナリ）なので、使い回すと壊れやすい
- 容量が大きく、コピー時間も無駄に増える
- このテンプレは `postCreateCommand` で `.venv` を再作成できる

### 手順（推奨）

1. 元テンプレート側で `.venv` を削除
2. フォルダ全体をコピー
3. コピー先で DevContainer を Rebuild

## 2. コピー後に最初に変更する場所

### `devcontainer.json`

`.devcontainer/devcontainer.json` の `runArgs` にある `--env-file` パスを、あなたの環境に合わせて変更します。

```json
"runArgs": [
  "--env-file", "C:/your/path/.env",
  "--cap-add=NET_ADMIN"
]
```

### `.env` の置き場所

- `.env` はワークスペース配下に置かない
- コンテナ外に置いたファイルを `--env-file` で注入する

## 2.5 コピー直後に整理（不要ファイルの削除）

テンプレから新規案件を作るとき、次は不要なら削除してOKです。

- `開発メモ/conversation-summary.md`（会話の引き継ぎメモ）
- `開発メモ/devcontainer-retrospective.md`（検証/振り返りメモ）
- `開発メモ/` フォルダごと不要なら削除（設計・履歴メモ一式）
- リポジトリ直下の `README.md`（テンプレ説明。案件用 README に差し替えるなら削除）
- `requests_sample.py`（通信テストサンプル）
- `env_check.py`（環境変数チェックサンプル）

補足:

- `requirements.txt` は削除せず、案件に必要なライブラリだけ残して更新するのを推奨
- 後から参照したい場合は、削除前に別フォルダへ退避してもOK

## 3. `requirements.txt` の使い方

### 追加するとき

1. `requirements.txt` に必要ライブラリを1行ずつ追記
2. コンテナ内で次を実行

```bash
python -m pip install -r /workspace/requirements.txt
```

### サンプル

```txt
requests
pandas
numpy
python-dotenv
fastapi
uvicorn
```

### 注意点

- `pip install ...` ではなく、なるべく `python -m pip install ...` を使う  
  （実行中の Python と同じ環境に確実に入るため）

## 4. 動作確認コマンド

```bash
python -c "import sys; print(sys.executable)"
python -c "import requests; print(requests.__version__)"
python /workspace/requests_sample.py
python /workspace/env_check.py
```

確認ポイント:

- Python 実行ファイルが `/workspace/.venv/bin/python`
- `requests_sample.py` が成功
- `env_check.py` が必須環境変数不足を検知できる

## 5. よくある運用

- **ライブラリを増やしたい**: `requirements.txt` 追記 → `python -m pip install -r ...`
- **初期状態に戻したい**: `.venv` 削除 → Rebuild Container
- **他案件に再利用したい**: `.venv` を含めずにコピー

## 6. 追加のベストプラクティス

- 依存は `requirements.txt` を唯一の正にする（手元だけで `pip install` しっぱなしにしない）
- `requirements.txt` 更新後は動作確認コマンドまでセットで実行する
- `.env` は絶対に Git 管理しない（テンプレ運用でも毎回確認）
- 案件開始時に README を案件向けに最小更新（目的、起動手順、必要環境変数）する
- 不要サンプルを消したら、`git status` で削除漏れ/追加漏れを確認する
