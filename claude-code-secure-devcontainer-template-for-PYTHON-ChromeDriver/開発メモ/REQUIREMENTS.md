# 要件定義（Selenium + noVNC 対応 / セキュア DevContainer）

## 1. 目的

本プロジェクトは、DevContainer 内で **Claude Code を安全に運用**しつつ、Python による **Selenium（Chrome）自動化**を実行できる開発環境を提供する。  
加えて、Docker/DevContainer 内で動作する Chrome の画面を **リアルタイムで閲覧**できるようにする（noVNC）。

## 2. スコープ

### 2.1 対象（やること）

- DevContainer 環境で Python 実行（`.venv` 運用）を成立させる
- Selenium を利用して Chrome/Chromium を起動し、自動化を実行できる
- コンテナ内 GUI（仮想ディスプレイ）を noVNC で閲覧できる
- テンプレ既存のセキュリティ方針（`.env` 外部注入、UFW で外向き最小化、`.claude` 永続化）を維持する

### 2.2 対象外（今回やらない）

- Selenium Grid / 複数ノード分散実行
- ホスト側 GUI（ローカル Chrome）を直接操作する構成（X11 forward 等）
- CI での E2E 実行（必要になった時に別途）

## 3. 利用者像

- Windows ホスト上で VS Code / Cursor を用い DevContainer を起動する開発者
- Claude Code をコンテナ内で利用しつつ、Python + Selenium による検証/収集/自動操作を行う

## 4. 前提条件・制約

### 4.1 セキュリティ（テンプレ準拠）

- `.env` ファイルはワークスペース配下に置かない
- シークレットはハードコードしない（環境変数で注入）
- Claude Code の設定/認証はホスト側の `C:/Users/user/.claude` をマウントして永続化する

### 4.2 ネットワーク制約（UFW）

- コンテナからの外向き通信は原則拒否し、必要最小限のみ許可する
- 既定では DNS(53) と HTTPS(443) を許可する
- Selenium 実行で追加の外向き通信（例: 追加ドライバのダウンロード）が必要になる場合は、原則として **ビルド時に完結**させる

### 4.3 運用制約

- Python 依存は `requirements.txt` を唯一の正とする
- `.venv` はコピー運用せず、コンテナ作成時に再生成する

## 5. 機能要件

### 5.1 Python 実行

- `.venv` を `/workspace/.venv` に作成し、常にその Python が使われること
- `python -c "import sys; print(sys.executable)"` が `/workspace/.venv/...` を指すこと

### 5.2 Selenium 実行

- Python から `selenium` を import できること
- Chrome/Chromium を起動し、ページ遷移・DOM 操作・スクリーンショット取得等の基本操作ができること

### 5.3 リアルタイム閲覧（noVNC）

- コンテナ内で仮想ディスプレイ（例: Xvfb）上に描画された Chrome の画面を、ホストのブラウザから閲覧できること
- 推奨アクセス方法は `http://localhost:<noVNCポート>`（例: 6080）
- noVNC の公開範囲は原則ローカルホストに限定する（セキュリティ）

## 6. 非機能要件

### 6.1 セキュリティ

- noVNC のポートは `127.0.0.1` バインドを基本とし、意図せず LAN/WAN に公開しない
- noVNC に認証（パスワード等）を導入できる余地を残す（必要時に有効化）
- `.env` をコンテナ内/リポジトリ内に追加しない

### 6.2 再現性

- `Rebuild Container` で同じ手順で環境再構築できること
- Chrome/Driver のバージョン不整合で実行不能になりにくいこと（固定 or 自動整合の方針を明確化）

### 6.3 使いやすさ

- 最小手順で Selenium + 画面閲覧まで到達できること
- 典型的な動作確認コマンドが README に記載されること

## 7. 実装方針（最小変更）

### 7.1 変更対象ファイル（予定）

- `.devcontainer/Dockerfile`
  - Chrome/Chromium（および必要ライブラリ）導入
  - ChromeDriver（または自動管理手段）導入
  - Xvfb / VNC / noVNC（またはそれらを提供する軽量構成）導入
- `.devcontainer/devcontainer.json`
  - noVNC 用ポート転送（forwardPorts / portsAttributes 等）
  - 必要なら起動時に noVNC 関連プロセスを立ち上げる（postStartCommand 連携）
- `.devcontainer/init-firewall.sh`
  - 既存方針を維持しつつ、必要ならコンテナ内部プロセス間の通信に影響がないか確認
- `requirements.txt`
  - `selenium` 追加（必要なら補助ライブラリも）

### 7.2 画面表示の方式

- コンテナ内に「仮想ディスプレイ + VNC + noVNC」を用意し、ブラウザから閲覧する
- Chrome は headless ではなく、仮想ディスプレイ上で通常起動できる構成を採用する

### 7.3 ポート・URL（案）

- noVNC: `6080/tcp`（ホストから `http://localhost:6080`）
- VNC: `5900/tcp`（原則ホストへは公開しない。内部用途）

## 8. 受け入れ条件（Acceptance Criteria）

- DevContainer を起動し、`python` が `.venv` を指す
- `python -c "import selenium; print(selenium.__version__)"` が成功する
- Selenium スクリプトを実行すると Chrome が起動し、noVNC 画面にブラウザ操作が反映される
- noVNC はローカルホストから閲覧でき、外部ネットワークに不用意に公開されない
- `.env` をリポジトリに追加せず、`--env-file` により環境変数注入できる

## 9. 動作確認（テスト計画・最小）

- **環境確認**
  - `python -c "import sys; print(sys.executable)"`
  - `python -c "import selenium; print(selenium.__version__)"`
- **noVNC確認**
  - ブラウザで `http://localhost:6080` を開ける（ポートは構成に合わせる）
- **Selenium確認**
  - 任意のテスト URL を開き、ページタイトル取得・スクリーンショット保存を実行できる

## 10. 未決事項（決める必要があること）

- Chrome/Chromium と ChromeDriver のバージョン整合の取り方
  - 固定（安定）/ 自動追従（更新容易）のどちらを優先するか
- noVNC の認証方式（必要になる運用範囲があるか）
- Selenium 実行ターゲット（社内サイト等）により、UFW の外向き許可先を追加する必要があるか

