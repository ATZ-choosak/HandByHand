from fastapi import APIRouter
from . import root
from . import item
from . import auth
from . import user  # import the user router
from . import exchange
from . import chat

router = APIRouter()

def init_router_root(app):
    app.include_router(root.router, tags=["Main"])

# Include Routers
router.include_router(item.router, prefix="/items", tags=["Items"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(user.router, prefix="/users", tags=["Users"])  # include the user router
router.include_router(exchange.router, prefix="/exchanges", tags=["Exchanges"])
router.include_router(chat.router, prefix="/chats", tags=["Chats"])
def get_router():
    return router
