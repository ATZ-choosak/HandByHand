from fastapi import APIRouter
from . import root
from . import item

router = APIRouter()

router.include_router(root.router , prefix="" , tags=["Main"])
router.include_router(item.router , prefix="/items" , tags=["Items"])


def get_router():
    return router