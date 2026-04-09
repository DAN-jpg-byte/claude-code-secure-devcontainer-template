#!/usr/bin/env bash
# ==========================================
# Xvfb + x11vnc + websockify(noVNC)
# postStart で起動し、Selenium のウィンドウをブラウザから確認できるようにする
# ==========================================
set -euo pipefail

export DISPLAY="${DISPLAY:-:99}"

LOGDIR="${HOME}/.cache/novnc-logs"
mkdir -p "${LOGDIR}"

# noVNC の静的ファイル（--web は vnc.html を含むディレクトリ）
NOVNC_WEB="/usr/share/novnc"

# websockify の実体（PATH に無いイメージ向けに python モジュールも試す）
resolve_websockify() {
  if command -v websockify >/dev/null 2>&1; then
    echo "websockify"
    return 0
  fi
  if python3 -c "import websockify" >/dev/null 2>&1; then
    echo "python3 -m websockify"
    return 0
  fi
  return 1
}

# Xvfb :99（ソケットが無ければ起動）
if [[ ! -S /tmp/.X11-unix/X99 ]]; then
  # -ac: ホストベース認可を無効（コンテナ内ローカル用途）
  Xvfb :99 -screen 0 1920x1080x24 -ac +extension RANDR >>"${LOGDIR}/xvfb.log" 2>&1 &
  for _ in $(seq 1 100); do
    [[ -S /tmp/.X11-unix/X99 ]] && break
    sleep 0.05
  done
  if [[ ! -S /tmp/.X11-unix/X99 ]]; then
    echo "start-novnc: Xvfb の起動待ちがタイムアウトしました。${LOGDIR}/xvfb.log を確認してください。" >&2
    exit 1
  fi
fi

# VNC はループバックのみ（5900 はホストに公開しない想定）。認証は当面なし（要件 Step 0）
if ! ss -ltn 2>/dev/null | grep -qE ':5900\b'; then
  x11vnc -display :99 -forever -shared -rfbport 5900 -localhost -nopw -bg -o "${LOGDIR}/x11vnc.log"
fi
for _ in $(seq 1 40); do
  ss -ltn 2>/dev/null | grep -qE ':5900\b' && break
  sleep 0.05
done
if ! ss -ltn 2>/dev/null | grep -qE ':5900\b'; then
  echo "start-novnc: 5900 が待ち受けになっていません。${LOGDIR}/x11vnc.log を確認してください。" >&2
  tail -40 "${LOGDIR}/x11vnc.log" >&2 || true
  exit 1
fi

# noVNC: Dev Container のポート転送は 0.0.0.0 待ち受けが必要なことがある（ホスト側はエディタ経由で localhost）
if ! ss -ltn 2>/dev/null | grep -qE ':6080\b'; then
  if ! WS_CMD=$(resolve_websockify); then
    echo "start-novnc: websockify が見つかりません。.devcontainer の Dockerfile で novnc/websockify を入れたうえで Rebuild Container してください。" >&2
    exit 1
  fi
  # shellcheck disable=SC2086
  nohup ${WS_CMD} --web="${NOVNC_WEB}" 0.0.0.0:6080 127.0.0.1:5900 >>"${LOGDIR}/websockify.log" 2>&1 &
  disown || true
  for _ in $(seq 1 50); do
    ss -ltn 2>/dev/null | grep -qE ':6080\b' && break
    sleep 0.1
  done
  if ! ss -ltn 2>/dev/null | grep -qE ':6080\b'; then
    echo "start-novnc: 6080 が待ち受けになっていません。${LOGDIR}/websockify.log を確認してください。" >&2
    tail -40 "${LOGDIR}/websockify.log" >&2 || true
    exit 1
  fi
fi

echo "noVNC: ブラウザで vnc.html を開く（ポート転送後）例: http://127.0.0.1:6080/vnc.html"
