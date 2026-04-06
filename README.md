# 🐳 Claude Code × DevContainer セキュリティ設定

## このリポジトリは何？

Claude Code を **安全に** 使うための DevContainer 設定ファイル一式です。

Claude Code はターミナルで動く AI コーディングエージェントで、ファイルの読み書きやコマンドの実行ができます。
便利な反面、**ローカル（DevContainer なし）で起動すると、PC 上のすべてのファイルにアクセスできてしまう** というリスクがあります。
デスクトップのファイル、`.ssh` の秘密鍵、他のプロジェクトの `.env` ファイルなど、あなたのユーザー権限で読めるものは何でも読めます。

このリポジトリの設定を使うと、Claude Code を **Docker コンテナの中に閉じ込めて**、以下のセキュリティ対策を実現できます。

---

## 解決している問題（なぜこれが必要なのか）

### 問題 1：Claude Code は PC の全ファイルにアクセスできる

ローカルで `claude` を起動すると、起動したディレクトリだけでなく、`cd ..` で親に移動したり、
`cat ~/.ssh/id_rsa` で SSH 鍵を読んだりできてしまいます。
VS Code 拡張機能版の Claude Code でも同じです。

**→ DevContainer に入れることで、コンテナ内にマウントしたもの以外は一切アクセスできなくなります。**

### 問題 2：`.env` ファイルのシークレットが漏れる

コンテナ内に `.env` ファイルを置くと、Claude Code が `cat .env` で中身を読めてしまいます。
さらに、`.claudeignore` に書いても Claude Code はそれを無視することが報告されています（2026年1月 The Register 検証済み）。

**→ `.env` ファイルはコンテナの外に置き、`--env-file` オプションで環境変数としてだけ注入します。ファイルとしてはコンテナ内に存在しません。**

### 問題 3：コンテナを再ビルドすると設定が消える

Claude Code の認証情報、settings.json、カスタムスキルはデフォルトではコンテナ内に保存されます。
コンテナを Rebuild すると全部消えて、毎回ログインし直す必要がありました。

**→ Windows 側の `C:\Users\user\.claude` をコンテナにバインドマウントすることで、認証・設定・スキルが永続化されます。**

---

## ファイル構成

```
.devcontainer/
├── Dockerfile           … コンテナイメージの設計図
├── devcontainer.json    … DevContainer の設定（マウント、環境変数注入など）
└── init-firewall.sh     … コンテナ起動時に適用するファイアウォール

.claude/
└── settings.json        … Claude Code のパーミッション設定（allow / deny ルール）

CLAUDE.md                … Claude Code が起動時に自動で読むプロジェクト共通ルール
```

---

## 各ファイルの役割

### 1. `Dockerfile` — コンテナイメージの設計図

```dockerfile
FROM mcr.microsoft.com/devcontainers/javascript-node:20
```

- **ベースイメージ**: Microsoft 公式の Node.js 20 イメージ（デフォルトユーザーは `node`）
- **インストールするもの**: git, curl, ufw（ファイアウォール）, Claude Code
- Claude Code は `npm install -g @anthropic-ai/claude-code` でグローバルインストール
- イメージのビルドは初回（または Rebuild 時）だけ。普段の起動では再インストールされない

### 2. `devcontainer.json` — DevContainer の中核設定

このファイルで 3 つの重要なセキュリティ設定を行っている。
#### ① `runArgs` — .env を環境変数として注入

```json
"runArgs": [
  "--env-file", "C:/Users/user/projects/confidential/.env"
]
```
##### 構成の全体像

```
projects/
├── confidential/
│   └── .env                ← シークレットはここだけ（コンテナの外）
├── python-workspace/
│   ├── .devcontainer/      ← Python用DevContainer
│   ├── project-a/
│   ├── project-b/
│   └── ...
├── javascript-workspace/
│   ├── .devcontainer/      ← Node.js用DevContainer
│   └── ...
└── gas-workspace/
    ├── .devcontainer/      ← GAS(clasp+Node)用DevContainer
    └── ...
```

**ポイント：** `.env` ファイルは `confidential/` ディレクトリにだけ存在し、DevContainer のワークスペース内には一切置かない。






Windows 側の `.env` ファイルの中身を、コンテナ起動時に **環境変数として** 注入する。
ファイル自体はコンテナ内に存在しないので、Claude Code が `cat .env` しても何も見つからない。

#### ② `mounts` — Windows 側の .claude ディレクトリをマウント

```json
"mounts": [
  "source=C:/Users/user/.claude,target=/home/node/.claude,type=bind,consistency=cached"
]
```

Windows 側の `C:\Users\user\.claude` をコンテナ内の `/home/node/.claude` に接続する。
これにより以下が永続化される：

- 認証トークン（再ログイン不要）
- settings.json（パーミッション設定）
- カスタムスキル
- コマンド履歴・セッション情報

**重要**: `remoteUser` が `node` なのでパスは `/home/node/.claude`。
もし `vscode` ユーザーに変更する場合は `/home/vscode/.claude` に変える必要がある。

#### ③ `containerEnv` — 設定ディレクトリの場所を指定

```json
"containerEnv": {
  "CLAUDE_CONFIG_DIR": "/home/node/.claude"
}
```

Claude Code に「設定ファイルはここにあるよ」と明示的に教える環境変数。

#### その他の設定

- `postStartCommand`: コンテナ起動のたびにファイアウォールを適用（`postCreateCommand` ではなく `postStartCommand` を使うことで、再起動時にもファイアウォールが有効になる）
- `remoteUser`: `node`（Dockerfile のベースイメージに合わせる）

