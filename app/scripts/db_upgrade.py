from flask_migrate import upgrade
from app.main import app


def main():
    with app.app_context():
        upgrade()
        print("DB upgraded successfully")


if __name__ == "__main__":
    main()
