#!/usr/bin/env bash
# postStart から呼ぶ。UFW → noVNC の順で実行し、Dev Containers ログとファイルに到達点を残す。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_verify() {
  local logdir="${HOME}/.cache/novnc-logs"
  mkdir -p "${logdir}"
  {
    echo "=== $(date -u +"%Y-%m-%dT%H:%M:%SZ") post-start verify (5900/6080) ==="
    ss -ltn 2>/dev/null | grep -E ':5900\b|:6080\b' || true
  } >>"${logdir}/poststart-verify.log"
}

echo "[devcontainer post-start] init-firewall.sh ..." >&2
bash "${SCRIPT_DIR}/init-firewall.sh"

echo "[devcontainer post-start] start-novnc.sh ..." >&2
bash "${SCRIPT_DIR}/start-novnc.sh"

log_verify
echo "[devcontainer post-start] 完了。listen 確認: ss -ltn | grep -E '5900|6080' または ${HOME}/.cache/novnc-logs/poststart-verify.log" >&2
