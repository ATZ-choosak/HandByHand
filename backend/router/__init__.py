from . import root

def init_router(app):
    app.include_router(root.router)
