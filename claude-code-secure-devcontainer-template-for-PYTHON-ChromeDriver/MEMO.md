
**Step 1 は問題ありません。**  
（最初の `print(selenium.__version__)` はシェルに直接打っているのでエラーになりますが、`python -c "..."` のほうが正しいやり方です。）

---

**Step 2 をこちらで入れました。**

1. **`.devcontainer/Dockerfile`**  
   - `chromium` と `chromium-driver`（同じディストリの apt なので **バージョンはセットで揃う**）  
   - フォント用に `fonts-liberation`  
   - 方針どおり「固定」は **このイメージ＋その時点の apt** に依存する形です。

2. **`selenium_chrome_check.py`**（動作確認用）  
   - ヘッドレスで `https://example.com` を開き、タイトル表示と `/workspace/selenium_check.png` の保存まで行います。  
   - Step 3 で noVNC ＋通常起動に切り替える前提のコメントを入れています。

---

**あなたがやること**

1. **Rebuild Container**（Dockerfile 変更のため必須）  
2. コンテナ内で:

```bash
which chromium
which chromedriver
python /workspace/selenium_chrome_check.py
```

`title:` が出て `selenium_check.png` ができれば **Step 2 完了**です。  
エラーが出たら、そのログを貼ってください（パッケージ名の差し替えなどすぐ追います）。
