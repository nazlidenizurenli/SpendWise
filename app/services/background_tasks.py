import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.services.budget import BudgetService

logger = logging.getLogger(__name__)


class BudgetStatusManager:
    """Background task manager for automatic budget status updates"""
    
    def __init__(self):
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the background task for budget status updates"""
        if self.is_running:
            logger.warning("Budget status manager is already running")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._run_budget_status_updates())
        logger.info("Budget status manager started")
    
    async def stop(self):
        """Stop the background task"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Budget status manager stopped")
    
    async def _run_budget_status_updates(self):
        """Main loop for budget status updates"""
        while self.is_running:
            try:
                await self._update_all_budget_statuses()
                
                # Wait for 1 hour before next update
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Error in budget status update loop: {e}")
                # Wait 5 minutes before retrying on error
                await asyncio.sleep(300)
    
    async def _update_all_budget_statuses(self):
        """Update all budget statuses"""
        try:
            # Get database session
            db = next(get_db())
            budget_service = BudgetService(db)
            
            # Update all budget statuses
            updated_count = budget_service.update_all_budget_statuses()
            
            if updated_count > 0:
                logger.info(f"Updated {updated_count} budget statuses")
            else:
                logger.debug("No budget statuses needed updating")
                
        except Exception as e:
            logger.error(f"Error updating budget statuses: {e}")
        finally:
            db.close()
    
    async def trigger_manual_update(self) -> int:
        """Manually trigger a budget status update"""
        try:
            db = next(get_db())
            budget_service = BudgetService(db)
            updated_count = budget_service.update_all_budget_statuses()
            db.close()
            return updated_count
        except Exception as e:
            logger.error(f"Error in manual budget status update: {e}")
            return 0


# Global instance
budget_status_manager = BudgetStatusManager()


async def start_budget_status_manager():
    """Start the budget status manager (called on app startup)"""
    await budget_status_manager.start()


async def stop_budget_status_manager():
    """Stop the budget status manager (called on app shutdown)"""
    await budget_status_manager.stop()


async def trigger_budget_status_update() -> int:
    """Trigger a manual budget status update"""
    return await budget_status_manager.trigger_manual_update()
