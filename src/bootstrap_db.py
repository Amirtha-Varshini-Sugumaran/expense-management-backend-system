from src.db import engine, Base
from src import models  # noqa: F401  (loads Expense model so Base knows it)

def main():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")

if __name__ == "__main__":
    main()
