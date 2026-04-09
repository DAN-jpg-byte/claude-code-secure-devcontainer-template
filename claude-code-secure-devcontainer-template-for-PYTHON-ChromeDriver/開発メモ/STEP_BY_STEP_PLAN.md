# Selenium + noVNC 導入ステップ計画

`REQUIREMENTS.md` の要件を、依存関係を崩さず段階的に実施するための作業計画。

## 方針

- 一気に全部実装せず、`決める -> 土台構築 -> 動作確認` の順で進める
- 各ステップごとに「ゴール」と「受け入れ確認」を明確にする
- 先に Selenium 単体を成立させ、後から noVNC を重ねる

## Step 0: 未決事項を先に確定

### 決めること

- Chrome/ChromeDriver の整合方式
  - 初期は固定バージョン運用（再現性優先）
- noVNC 認証の有無
  - 初期は認証オフ、ただし localhost 限定公開を厳守
- UFW 追加許可の必要性
  - Selenium の実行ターゲットに応じて最小限で追加

### 完了条件

- 上記 3 点が方針として合意されている

## Step 1: Python 基盤を先に成立

### 対象

- `requirements.txt`
- 必要に応じて `.devcontainer/Dockerfile` の Python 関連

### 実施内容

- `.venv` が `/workspace/.venv` に作られる状態を整える
- `selenium` を `requirements.txt` から導入できる状態にする

### ゴール

- `.venv` の Python がデフォルトで使われる
- `import selenium` が成功する

### 受け入れ確認

- `python -c "import sys; print(sys.executable)"`
- `python -c "import selenium; print(selenium.__version__)"`

## Step 2: Chrome + Driver の Selenium 単体を成立

### 対象

- `.devcontainer/Dockerfile`

### 実施内容

- Chrome/Chromium と Driver を導入
- Selenium からブラウザ起動、ページ操作、スクリーンショット保存を確認

### ゴール

- noVNC なしでも Selenium 自動化が実行できる

### 受け入れ確認

- テスト URL を開いてタイトル取得が成功
- スクリーンショットファイルが生成される

## Step 3: noVNC 表示系を追加

### 対象

- `.devcontainer/Dockerfile`
- `.devcontainer/devcontainer.json`

### 実施内容

- 仮想ディスプレイ（Xvfb） + VNC + noVNC を導入
- ポート転送設定を追加（例: `6080`）
- `5900` は内部用途として扱い、ホスト公開しない

### ゴール

- ブラウザで `http://localhost:6080` からコンテナ内画面が見える

### 受け入れ確認

- noVNC 接続時に Chrome 操作がリアルタイム反映される

## Step 4: 起動フローを自動化

### 対象

- `.devcontainer/devcontainer.json`

### 実施内容

- `postStartCommand` などで noVNC 関連プロセスを自動起動
- Rebuild 後に最小手順で利用開始できるよう整理

### ゴール

- 環境再構築後も同じ手順で起動可能

## Step 5: セキュリティ要件を最終確認

### 対象

- `.devcontainer/init-firewall.sh`
- ポート公開設定
- 環境変数注入手順

### 実施内容

- `.env` をワークスペースに置かない運用を維持
- noVNC は localhost バインドを確認
- 外向き通信の許可先を最小化

### ゴール

- 既存テンプレのセキュリティ方針を維持したまま機能追加できている

## Step 6: README に最小手順を固定

### 対象

- リポジトリ直下の `README.md`

### 実施内容

- セットアップ手順、起動手順、確認コマンドを記載
- 初回利用者が迷わない順序に整理

### ゴール

- 新規メンバーが再現できるドキュメント状態

## 進行の目安

- Sprint A（半日〜1日）: Step 0〜2
- Sprint B（半日〜1日）: Step 3〜4
- Sprint C（1〜2時間）: Step 5〜6 + 最終受け入れ確認

## 最終受け入れチェック（要件対応）

- `python` が `.venv` を指す
- `selenium` の import とバージョン表示が成功
- Selenium 実行結果が noVNC 画面に反映される
- noVNC が外部ネットワークへ不用意に公開されない
- `.env` をリポジトリに追加せず、環境変数注入で運用できる
