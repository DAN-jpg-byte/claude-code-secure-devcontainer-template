#!/usr/bin/env python3
"""
Chromium + chromedriver の最小動作確認（コンテナ内・ヘッドレス）。
Step 3（noVNC）以降は仮想ディスプレイ上の通常起動に切り替える想定。
"""

import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def main() -> None:
    # 環境変数で上書き可能（固定パス運用のデフォルト）
    chromium_bin = os.environ.get("CHROMIUM_BINARY", "/usr/bin/chromium")
    driver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    test_url = os.environ.get("SELENIUM_TEST_URL", "https://example.com")

    options = Options()
    options.binary_location = chromium_bin
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    service = Service(driver_path)
    with webdriver.Chrome(service=service, options=options) as driver:
        driver.get(test_url)
        print("title:", driver.title)
        out = Path("/workspace/selenium_check.png")
        driver.save_screenshot(str(out))
        print("screenshot:", out)


if __name__ == "__main__":
    main()
