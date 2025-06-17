"""
Admin Routes - Complete Working Implementation for SyncAI
"""

import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
import time
import os

logger = logging.getLogger("admin_routes")
router = APIRouter(prefix="/admin", tags=["admin"])

def get_config_loader(request: Request):
    """Get config loader from app state"""
    if not hasattr(request.app.state, 'config_loader'):
        raise HTTPException(status_code=503, detail="Configuration not available")
    return request.app.state.config_loader

def get_agent_registry(request: Request):
    """Get agent registry from app state"""
    if not hasattr(request.app.state, 'agent_registry'):
        raise HTTPException(status_code=503, detail="Agent registry not available")
    return request.app.state.agent_registry

class SystemStatus(BaseModel):
    """System status response model"""
    status: str
    timestamp: str
    uptime_seconds: float
    version: str
    environment: str

class ConfigReloadRequest(BaseModel):
    """Configuration reload request model"""
    force: bool = False

@router.get("/status")
async def get_admin_status(request: Request):
    """Get comprehensive admin and system status"""
    try:
        # Get basic system info
        start_time = getattr(request.app.state, 'start_time', time.time())
        uptime = time.time() - start_time
        
        # Get config loader
        try:
            config_loader = get_config_loader(request)
            config_summary = config_loader.get_config_summary()
            config_valid = config_summary.get("validation", {}).get("valid", False)
        except Exception as e:
            logger.warning(f"Config loader not available: {e}")
            config_summary = {"error": "Config loader not available"}
            config_valid = False
        
        # Get agent registry status
        try:
            agent_registry = get_agent_registry(request)
            registry_status = agent_registry.get_status()
        except Exception as e:
            logger.warning(f"Agent registry not available: {e}")
            registry_status = {"error": "Agent registry not available"}
        
        # Get registered agents
        registered_agents = getattr(request.app.state, 'registered_agents', {})
        
        # Get SyncAI status
        sync_search_available = hasattr(request.app.state, 'sync_search_agent') and request.app.state.sync_search_agent is not None
        
        return {
            "service": "SyncAI Admin",
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime,
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "system_health": {
                "config_valid": config_valid,
                "agents_registered": len(registered_agents),
                "sync_search_available": sync_search_available,
                "registry_operational": "error" not in registry_status
            },
            "configuration": config_summary,
            "agent_registry": registry_status,
            "registered_agents": list(registered_agents.keys()),
            "capabilities": [
                "System monitoring",
                "Configuration management", 
                "Agent lifecycle management",
                "Health checks",
                "Status reporting"
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get admin status: {e}")
        return {
            "service": "SyncAI Admin",
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/health")
async def health_check(request: Request):
    """Comprehensive health check endpoint"""
    health_status = {
        "healthy": True,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check configuration
    try:
        config_loader = get_config_loader(request)
        validation = config_loader.validate_config()
        health_status["checks"]["configuration"] = {
            "healthy": validation["valid"],
            "warnings": validation.get("warnings", []),
            "errors": validation.get("errors", [])
        }
        if not validation["valid"]:
            health_status["healthy"] = False
    except Exception as e:
        health_status["checks"]["configuration"] = {
            "healthy": False,
            "error": str(e)
        }
        health_status["healthy"] = False
    
    # Check agent registry
    try:
        agent_registry = get_agent_registry(request)
        registry_status = agent_registry.get_status()
        health_status["checks"]["agent_registry"] = {
            "healthy": True,
            "registered_agents": registry_status.get("registered_agents", 0),
            "active_sessions": registry_status.get("active_sessions", 0)
        }
    except Exception as e:
        health_status["checks"]["agent_registry"] = {
            "healthy": False,
            "error": str(e)
        }
        health_status["healthy"] = False
    
    # Check LlamaStack connectivity
    try:
        if hasattr(request.app.state, 'client'):
            # Try a simple health check to LlamaStack
            health_status["checks"]["llamastack"] = {
                "healthy": True,
                "note": "Client available"
            }
        else:
            health_status["checks"]["llamastack"] = {
                "healthy": False,
                "error": "LlamaStack client not available"
            }
            health_status["healthy"] = False
    except Exception as e:
        health_status["checks"]["llamastack"] = {
            "healthy": False,
            "error": str(e)
        }
        health_status["healthy"] = False
    
    # Check SyncAI Search Agent
    try:
        if hasattr(request.app.state, 'sync_search_agent') and request.app.state.sync_search_agent:
            health_status["checks"]["sync_search"] = {
                "healthy": True,
                "agent_available": True
            }
        else:
            health_status["checks"]["sync_search"] = {
                "healthy": True,  # Not critical for overall health
                "agent_available": False,
                "note": "SyncAI Search agent not configured"
            }
    except Exception as e:
        health_status["checks"]["sync_search"] = {
            "healthy": False,
            "error": str(e)
        }
    
    # Overall health status
    if health_status["healthy"]:
        return health_status
    else:
        raise HTTPException(status_code=503, detail=health_status)

@router.post("/config/reload")
async def reload_configuration(
    request: ConfigReloadRequest,
    config_loader = Depends(get_config_loader)
):
    """Reload configuration from file"""
    try:
        logger.info(f"Reloading configuration (force: {request.force})")
        
        success = config_loader.reload_config()
        
        if success:
            # Get updated summary
            config_summary = config_loader.get_config_summary()
            
            return {
                "success": True,
                "message": "Configuration reloaded successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "config_summary": config_summary,
                "note": "Some changes may require application restart to take effect"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to reload configuration"
            )
    except Exception as e:
        logger.error(f"Configuration reload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Configuration reload failed: {str(e)}"
        )

@router.get("/config/validate")
async def validate_configuration(config_loader = Depends(get_config_loader)):
    """Validate current configuration"""
    try:
        validation = config_loader.validate_config()
        
        return {
            "validation": validation,
            "timestamp": datetime.utcnow().isoformat(),
            "config_summary": config_loader.get_config_summary()
        }
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Configuration validation failed: {str(e)}"
        )

@router.get("/agents")
async def list_agents(request: Request):
    """List all registered agents"""
    try:
        registered_agents = getattr(request.app.state, 'registered_agents', {})
        
        # Get detailed agent information
        agent_details = {}
        for agent_name, agent_info in registered_agents.items():
            agent_details[agent_name] = {
                "agent_id": agent_info.get("agent_id"),
                "session_id": agent_info.get("session_id"),
                "status": "active",
                "config": {
                    "model": agent_info.get("config", {}).get("model"),
                    "tools": agent_info.get("config", {}).get("tools", []),
                    "name": agent_info.get("config", {}).get("name")
                }
            }
        
        return {
            "agents": agent_details,
            "total_count": len(agent_details),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list agents: {str(e)}"
        )

@router.get("/agents/{agent_name}")
async def get_agent_details(agent_name: str, request: Request):
    """Get detailed information about a specific agent"""
    try:
        registered_agents = getattr(request.app.state, 'registered_agents', {})
        
        if agent_name not in registered_agents:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{agent_name}' not found"
            )
        
        agent_info = registered_agents[agent_name]
        
        return {
            "agent_name": agent_name,
            "agent_id": agent_info.get("agent_id"),
            "session_id": agent_info.get("session_id"),
            "status": "active",
            "configuration": agent_info.get("config", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent details for {agent_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent details: {str(e)}"
        )

@router.get("/system/info")
async def get_system_info():
    """Get system information"""
    try:
        import platform
        import sys
        
        return {
            "system": {
                "platform": platform.platform(),
                "python_version": sys.version,
                "architecture": platform.architecture(),
                "processor": platform.processor(),
                "hostname": platform.node()
            },
            "environment": {
                "python_path": sys.executable,
                "working_directory": os.getcwd(),
                "environment_variables": {
                    "ENVIRONMENT": os.getenv("ENVIRONMENT", "not_set"),
                    "DEBUG": os.getenv("DEBUG", "not_set"),
                    "HOST": os.getenv("HOST", "not_set"),
                    "PORT": os.getenv("PORT", "not_set")
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system info: {str(e)}"
        )