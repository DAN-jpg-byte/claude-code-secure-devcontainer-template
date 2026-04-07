import requests


def main() -> None:
    # 公開APIへGETリクエストを送る簡単な例
    url = "https://httpbin.org/get"
    params = {"q": "python", "page": 1}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"リクエストに失敗しました: {error}")
        return

    data = response.json()
    print("ステータスコード:", response.status_code)
    print("返ってきたURL:", data.get("url"))
    print("送信したクエリ:", data.get("args"))


if __name__ == "__main__":
    main()
