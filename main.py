import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    api = os.getenv("POLYGON_API_KEY", "")
    print("Hello, fresh trading-bot 👋")
    print("POLYGON_API_KEY:", "set" if api else "missing")

if __name__ == "__main__":
    main()
