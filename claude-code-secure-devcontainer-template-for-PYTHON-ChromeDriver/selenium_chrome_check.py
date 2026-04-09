#!/usr/bin/env python3
"""
Chromium + chromedriver の最小動作確認（コンテナ内・ヘッドレス）。
Step 3（noVNC）以降は仮想ディスプレイ上の通常起動に切り替える想定。

デフォルト URL は HTTP（neverssl.com）にしている。
社内プロキシが HTTPS を独自CAで検査する環境でも、まず「ブラウザがページを開ける」ことまで確認しやすい。
HTTPS の本番相当確認は SELENIUM_TEST_URL と企業ルートCA（または検証専用の SELENIUM_INSECURE_TLS）で行う。
"""

import os
import shutil
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


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

    options = Options()
    options.binary_location = chromium_bin
    options.add_argument("--headless=new")
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

    service = Service(driver_path)
    with webdriver.Chrome(service=service, options=options) as driver:
        # UFW やプロキシで詰まったときに無限待ちしない（秒）
        driver.set_page_load_timeout(30)
        driver.get(test_url)
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
