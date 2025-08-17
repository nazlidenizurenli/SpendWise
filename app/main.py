from fastapi import FastAPI
from app.routes import root, auth
from app.routes import transactions
from app.routes import upload

app = FastAPI()

# Register routers
app.include_router(root.router)
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(upload.router)
