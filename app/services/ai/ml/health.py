"""
Enhanced Health Checks
Adds /health/ready and /health/live endpoints
Existing /health endpoint remains unchanged
"""
from fastapi import HTTPException
from typing import Dict, Any
import time
import os


class HealthChecker:
    """Comprehensive health checker"""
    
    def __init__(self, app_state):
        self.app_state = app_state
    
    async def check_health(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        checks = {
            "status": "healthy",
            "timestamp": time.time(),
            "checks": {}
        }
        
        # Vector store check
        checks["checks"]["vector_store"] = await self._check_vector_store()
        
        # Model check
        checks["checks"]["model"] = self._check_model()
        
        # FAISS index check
        checks["checks"]["faiss_index"] = self._check_faiss_index()
        
        # Disk space check
        checks["checks"]["disk_space"] = self._check_disk_space()
        
        # Memory check (optional, requires psutil)
        checks["checks"]["memory"] = self._check_memory()
        
        # Determine overall status
        all_healthy = all(
            check.get("status") == "healthy" 
            for check in checks["checks"].values()
        )
        checks["status"] = "healthy" if all_healthy else "degraded"
        
        return checks
    
    async def _check_vector_store(self) -> Dict[str, Any]:
        """Check vector store health"""
        try:
            vector_store = self.app_state.vector_store
            if vector_store is None:
                return {"status": "unhealthy", "message": "Vector store not initialized"}
            
            # Try a simple search
            results = await vector_store.search("test", top_k=1)
            vector_count = 0
            if hasattr(vector_store, 'faiss_index') and vector_store.faiss_index:
                vector_count = vector_store.faiss_index.ntotal
            
            return {
                "status": "healthy",
                "vector_count": vector_count
            }
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}
    
    def _check_model(self) -> Dict[str, Any]:
        """Check model health"""
        model = getattr(self.app_state, 'model', None)
        tokenizer = getattr(self.app_state, 'tokenizer', None)
        
        if model is None or tokenizer is None:
            return {"status": "degraded", "message": "Model not loaded (optional)"}
        
        try:
            import torch
            device = str(next(model.parameters()).device)
            return {"status": "healthy", "device": device}
        except Exception as e:
            return {"status": "degraded", "message": str(e)}
    
    def _check_faiss_index(self) -> Dict[str, Any]:
        """Check FAISS index health"""
        faiss_index = getattr(self.app_state, 'faiss_index', None)
        if faiss_index is None:
            return {"status": "degraded", "message": "FAISS index not loaded"}
        
        try:
            return {
                "status": "healthy",
                "vector_count": faiss_index.ntotal
            }
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_percent = (free / total) * 100
            
            if free_percent < 10:
                return {"status": "unhealthy", "free_percent": round(free_percent, 2)}
            elif free_percent < 20:
                return {"status": "degraded", "free_percent": round(free_percent, 2)}
            else:
                return {"status": "healthy", "free_percent": round(free_percent, 2)}
        except Exception as e:
            return {"status": "unknown", "message": str(e)}
    
    def _check_memory(self) -> Dict[str, Any]:
        """Check memory availability"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_percent = memory.available / memory.total * 100
            
            if available_percent < 10:
                return {"status": "unhealthy", "available_percent": round(available_percent, 2)}
            elif available_percent < 20:
                return {"status": "degraded", "available_percent": round(available_percent, 2)}
            else:
                return {"status": "healthy", "available_percent": round(available_percent, 2)}
        except ImportError:
            return {"status": "unknown", "message": "psutil not available"}
        except Exception as e:
            return {"status": "unknown", "message": str(e)}
