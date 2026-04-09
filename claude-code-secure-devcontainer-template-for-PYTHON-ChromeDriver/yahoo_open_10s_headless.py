#!/usr/bin/env python3
"""Yahoo! JAPAN を常にヘッドレスで開き、待って終了する（DISPLAY / noVNC 不要）。"""

import os
import shutil
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

WAIT_SEC = 10
URL = "https://www.yahoo.co.jp"

chromium = os.environ.get("CHROMIUM_BINARY") or shutil.which("chromium") or "/usr/bin/chromium"
driver_bin = os.environ.get("CHROMEDRIVER_PATH") or shutil.which("chromedriver") or "/usr/bin/chromedriver"

opts = Options()
opts.binary_location = chromium
opts.add_argument("--headless=new")
for arg in ("--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"):
    opts.add_argument(arg)
if os.environ.get("SELENIUM_INSECURE_TLS", "").lower() in ("1", "true", "yes"):
    opts.add_argument("--ignore-certificate-errors")

with webdriver.Chrome(service=Service(driver_bin), options=opts) as driver:
    driver.set_page_load_timeout(60)
    driver.get(URL)

    title = (driver.title or "").strip()
    print("url:", URL, flush=True)
    print("title:", title if title else "(空)", flush=True)

    # 本文の先頭だけ（長すぎるので切る）
    try:
        body = driver.find_element(By.TAG_NAME, "body").text
        snippet = " ".join(body.split())[:400]
        print("body_snippet:", snippet + ("…" if len(body) > 400 else ""), flush=True)
    except Exception as e:
        print("body_snippet: (取得できず)", repr(e), flush=True)

    time.sleep(WAIT_SEC)
