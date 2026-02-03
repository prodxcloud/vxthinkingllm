"""
Lifecycle Hooks
Background tasks for Model Cleanup and Health Check Probes
"""
import asyncio
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Model, ModelMetadata, ModelState

logger = logging.getLogger("vallm")


class ModelCleanupTask:
    """
    Background task for model cleanup
    Clears temp weights from GPU cache and manages model lifecycle
    """
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.running = False
        self.cleanup_interval = int(os.getenv("VALLM_CLEANUP_INTERVAL_SECONDS", "300"))  # 5 min
    
    async def start(self):
        """Start the cleanup task"""
        self.running = True
        logger.info("Model cleanup task started")
        
        while self.running:
            try:
                await self._cleanup_cycle()
                await asyncio.sleep(self.cleanup_interval)
            except Exception as e:
                logger.error(f"Error in model cleanup task: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    def stop(self):
        """Stop the cleanup task"""
        self.running = False
        logger.info("Model cleanup task stopped")
    
    async def _cleanup_cycle(self):
        """Execute one cleanup cycle"""
        try:
            db = SessionLocal()
            try:
                # Find models that need cleanup
                # 1. Soft-deleted models older than retention period
                retention_days = int(os.getenv("VALLM_DELETED_MODEL_RETENTION_DAYS", "30"))
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                
                deleted_models = db.query(Model).filter(
                    Model.is_deleted == True,
                    Model.deleted_at < cutoff_date
                ).all()
                
                for model in deleted_models:
                    await self._cleanup_model_weights(model)
                    logger.info(f"Cleaned up deleted model: {model.id}")
                
                # 2. Clear GPU cache for models not in use
                await self._clear_unused_gpu_cache(db)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Cleanup cycle error: {e}")
    
    async def _cleanup_model_weights(self, model: Model):
        """Clean up model weights from disk/GPU"""
        try:
            # Clear GPU cache if model is loaded
            if hasattr(self.app_state, 'model') and self.app_state.model:
                # Check if this is the model to clean
                # (In production, you'd track which model is loaded)
                pass
            
            # Optionally delete model files from disk
            # (Be careful - this is permanent!)
            model_path = model.model_path
            if os.path.exists(model_path) and os.getenv("VALLM_DELETE_MODEL_FILES", "false").lower() == "true":
                import shutil
                shutil.rmtree(model_path, ignore_errors=True)
                logger.info(f"Deleted model files: {model_path}")
        
        except Exception as e:
            logger.error(f"Error cleaning model weights for {model.id}: {e}")
    
    async def _clear_unused_gpu_cache(self, db: Session):
        """Clear GPU cache for models not currently in use"""
        try:
            import torch
            
            if not torch.cuda.is_available():
                return
            
            # Get currently active models (in production state)
            active_models = db.query(Model).filter(
                Model.state == ModelState.PRODUCTION,
                Model.is_deleted == False
            ).all()
            
            # If no production models, clear cache
            if not active_models:
                torch.cuda.empty_cache()
                logger.debug("Cleared GPU cache (no active models)")
            
        except ImportError:
            logger.debug("PyTorch not available for GPU cache management")
        except Exception as e:
            logger.error(f"Error clearing GPU cache: {e}")


class HealthCheckProbe:
    """
    Background task for health check probes
    Verifies if models are 'Warm' (loaded in memory) or 'Cold' (not loaded)
    """
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.running = False
        self.probe_interval = int(os.getenv("VALLM_HEALTH_PROBE_INTERVAL_SECONDS", "60"))  # 1 min
        self.model_status_cache: Dict[str, Dict[str, Any]] = {}
    
    async def start(self):
        """Start the health probe task"""
        self.running = True
        logger.info("Health check probe task started")
        
        while self.running:
            try:
                await self._probe_cycle()
                await asyncio.sleep(self.probe_interval)
            except Exception as e:
                logger.error(f"Error in health probe task: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    def stop(self):
        """Stop the health probe task"""
        self.running = False
        logger.info("Health check probe task stopped")
    
    async def _probe_cycle(self):
        """Execute one probe cycle"""
        try:
            db = SessionLocal()
            try:
                # Check production models
                production_models = db.query(Model).filter(
                    Model.state == ModelState.PRODUCTION,
                    Model.is_deleted == False
                ).all()
                
                for model in production_models:
                    status = await self._check_model_health(model)
                    self.model_status_cache[model.id] = status
                    
                    # Log if model is cold when it should be warm
                    if status["state"] == "cold" and status["should_be_warm"]:
                        logger.warning(
                            f"Model {model.id} ({model.alias}) is COLD but should be WARM"
                        )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Probe cycle error: {e}")
    
    async def _check_model_health(self, model: Model) -> Dict[str, Any]:
        """
        Check if model is Warm or Cold
        Returns status dict with state, load_time, etc.
        """
        status = {
            "model_id": model.id,
            "alias": model.alias,
            "state": "unknown",
            "should_be_warm": model.state == ModelState.PRODUCTION,
            "is_loaded": False,
            "load_time_ms": None,
            "memory_usage_mb": None,
            "checked_at": datetime.utcnow().isoformat()
        }
        
        try:
            # Check if model is loaded in app state
            app_model = getattr(self.app_state, 'model', None)
            app_tokenizer = getattr(self.app_state, 'tokenizer', None)
            
            if app_model is not None and app_tokenizer is not None:
                # Model is loaded - check if it's the right one
                # (In production, you'd track which model is loaded)
                status["is_loaded"] = True
                status["state"] = "warm"
                
                # Estimate memory usage
                try:
                    import torch
                    if torch.cuda.is_available() and hasattr(app_model, 'parameters'):
                        # Get GPU memory if on GPU
                        if next(app_model.parameters()).is_cuda:
                            memory_allocated = torch.cuda.memory_allocated() / (1024 ** 2)  # MB
                            status["memory_usage_mb"] = round(memory_allocated, 2)
                except:
                    pass
            else:
                status["is_loaded"] = False
                status["state"] = "cold"
            
            # Measure load time (if we were to load it)
            if status["state"] == "cold" and status["should_be_warm"]:
                # In production, you might pre-warm models here
                pass
            
        except Exception as e:
            logger.error(f"Error checking model health for {model.id}: {e}")
            status["state"] = "error"
            status["error"] = str(e)
        
        return status
    
    def get_model_status(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get cached model status"""
        return self.model_status_cache.get(model_id)
    
    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached model statuses"""
        return self.model_status_cache.copy()


# Global instances (will be initialized in app startup)
cleanup_task: Optional[ModelCleanupTask] = None
health_probe: Optional[HealthCheckProbe] = None


async def start_lifecycle_tasks(app_state):
    """Start all lifecycle background tasks"""
    global cleanup_task, health_probe
    
    cleanup_task = ModelCleanupTask(app_state)
    health_probe = HealthCheckProbe(app_state)
    
    # Start tasks in background
    asyncio.create_task(cleanup_task.start())
    asyncio.create_task(health_probe.start())
    
    logger.info("Lifecycle tasks started")


async def stop_lifecycle_tasks():
    """Stop all lifecycle background tasks"""
    global cleanup_task, health_probe
    
    if cleanup_task:
        cleanup_task.stop()
    if health_probe:
        health_probe.stop()
    
    logger.info("Lifecycle tasks stopped")
