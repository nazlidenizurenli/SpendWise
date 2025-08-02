from fastapi import FastAPI
from app.routes import root, auth
from app.routes import transactions

app = FastAPI()

# Register routers
app.include_router(root.router)
app.include_router(auth.router)
app.include_router(transactions.router)
