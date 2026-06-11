from app.database import SessionLocal, init_db
from app.services.seed_data import seed


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()

