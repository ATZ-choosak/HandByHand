# ssl patch
import os
# from gevent import monkey
# monkey.patch_all()

import socketio

from fastapi import FastAPI
from contextlib import asynccontextmanager
from . import db
from . import router
from .core import config
from .db import mongodb
from fastapi.staticfiles import StaticFiles
from .socket_events import sio

# ใช้ async context manager สำหรับจัดการ lifespan ของแอป
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if db.engine is not None:
        await db.close_session()

def create_images_directory_if_not_exists():
    images_directory = "images"
    
    if not os.path.exists(images_directory):
        print(f"Creating directory: {images_directory}")
        os.makedirs(images_directory)
    else:
        print(f"Directory {images_directory} already exists")
# ฟังก์ชันสร้างแอป
def create_app(settings=None):
    if not settings:
        settings = config.get_settings()

    app = FastAPI(lifespan=lifespan)

    # เริ่มต้นการเชื่อมต่อกับฐานข้อมูล
    db.init_db(settings)
    router.init_router_root(app)
    app.include_router(router.get_router(), prefix="/api")
    # Create images directory
    create_images_directory_if_not_exists()
    # เริ่มต้น MongoDB
    mongodb.init_mongoDB(settings)
    app.mount("/images", StaticFiles(directory="images"), name="images")
    
    app_socket = socketio.ASGIApp(sio, app)

    return app_socket

