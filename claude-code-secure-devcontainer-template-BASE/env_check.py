import os
import sys


def main() -> int:
    # 必須環境変数をここで定義
    required_vars = [
        "PASSWORD",

    ]

    missing = [name for name in required_vars if not os.getenv(name)]
    if missing:
        print("必須環境変数が不足しています:", ", ".join(missing))
        return 1

    # 値の先頭だけを表示して、フルシークレットは出さない
    for name in required_vars:
        value = os.getenv(name, "")
        masked = f"{value[:4]}..." if len(value) > 4 else "***"
        print(f"{name} = {masked}")

    print("環境変数の読み取りに成功しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