### 3. `init-firewall.sh` — ファイアウォール

```bash
sudo ufw default deny outgoing   # 全拒否がデフォルト
sudo ufw allow out to any port 53   # DNS（名前解決に必須）
sudo ufw allow out to any port 443  # HTTPS（Claude Code, npm, GitHub 等に必須）
```

- HTTPS 以外の通信（平文 HTTP、SSH 外部接続、Telnet など）をすべてブロック
- これは「おまけの防御層」という位置づけ。メインの防御は DevContainer の分離と settings.json
- より厳密なドメイン単位の制御が必要な場合は、Anthropic 公式の iptables ベースのスクリプトを参照:
  https://github.com/anthropics/claude-code/tree/main/.devcontainer

### 4. `settings.json` — Claude Code のパーミッション設定

Claude Code が「何をしていいか」「何をしてはいけないか」を定義するファイル。

**allow（許可）の考え方:**
- `Read` — ファイル読み取り（DevContainer 内なので安全）
- `Write(/workspace/**)` — ワークスペースへの書き込み（コードを書いてもらうのに必要）
- `Write(/tmp/**)` — 一時ファイル
- git の基本操作、grep/find/sed などのテキスト処理コマンド

**deny（禁止）の考え方:**
- ファイル削除系: `rm`, `shred`, `rmdir` など
- ネットワーク系: `curl`, `wget`, `ssh`, `scp` など
- 機密ファイル系: `.env`, `.ssh`, `.aws`, `.git-credentials` など
- 環境変数の覗き見: `printenv`, `env`, `set`, `/proc/*/environ`
- 危険な操作: `sudo`, `chmod 777`, `git push --force`, `git reset --hard`

### 5. `CLAUDE.md` — プロジェクト共通ルール

Claude Code が起動時に自動で読み込むファイル。以下のルールを指示している：

- `.env` ファイルを絶対に読まない
- シークレットをハードコードしない（すべて環境変数経由）
- コメントは日本語、変数名・関数名は英語
- `.env.example` にはプレースホルダーだけ書く

---

## セキュリティの多層防御（まとめ）

この設定は 4 つの防御層で構成されている：

| 層 | 何をしているか | 防いでいること |
|---|---|---|
| **第 1 層: DevContainer** | コンテナ分離 | PC のデスクトップ、.ssh、他プロジェクトへのアクセス |
| **第 2 層: --env-file** | .env をコンテナ外に配置 | シークレットファイルの直接読み取り |
| **第 3 層: settings.json** | allow/deny ルール | 危険なコマンド実行、環境変数の覗き見 |
| **第 4 層: ファイアウォール** | HTTPS 以外の通信をブロック | 平文でのデータ持ち出し |

---

## 使い方

### 前提条件

- Docker Desktop がインストールされていること
- VS Code + Dev Containers 拡張機能がインストールされていること
- Claude Code のアカウント（Anthropic のサブスクリプション）

### セットアップ

1. このリポジトリをクローンまたはコピーする

2. `C:\Users\user\projects\confidential\.env` にシークレットを配置する
   ```
   DATABASE_URL=postgres://...
   API_KEY=sk-...
   ```

3. VS Code でこのフォルダを開き、「Reopen in Container」を実行

4. コンテナが起動したら、作業したいプロジェクトのディレクトリに移動して Claude Code を起動
   ```bash
   cd /workspace/project-a
   claude
   ```

### Claude Code の起動ルール

**必ずサブディレクトリで起動すること。** Claude Code は起動したディレクトリを起点にコードベースを把握するので、
ワークスペースのルートで起動すると、すべてのプロジェクトのファイルを読み込んでしまう。

```bash
# ✅ 良い例
cd /workspace/project-a
claude

# ❌ 悪い例（ワークスペースのルートで起動）
cd /workspace
claude
```

---

## カスタマイズする場合の注意

### .env のパスを変更したい場合

`devcontainer.json` の `runArgs` 内のパスを書き換える：
```json
"runArgs": [
  "--env-file", "C:/Users/あなたのユーザー名/projects/confidential/.env"
]
```

### remoteUser を変更する場合

`remoteUser` を `vscode` などに変更する場合、以下の 2 箇所のパスも一緒に変える：
- `mounts` の `target` → `/home/vscode/.claude`
- `containerEnv` の `CLAUDE_CONFIG_DIR` → `/home/vscode/.claude`

### プロジェクト固有の CLAUDE.md を追加する場合

各プロジェクトディレクトリにも CLAUDE.md を置ける。
Claude Code は親ディレクトリを遡って CLAUDE.md を探すので、共通ルール（ルートの CLAUDE.md）と
プロジェクト固有ルールの両方が自動で読み込まれる。

```
/workspace/
├── CLAUDE.md              ← 共通ルール（すべてのプロジェクトに適用）
├── project-a/
│   ├── CLAUDE.md          ← project-a 固有のルール
│   └── src/
└── project-b/
    ├── CLAUDE.md          ← project-b 固有のルール
    └── src/
```

---

## 参考リンク

- [Anthropic 公式 DevContainer リファレンス](https://github.com/anthropics/claude-code/tree/main/.devcontainer)
- [Claude Code DevContainer ドキュメント](https://docs.anthropic.com/en/docs/claude-code/devcontainer)
- [API キーのベストプラクティス（Anthropic公式）](https://support.claude.com/en/articles/9767949-api-key-best-practices-keeping-your-keys-safe-and-secure)