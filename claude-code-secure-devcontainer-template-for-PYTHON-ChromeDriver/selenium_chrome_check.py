#!/usr/bin/env python3
"""
Chromium + chromedriver の最小動作確認（コンテナ内・ヘッドレス）。
Step 3（noVNC）以降は仮想ディスプレイ上の通常起動に切り替える想定。

デフォルト URL は HTTP（neverssl.com）にしている。
社内プロキシが HTTPS を独自CAで検査する環境でも、まず「ブラウザがページを開ける」ことまで確認しやすい。
HTTPS の本番相当確認は SELENIUM_TEST_URL と企業ルートCA（または検証専用の SELENIUM_INSECURE_TLS）で行う。

環境変数（任意）:
- SELENIUM_HEADLESS=1 … DISPLAY があってもヘッドレスにし、起動・描画を軽くする（noVNC には映らない）
- SELENIUM_PAGE_LOAD_STRATEGY … normal / eager / none（既定 eager。外部ページの「完全読み込み待ち」を減らす）
- SELENIUM_GET_RETRIES … driver.get の最大試行回数（既定 4）
- SELENIUM_GET_RETRY_PAUSE_SEC … 再試行の待ち秒（既定 2）
"""

import os
import shutil
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def _navigate_with_retry(driver, url: str, *, attempts: int, pause_sec: float) -> None:
    """ネットワークや初回起動のブレで落ちるときに数回だけ繰り返す。"""
    for i in range(attempts):
        try:
            driver.get(url)
            return
        except (TimeoutException, WebDriverException) as e:
            msg = str(e).lower()
            retryable = any(
                s in msg
                for s in (
                    "err_connection",
                    "timeout",
                    "renderer",
                    "disconnected",
                    "invalid session",
                )
            )
            if not retryable or i == attempts - 1:
                raise
            print(f"ナビゲーション再試行 {i + 1}/{attempts}: {e!r}")
            time.sleep(pause_sec)


def main() -> None:
    # 環境変数で上書き可能。未指定時は代表的な配置候補から自動検出する
    chromium_bin = os.environ.get("CHROMIUM_BINARY")
    if not chromium_bin:
        chromium_bin = shutil.which("chromium") or shutil.which("chromium-browser")
        if not chromium_bin:
            for candidate in ("/usr/bin/chromium", "/usr/bin/chromium-browser"):
                if Path(candidate).is_file():
                    chromium_bin = candidate
                    break

    driver_path = os.environ.get("CHROMEDRIVER_PATH")
    if not driver_path:
        driver_path = shutil.which("chromedriver")
        if not driver_path:
            for candidate in (
                "/usr/bin/chromedriver",
                "/usr/lib/chromium/chromedriver",
                "/usr/lib/chromium-browser/chromedriver",
            ):
                if Path(candidate).is_file():
                    driver_path = candidate
                    break

    if not chromium_bin:
        raise RuntimeError(
            "Chromium binary が見つかりません。CHROMIUM_BINARY を指定してください。"
        )
    if not driver_path:
        raise RuntimeError(
            "chromedriver が見つかりません。CHROMEDRIVER_PATH を指定してください。"
        )

    # 既定は TLS を挟まない HTTP（プロキシ環境でのスモークテスト向け）
    test_url = os.environ.get("SELENIUM_TEST_URL", "http://neverssl.com")

    # 社内プロキシ等で独自CAのみ信頼される場合の動作確認用（本番ターゲットでは使わない）
    insecure_tls = os.environ.get("SELENIUM_INSECURE_TLS", "").lower() in (
        "1",
        "true",
        "yes",
    )

    force_headless = os.environ.get("SELENIUM_HEADLESS", "").lower() in (
        "1",
        "true",
        "yes",
    )
    use_display = bool(os.environ.get("DISPLAY")) and not force_headless

    # ページ読み込み待ち: eager で DOM 操作可能になった時点で進む（完全読み込み待ちによる遅延・不安定さを減らす）
    pls = os.environ.get("SELENIUM_PAGE_LOAD_STRATEGY", "eager").strip().lower()
    if pls not in ("normal", "eager", "none"):
        pls = "eager"

    get_retries = int(os.environ.get("SELENIUM_GET_RETRIES", "4"))
    get_retries = max(1, min(get_retries, 10))
    retry_pause = float(os.environ.get("SELENIUM_GET_RETRY_PAUSE_SEC", "2"))

    # 仮想ディスプレイ＋コンテナでは D-Bus が無くレンダラがタイムアウトすることがある
    if use_display:
        os.environ.setdefault("DBUS_SESSION_BUS_ADDRESS", "/dev/null")

    options = Options()
    options.binary_location = chromium_bin
    options.page_load_strategy = pls
    # DISPLAY が付いているときはウィンドウ表示（noVNC の :99 で確認）。無いときだけヘッドレス
    if not use_display:
        options.add_argument("--headless=new")
    else:
        options.add_argument("--window-size=1280,800")
        # Xvfb 上でレンダラが固まりにくくする（Timed out receiving message from renderer 対策）
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-gpu-sandbox")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    if insecure_tls:
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--allow-insecure-localhost")

    print("chromium:", chromium_bin)
    print("chromedriver:", driver_path)
    print("test_url:", test_url)
    print("SELENIUM_INSECURE_TLS:", insecure_tls)
    print("use_display (noVNC 向けウィンドウ):", use_display)
    print("page_load_strategy:", pls)
    print("get_retries:", get_retries)

    service = Service(driver_path)
    with webdriver.Chrome(service=service, options=options) as driver:
        # UFW やプロキシで詰まったときに無限待ちしない（秒）
        # ウィンドウ表示は初回起動が重く、レンダラ応答も遅れがちなので長めに取る
        driver.set_page_load_timeout(90 if use_display else 45)
        # 初回の子プロセス・GPU/レンダラ立ち上げを安定させる
        driver.get("about:blank")
        time.sleep(0.5)
        _navigate_with_retry(
            driver,
            test_url,
            attempts=get_retries,
            pause_sec=retry_pause,
        )
        title = driver.title
        print("title:", title)
        if "privacy" in title.lower() or "not private" in title.lower():
            print(
                "ヒント: 証明書が信頼されていません（多くは社内プロキシの TLS 検査）。"
                " HTTPS 確認はコンテナに企業ルートCAを追加するか、"
                " 検証専用に SELENIUM_INSECURE_TLS=1 を付けてください。"
            )
        out = Path("/workspace/selenium_check.png")
        driver.save_screenshot(str(out))
        print("screenshot:", out)


if __name__ == "__main__":
    main()
