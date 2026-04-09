# Claude Code Secure DevContainer Template for Python

このテンプレートは、Claude Code を **Python 開発向け DevContainer 内で安全に運用**するための最小構成です。  
実ファイル（`.devcontainer/*`、`requirements.txt`、`env_check.py`、`requests_sample.py`）に合わせて説明しています。  
**後から全体像だけ追いかけたい**ときは、下の **「このテンプレでできること・全体の振り返り（後から読む用）」** を読んでください。

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

**6080 だけ LISTEN して 5900 が無い**場合は、postStart のシェル終了時に **x11vnc だけ落ち**、**websockify（nohup）だけ残る**ことがあります。`start-novnc.sh` では Xvfb / x11vnc を **`setsid` + `nohup`** で制御端末から切り離して起動しています。**Rebuild** するか、下の手動復旧で `start-novnc.sh` を再実行してください。

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

## このテンプレでできること・全体の振り返り（後から読む用）

数ヶ月後に README だけ開いても、「このリポジトリは何の箱か」「どう動いていたか」「困ったとき何を見るか」が追いやすいように、いまの構成をやさしい言葉でまとめた節です。上の「Selenium + noVNC（最短手順）」と重なる部分もありますが、こちらは**意味と経緯**を取りに来たとき向けです。

### 一言でいうと何ができるか

**自分の Windows の上で動いている VS Code / Cursor から、Docker の中の Linux（Dev Container）に入り、その中で Python を動かせます。** さらにその箱の中では、

- **Chromium（Chrome に近いブラウザ）** を **Selenium** で自動的に開いたり、ページを読んだり、画面の画像を保存したりできる  
- コンテナの中には物理モニターがないので **仮想ディスプレイ（Xvfb）** の上に画面を描画し、**noVNC** 経由で **自分の PC のブラウザ**（`http://127.0.0.1:6080/vnc.html`）から、その様子を**動画に近い形で見られる**  
- 外のネットワークへの出方は **UFW（ファイアウォール）** で「許可した種類の通信だけ」に寄せている  
- パスワードや API キーは **`.env` ファイルをプロジェクトフォルダに置かず**、**別の場所のファイル**から **`--env-file`** で環境変数としてだけ流し込む、という運用を前提にしている  

という状態を目指したテンプレです。**「Web を自動操作して検証する」「画面付きで挙動を目視したい」「秘密情報をリポジトリに混ぜたくない」** の出発点として使えます。

### 部品の名前と役割（対応表）

名前が多いので、**何をしている部品か**だけ短く対応させます。

| 名前 | ざっくりした役割 |
|------|------------------|
| **Dev Container** | エディタが開く「コンテナの中の開発部屋」。ホストのファイルを `/workspace` にマウントして編集する。 |
| **Dockerfile** | その部屋の「最初から入っているソフト」のレシピ。Node・Python 用土台・Chromium・noVNC 用ツール・UFW など。 |
| **`devcontainer.json`** | 部屋の使い方の設定。ポート転送、環境変数、コンテナ起動後に走らせるコマンドなど。 |
| **`.venv`** | Python 用の仮想環境。`requirements.txt` をここに `pip install` する想定で、`remoteEnv` で優先される。 |
| **Chromium + chromedriver** | ブラウザ本体と、プログラムから操作するためのドライバ。同じディストリの **apt** で揃え、バージョンの食い違いを減らす方針。 |
| **Xvfb** | モニターがない環境で「仮想の画面（ディスプレイ `:99`）」を作る。 |
| **x11vnc** | その仮想画面を VNC で出す。既定では **5900** 番ポートで待ち受け、**コンテナ内の localhost 向け**に寄せている。 |
| **websockify（noVNC 用）** | VNC を Web 用プロトコルに載せ替え、**6080** で待ち受ける。ホスト側はエディタの **ポート転送** で `localhost` から触る。 |
| **UFW** | 「外へ出す通信は基本ダメ。書いたルールだけ通す」方式のファイアウォール。`init-firewall.sh` でルールを入れる。 |
| **`post-start.sh`** | コンテナが**起動するたび**に走る `postStart` 用の入口。中でファイアウォールのあと **noVNC 一式を起動**し、ログに listen 状況を残す。 |

### コンテナを開いたあと、裏で何が起きるか（順序）

初めての人が「なぜ Rebuild したら一通り動くのか」を追いやすいように、**だいたいの順番**だけ書きます。

1. **Rebuild** や **Reopen in Container** でコンテナが立ち上がる。  
2. **`postCreateCommand`**（初回に近いタイミング）で、`.venv` の作成と `pip install -r requirements.txt` が走る。Python と Selenium などがここで入る。  
3. **`postStartCommand`** で **`bash .devcontainer/post-start.sh`** が実行される。  
4. **`post-start.sh`** の中で、まず **`init-firewall.sh`** が UFW のルールを入れる（DNS・HTTP・HTTPS の外向き、6080 の受信、ループバックの許可など）。  
5. 続けて **`start-novnc.sh`** が **Xvfb → x11vnc → websockify** の順で（必要なら）起動する。  
6. 成功すると、Dev Containers のログに **`[devcontainer post-start] 完了`** のような行が出る。また **`~/.cache/novnc-logs/poststart-verify.log`** に、そのときの **5900 / 6080** の listen 抜粋が追記される。  

