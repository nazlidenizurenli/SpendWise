from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, root, transactions, upload, budget, leaderboards, insights
from app.services.background_tasks import start_budget_status_manager, stop_budget_status_manager

app = FastAPI(title="SpendWise API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(root.router)
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(upload.router)
app.include_router(budget.router)
app.include_router(leaderboards.router)
app.include_router(insights.router)



@app.on_event("startup")
async def startup_event():
    """Startup event - start background tasks"""
    await start_budget_status_manager()


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event - stop background tasks"""
    await stop_budget_status_manager()
