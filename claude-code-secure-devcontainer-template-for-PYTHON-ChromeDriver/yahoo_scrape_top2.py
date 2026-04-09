#!/usr/bin/env python3
"""
Yahoo! JAPAN トップ（yahoo.co.jp）から、画面上部付近のニュース記事リンクを2件拾い、
各記事ページの見出しと本文テキスト（抜粋）を表示するサンプル。

注意:
- 利用規約・robots.txt・著作権を確認し、学習・個人検証の範囲で使うこと。
- 短時間に大量アクセスしないこと。
- Yahoo 側の HTML が変わるとセレクタが合わなくなることがある。
"""

from __future__ import annotations

import json
import os
import re
import shutil
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TOP_URL = "https://www.yahoo.co.jp"
MAX_ARTICLES = 2
# 記事らしい news.yahoo.co.jp のパス（トップのカテゴリ一覧などは除外しやすくする）
_ARTICLE_PATH_HINTS = ("/articles/", "/pickup/", "/byline/", "/exclusive/", "/story/", "/commentary/")


def _resolve_chromium_paths() -> tuple[str, str]:
    chromium = os.environ.get("CHROMIUM_BINARY") or shutil.which("chromium") or "/usr/bin/chromium"
    driver_path = os.environ.get("CHROMEDRIVER_PATH") or shutil.which("chromedriver") or "/usr/bin/chromedriver"
    return chromium, driver_path


def _build_options(chromium: str) -> Options:
    opts = Options()
    opts.binary_location = chromium
    opts.page_load_strategy = "eager"
    for a in ("--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"):
        opts.add_argument(a)

    headless = os.environ.get("SELENIUM_HEADLESS", "").lower() in ("1", "true", "yes")
    if os.environ.get("DISPLAY") and not headless:
        os.environ.setdefault("DBUS_SESSION_BUS_ADDRESS", "/dev/null")
        opts.add_argument("--window-size=1280,800")
        for a in (
            "--disable-setuid-sandbox",
            "--disable-gpu-sandbox",
            "--disable-software-rasterizer",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-extensions",
        ):
            opts.add_argument(a)
    else:
        opts.add_argument("--headless=new")

    if os.environ.get("SELENIUM_INSECURE_TLS", "").lower() in ("1", "true", "yes"):
        opts.add_argument("--ignore-certificate-errors")

    return opts


def _normalize_href(base_url: str, href: str | None) -> str | None:
    if not href or href.startswith("#") or href.startswith("javascript:"):
        return None
    full = urljoin(base_url, href)
    parsed = urlparse(full)
    if parsed.scheme not in ("http", "https"):
        return None
    return full.split("#")[0]


def _is_yahoo_news_article_url(url: str) -> bool:
    host = urlparse(url).netloc
    if "news.yahoo.co.jp" not in host:
        return False
    path = urlparse(url).path
    if not any(h in path for h in _ARTICLE_PATH_HINTS):
        return False
    # 一覧・カテゴリだけの URL をざっくり除外
    if re.search(r"/articles/?$", path):
        return False
    return True


def collect_top_article_urls(driver: webdriver.Chrome, base_url: str, limit: int) -> list[str]:
    """トップページ上の a タグから、先頭から limit 件の記事 URL を返す（出現順・重複なし）。"""
    seen: set[str] = set()
    out: list[str] = []
    for a in driver.find_elements(By.TAG_NAME, "a"):
        href = _normalize_href(base_url, a.get_attribute("href"))
        if not href or href in seen:
            continue
        if not _is_yahoo_news_article_url(href):
            continue
        seen.add(href)
        out.append(href)
        if len(out) >= limit:
            break
    return out


def extract_article_text(driver: webdriver.Chrome) -> tuple[str, str]:
    """記事ページから (title, body_excerpt) を取る。複数セレクタを試す。"""
    wait = WebDriverWait(driver, 20)

    def _title() -> str:
        for sel in (
            (By.CSS_SELECTOR, "h1"),
            (By.CSS_SELECTOR, 'meta[property="og:title"]'),
        ):
            try:
                el = wait.until(EC.presence_of_element_located(sel))
                t = el.get_attribute("content") if el.tag_name == "meta" else el.text
                t = (t or "").strip()
                if t:
                    return t
            except Exception:
                continue
        return ""

    def _body_excerpt(max_chars: int = 4000) -> str:
        # 記事本文っぽい段落を集める（サイト改修で変わりやすい）
        selectors = [
            "article p",
            "main p",
            '[class*="article"] p',
            ".pickupMain p",
        ]
        chunks: list[str] = []
        for sel in selectors:
            for p in driver.find_elements(By.CSS_SELECTOR, sel):
                t = (p.text or "").strip()
                if len(t) < 2:
                    continue
                if t in chunks:
                    continue
                chunks.append(t)
            if sum(len(c) for c in chunks) > 200:
                break
        text = "\n".join(chunks).strip()
        if len(text) > max_chars:
            text = text[:max_chars] + "\n…（省略）"
        return text

    title = _title()
    body = _body_excerpt()
    return title, body


def main() -> None:
    chromium, driver_path = _resolve_chromium_paths()
    opts = _build_options(chromium)

    results: list[dict[str, str]] = []

    with webdriver.Chrome(service=Service(driver_path), options=opts) as driver:
        driver.set_page_load_timeout(90)
        driver.get(TOP_URL)
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        urls = collect_top_article_urls(driver, TOP_URL, MAX_ARTICLES)
        if len(urls) < MAX_ARTICLES:
            print(
                f"警告: 記事 URL が {len(urls)} 件しか見つかりませんでした。"
                " HTML 変更や読み込み不足の可能性があります。",
                flush=True,
            )

        for i, url in enumerate(urls, start=1):
            driver.get(url)
            WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            title, body = extract_article_text(driver)
            results.append(
                {
                    "index": str(i),
                    "url": url,
                    "title": title,
                    "body": body,
                }
            )

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