ここまでが「毎回自動」。**手で `start-novnc.sh` を叩かなくても**、設定どおりなら起動直後から noVNC の準備が整う想定です。

### なぜ `setsid` と `nohup` を使っているか（経緯のメモ）

過去の挙動として、**postStart を実行したシェルが終わるタイミングで、プロセスに SIGHUP（いわゆる「親が終わるよ」信号）が飛ぶ**ことがありました。その結果、

- **websockify** はもともと **`nohup`** で起動していて生き残る → **6080 だけ LISTEN のまま**  
- **x11vnc** 側だけ落ちる → **5900 が消える**  

という「半分だけ残る」状態になり得ました。いまの **`start-novnc.sh`** では **Xvfb** と **x11vnc** も **`setsid` + `nohup`** で**制御端末から切り離して**起動し、postStart の親シェルが終わっても **5900 と 6080 が揃ったまま**残りやすくしてあります。

確認はコンテナ内で次のどちらかで十分です。

```bash
ss -ltnp | grep -E '5900|6080'
```

### Selenium の「画面に出す／出さない」

- **noVNC で Chromium のウィンドウを見たい**  
  - コンテナに **`DISPLAY=:99`** が付いている状態（このテンプレの既定）で、**`SELENIUM_HEADLESS=1` を付けない**。  
  - 代表例: `python /workspace/selenium_chrome_check.py`（スクリーンショットは `/workspace/selenium_check.png`）。  

- **ヘッドレスで軽く動かしたい（noVNC には映らない）**  
  - **`SELENIUM_HEADLESS=1`** を付ける。  

- **開く URL や証明書まわり**  
  - URL は **`SELENIUM_TEST_URL`** で変えられる。  
  - 企業プロキシなどで HTTPS が壊れて見える場合は、**正攻法は企業のルート CA をコンテナに入れる**こと。検証専用としてだけ **`SELENIUM_INSECURE_TLS=1`** を使う、という整理（本番の検証対象では使わない）。  

細かい環境変数の一覧は **`selenium_chrome_check.py`** 先頭のドキュメント文字列にあります。

### セキュリティで押さえておきたいこと（短く）

- **6080** … **インターネット全体にポートを開けない**。**エディタのポート転送**で **localhost から**使う想定。  
- **UFW** … **外向きは必要最小限**（いまは DNS・HTTP・HTTPS など）。業務で別ポートが要るなら**足しすぎない**。  
- **`.env`** … **リポジトリに含めない**。**ワークスペース外**に置き、`runArgs` の **`--env-file`** だけで注入する。  

詳細はこの README の「セキュリティの最終確認（Step 5）」と **`REQUIREMENTS.md`** も参照してください。

### 困ったときの見どころ（チェックリスト）

| 気になること | まず見る場所 |
|--------------|----------------|
| 起動直後から noVNC に繋がらない | Dev Containers の**出力ログ**で `postStart` が **`[devcontainer post-start] 完了`** まで行っているか。`~/.cache/novnc-logs/` の各 `.log`。 |
| **6080 だけ**あって **5900 が無い** | 古い挙動や途中失敗の可能性。最新の `start-novnc.sh` で **Rebuild** 済みか。手動なら `bash /workspace/.devcontainer/start-novnc.sh`。 |
| Selenium だけ外部に繋がらない | **UFW** で 80/443 が許可されているか（`init-firewall.sh`）。タイムアウトなら `selenium_chrome_check.py` のリトライや `page_load_strategy` の説明。 |
| 証明書エラーだらけ | プロキシの TLS 検査が疑わしい。**CA 追加**か、検証専用の **`SELENIUM_INSECURE_TLS`** の扱いを読む。 |

より表形式の対処は **`HANDOFF.md`** にまとまっています。

### 要件・計画ドキュメントへの道しるべ

| 読みたい内容 | ファイル |
|--------------|-----------|
| 何を必須とみなすか、受け入れ条件 | **`REQUIREMENTS.md`** |
| Step 0〜6 の段階的な計画 | **`STEP_BY_STEP_PLAN.md`** |
| ファイル別の変更内容・ハマりどころ表 | **`HANDOFF.md`** |
| テンプレを複製したときの手順 | **`TEMPLATE_SETUP_GUIDE.md`** |

---

この節は「忘れ防止用の地図」です。**手順だけ素早くやりたい**ときは、上の **「Selenium + noVNC（最短手順）」** に戻るとよいです。

## 補足ドキュメント

- Selenium / noVNC / UFW の引き継ぎとトラブル表: [`HANDOFF.md`](HANDOFF.md)
- 詳細な経緯とハマりどころ: `devcontainer-retrospective.md`
- 会話ベースの引き継ぎ要約: `conversation-summary.md`