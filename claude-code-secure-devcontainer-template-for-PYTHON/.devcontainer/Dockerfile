# 1. 土台となる「お部屋のベース」を選びます
# 「Node.js（JavaScriptを動かす道具）」が最初から入っている、
# マイクロソフト社公認の「綺麗な空き部屋」を借りてくる、という指示です。
FROM mcr.microsoft.com/devcontainers/javascript-node:20

# 2. 部屋に必要な「備え付けの工具」をインストールします
# ・apt-get update：最新の工具カタログをチェックして
# ・git：プログラムの履歴を保存する道具
# ・curl：ネットからファイルをダウンロードする道具
# ・ufw：泥棒が入らないようにする「玄関の鍵（ファイアウォール）」
# これらをまとめて部屋に備え付けます。
RUN apt-get update && apt-get install -y git curl ufw && \
    rm -rf /var/lib/apt/lists/*

# postStartCommand は remoteUser=node で動くため、UFW だけパスワードなし sudo 可能にする（NOPASSWD: ALL は付けない）
RUN echo 'node ALL=(root) NOPASSWD: /usr/sbin/ufw, /sbin/ufw' > /etc/sudoers.d/node-firewall && \
    chmod 0440 /etc/sudoers.d/node-firewall

# 3. メインの道具「Claude Code」をインストールします
# 先ほど借りたNode.jsという土台を使って、
# アンソロピック社の「Claude Code」という特別な道具を部屋の中に設置します。
RUN npm install -g @anthropic-ai/claude-code

# 4. 「作業机」の場所を決めます
# 「これからこの部屋に入ったら、"/workspace" という机の前で作業を始めてね」
# という立ち位置の指定です。
WORKDIR /workspace