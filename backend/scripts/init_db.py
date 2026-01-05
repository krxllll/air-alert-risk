from app.db import init_db

def main() -> None:
    init_db()
    print("[db] init_db done")

if __name__ == "__main__":
    main()
