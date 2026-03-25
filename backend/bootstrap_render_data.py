from app import models  # noqa: F401
from app.db.base import Base
from app.db.session import engine
from app.services.bootstrap_data import ensure_bootstrap_data


def run() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_bootstrap_data()
    print('Render bootstrap completed.')


if __name__ == '__main__':
    run()
