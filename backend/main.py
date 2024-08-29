# ssl patch
from gevent import monkey

monkey.patch_all()

from fastapi import FastAPI
from contextlib import asynccontextmanager
from . import db
from . import router
from .core import config




@asynccontextmanager
async def lifespan(app : FastAPI):
    yield
    if db.engine is not None:
        await db.close_session()

def create_app(settings=None):
    if not settings:
        settings = config.get_settings()

    app = FastAPI(lifespan=lifespan)
    db.init_db(settings)
    app.include_router(router.get_router() , prefix="/api")

    return app

