from src import models  # noqa: F401
from src.db import Base, engine


def main():
    Base.metadata.create_all(bind=engine)
    print("Tables created")


if __name__ == "__main__":
    main()
