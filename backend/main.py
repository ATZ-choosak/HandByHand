# ssl patch
from gevent import monkey
monkey.patch_all()

from fastapi import FastAPI
from contextlib import asynccontextmanager
from . import db
from . import router
from .core import config
from .db import mongodb

# ใช้ async context manager สำหรับจัดการ lifespan ของแอป
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if db.engine is not None:
        await db.close_session()

# ฟังก์ชันสร้างแอป
def create_app(settings=None):
    if not settings:
        settings = config.get_settings()

    app = FastAPI(lifespan=lifespan)

    # เริ่มต้นการเชื่อมต่อกับฐานข้อมูล
    db.init_db(settings)
    router.init_router_root(app)
    app.include_router(router.get_router(), prefix="/api")

    # เริ่มต้น MongoDB
    mongodb.init_mongoDB(settings)

    

    return app
