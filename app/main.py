from fastapi import FastAPI
from app.routes import root, auth

app = FastAPI()

# Register routers
app.include_router(root.router)
app.include_router(auth.router, prefix="/auth")
