import asyncio
from backend import db
from backend.core import config

if __name__ == "__main__":
    settings = config.get_settings()
    print(settings)
    db.init_db(settings)
    asyncio.run(db.recreate_table())