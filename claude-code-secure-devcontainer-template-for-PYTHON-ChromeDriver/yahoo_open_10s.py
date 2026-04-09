#!/usr/bin/env python3
"""Yahoo! JAPAN を開いて一定時間待って閉じるだけの短いサンプル（Selenium + Chromium）。"""

import os
import shutil
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# 開く秒数（変えたいときはここだけ）
WAIT_SEC = 10
URL = "https://www.yahoo.co.jp"


def main() -> None:
    chromium = os.environ.get("CHROMIUM_BINARY") or shutil.which("chromium") or "/usr/bin/chromium"
    driver_path = os.environ.get("CHROMEDRIVER_PATH") or shutil.which("chromedriver") or "/usr/bin/chromedriver"

    opts = Options()
    opts.binary_location = chromium
    opts.page_load_strategy = "eager"
    for a in ("--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"):
        opts.add_argument(a)

    # DISPLAY があるときはウィンドウ表示（noVNC で見える）。SELENIUM_HEADLESS=1 でヘッドレス
    headless = os.environ.get("SELENIUM_HEADLESS", "").lower() in ("1", "true", "yes")
    if os.environ.get("DISPLAY") and not headless:
        os.environ.setdefault("DBUS_SESSION_BUS_ADDRESS", "/dev/null")
        opts.add_argument("--window-size=1280,800")
    else:
        opts.add_argument("--headless=new")

    if os.environ.get("SELENIUM_INSECURE_TLS", "").lower() in ("1", "true", "yes"):
        opts.add_argument("--ignore-certificate-errors")

    with webdriver.Chrome(service=Service(driver_path), options=opts) as driver:
        driver.set_page_load_timeout(60)
        driver.get(URL)
        time.sleep(WAIT_SEC)


if __name__ == "__main__":
    main()
