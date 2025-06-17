#!/usr/bin/env python3
"""
SyncAI API - Complete Working Implementation with Fixed Tavily Configuration
Professional intelligence platform for staying synchronized with technology developments
Updated for Single Agent Pattern with Working Web Search
"""

import logging
import os
import json
import uuid
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import route modules  
from routes.admin import router as admin_router
from routes.sync_search import router as sync_search_router
from routes.files import router as files_router
from routes.vector_db import router as vector_db_router

# Import agent management
from agents.agent import AgentManager
from config.config import ConfigLoader

# Import SyncAI search components
from agents.sync_search.persona_config_loader import PersonaConfigLoader
from agents.sync_search.sync_search_agent import SyncSearchAgent

# Import utilities
from routes.files import set_upload_dir
from routes.vector_db import set_vector_db_client

# LlamaStack imports
from llama_stack_client import LlamaStackClient
from llama_stack_client.types.agent_create_params import AgentConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("syncai_main")

class EnhancedConfigLoader(ConfigLoader):
    """Enhanced ConfigLoader with Tavily API key support"""
    
    def get_tavily_api_key(self) -> Optional[str]:
        """
        Get Tavily API key from configuration
        
        Returns:
            Tavily API key if configured, None otherwise
        """
        try:
            # Check in api_keys section
            api_keys = self.config.get("api_keys", {})
            tavily_key = api_keys.get("tavily_search_api_key")
            
            if tavily_key:
                # Validate the key format (Tavily keys start with 'tvly-')
                if not tavily_key.startswith('tvly-'):
                    logger.warning("⚠️ Tavily API key doesn't start with 'tvly-' - may be invalid")
                return tavily_key
            
            # Fallback: check root level (if someone puts it there)
            tavily_key = self.config.get("tavily_api_key")
            if tavily_key:
                return tavily_key
            
            # Check environment variables as fallback
            env_key = os.getenv("TAVILY_API_KEY") or os.getenv("TAVILY_SEARCH_API_KEY")
            if env_key:
                logger.info("🔑 Using Tavily API key from environment variable")
                return env_key
            
            logger.warning("⚠️ No Tavily API key found in configuration or environment")
            return None
            
        except Exception as e:
            logger.error(f" Error getting Tavily API key: {e}")
            return None

# Load configuration with enhanced loader
config_loader = EnhancedConfigLoader("config.yaml")
llamastack_base_url = config_loader.get_llamastack_base_url()
agents_config = config_loader.get_agents_config()

class AgentRegistry:
    """Complete Agent Registry - Prevents duplicates for ALL agents"""
    def __init__(self, client: LlamaStackClient):
        self.client = client
        self.agents = {}  # agent_name -> agent_id
        self.sessions = {}  # agent_name -> session_id
        self.agent_configs = {}  # agent_name -> config for comparison
        
    def get_existing_agent_by_name(self, agent_name: str) -> str:
        """Check if agent with this name already exists in LlamaStack"""
        try:
            if hasattr(self.client.agents, "list"):
                response = self.client.agents.list()
                agents_data = response.data if hasattr(response, 'data') else response
            else:
                import httpx
                response = httpx.get(f"{self.client.base_url}/v1/agents", timeout=30)
                response.raise_for_status()
                data = response.json()
                agents_data = data.get("data", [])
            
            for agent in agents_data:
                agent_config = agent.get("agent_config", {})
                existing_name = agent_config.get("name")
                
                if existing_name and existing_name == agent_name:
                    agent_id = agent.get("agent_id")
                    logger.info(f"🔍 Found existing agent: {agent_name} with ID: {agent_id}")
                    return agent_id
                    
        except Exception as e:
            logger.warning(f"Error checking existing agents: {e}")
        
        logger.info(f"🔍 No existing agent found for: {agent_name}")
        return None
    
    async def get_or_create_agent(self, agent_config_dict: dict) -> str:
        """Get or create agent with proper name handling - NO DUPLICATES"""
        agent_name = agent_config_dict["name"]
        
        if not agent_name or agent_name.lower() in ['none', 'null', '']:
            raise ValueError(f"Agent name cannot be None/empty: {agent_name}")
        
        # Check local registry first
        if agent_name in self.agents:
            logger.info(f"♻️ Reusing locally registered agent: {agent_name}")
            return self.agents[agent_name]
        
        # Check if agent exists in LlamaStack
        existing_agent_id = self.get_existing_agent_by_name(agent_name)
        if existing_agent_id:
            self.agents[agent_name] = existing_agent_id
            self.agent_configs[agent_name] = agent_config_dict
            logger.info(f"📝 Registered existing LlamaStack agent: {agent_name}")
            return existing_agent_id
        
        # Create new agent
        logger.info(f"🆕 Creating new agent: {agent_name}")
        
        agent_config = AgentConfig(
            name=agent_name,
            model=agent_config_dict["model"],
            instructions=agent_config_dict["instructions"],
            sampling_params=agent_config_dict.get("sampling_params"),
            max_infer_iters=agent_config_dict.get("max_infer_iters"),
            toolgroups=agent_config_dict.get("toolgroups", []),
            tools=agent_config_dict.get("tools", []),
            tool_config=agent_config_dict.get("tool_config"),
            enable_session_persistence=True,
        )
        
        try:
            response = self.client.agents.create(agent_config=agent_config)
            agent_id = response.agent_id
            
            self.agents[agent_name] = agent_id
            self.agent_configs[agent_name] = agent_config_dict
            
            logger.info(f" Created and registered new agent: {agent_name} with ID: {agent_id}")
            return agent_id
            
        except Exception as e:
            logger.error(f" Failed to create agent {agent_name}: {e}")
            raise
    
    def create_session(self, agent_name: str) -> str:
        """Create session for agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not registered")
            
        agent_id = self.agents[agent_name]
        
        if agent_name in self.sessions:
            logger.info(f"♻️ Reusing existing session for agent: {agent_name}")
            return self.sessions[agent_name]
        
        try:
            response = self.client.agents.session.create(
                agent_id=agent_id,
                session_name=f"Session-{agent_name}-{uuid.uuid4()}",
            )
            session_id = response.session_id
            self.sessions[agent_name] = session_id
            
            logger.info(f"📱 Created session {session_id} for agent: {agent_name}")
            return session_id
            
        except Exception as e:
            logger.error(f" Failed to create session for agent {agent_name}: {e}")
            raise
    
    def get_agent_id(self, agent_name: str) -> str:
        """Get agent ID by name"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not registered")
        return self.agents[agent_name]
    
    def get_session_id(self, agent_name: str) -> str:
        """Get session ID by agent name"""
        if agent_name not in self.sessions:
            return self.create_session(agent_name)
        return self.sessions[agent_name]
    
    def get_status(self) -> dict:
        """Get registry status"""
        return {
            "registered_agents": len(self.agents),
            "active_sessions": len(self.sessions),
            "agents": dict(self.agents),
            "sessions": dict(self.sessions)
        }

# Global registry instance
agent_registry = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_registry
    
    logger.info("🚀 Starting SyncAI API...")
    
    # Initialize single client and registry with ENHANCED Tavily configuration
    try:
        # Get Tavily API key from config with enhanced logging
        tavily_api_key = config_loader.get_tavily_api_key()
        provider_data = {"tavily_search_api_key": tavily_api_key} if tavily_api_key else None
        
        # ENHANCED DEBUG LOGGING
        logger.info(f"🔑 Tavily API Key loaded: {tavily_api_key[:10] + '...' if tavily_api_key else 'None'}")
        logger.info(f"🔗 Provider data configured: {bool(provider_data)}")
        if provider_data:
            logger.info(f"🔗 Provider data keys: {list(provider_data.keys())}")
        
        # Initialize LlamaStack client with Tavily configuration
        client = LlamaStackClient(
            base_url=llamastack_base_url,
            provider_data=provider_data
        )
        
        agent_registry = AgentRegistry(client)
        app.state.client = client
        app.state.agent_registry = agent_registry
        app.state.config_loader = config_loader
        
        logger.info(f"🔗 Connected to LlamaStack: {llamastack_base_url}")
        if tavily_api_key:
            logger.info("🔑 Tavily API key configured and passed to LlamaStack")
        else:
            logger.warning("⚠️ NO Tavily API key - web search will not work!")
            logger.warning("⚠️ Add tavily_search_api_key to your config.yaml under api_keys section")
            
    except Exception as e:
        logger.error(f" Failed to initialize LlamaStack client: {e}")
        raise

    # === Register ALL agents through AgentRegistry ===
    logger.info("🤖 Registering all agents...")
    
    registered_agents = {}
    
    for agent_config in agents_config:
        agent_name = agent_config["name"]
        logger.info(f"🔧 Setting up {agent_name} agent...")
        
        try:
            agent_id = await agent_registry.get_or_create_agent(agent_config)
            session_id = agent_registry.create_session(agent_name)
            
            registered_agents[agent_name] = {
                "agent_id": agent_id,
                "session_id": session_id,
                "config": agent_config
            }
            
            logger.info(f" {agent_name} agent ready: agent_id={agent_id}")
            
            # Special logging for sync_search agent
            if agent_name == "sync_search":
                tools = agent_config.get("tools", [])
                logger.info(f"🛠️ SyncSearch tools configured: {tools}")
                if "builtin::websearch" in tools:
                    logger.info("🌐 Web search tool configured")
                if any("rag" in str(tool).lower() for tool in tools):
                    logger.info("📚 RAG tool configured")
            
        except Exception as e:
            logger.error(f" Failed to setup {agent_name} agent: {e}")
            # Continue with other agents rather than failing completely
            continue

    app.state.registered_agents = registered_agents
    
    # Keep AgentManager for backward compatibility
    agent_manager = AgentManager(llamastack_base_url)
    app.state.agent_manager = agent_manager

    # === Setup SyncAI Search Agent (Single Agent Pattern) ===
    sync_search_agent_name = "sync_search"
    
    if sync_search_agent_name in registered_agents:
        try:
            # Load persona configuration
            persona_config_path = os.path.join("agents", "sync_search", "persona_config.yaml")
            if not os.path.exists(persona_config_path):
                logger.warning(f"⚠️ Persona config not found at {persona_config_path}, using default path")
                persona_config_path = "persona_config.yaml"
            
            persona_config_loader = PersonaConfigLoader(persona_config_path)
            
            # Initialize SyncAI Search Agent with SINGLE agent
            sync_search_agent = SyncSearchAgent(
                client=client,
                agent_id=registered_agents[sync_search_agent_name]["agent_id"],
                session_id=registered_agents[sync_search_agent_name]["session_id"],
                config_loader=persona_config_loader
            )
            
            app.state.sync_search_agent = sync_search_agent
            app.state.persona_config_loader = persona_config_loader
            
            logger.info(f"🔍 SyncAI Search Agent ready with {len(persona_config_loader.get_available_personas())} personas")
            logger.info(f"🤖 Single Agent: {registered_agents[sync_search_agent_name]['agent_id']}")
            logger.info(f"🛠️ Tools: builtin::websearch + builtin::rag")
            
            # Final web search status check
            sync_config = registered_agents[sync_search_agent_name]["config"]
            has_websearch = "builtin::websearch" in sync_config.get("tools", [])
            has_tavily = bool(tavily_api_key)
            
            if has_websearch and has_tavily:
                logger.info("🎉 Web search should be FULLY FUNCTIONAL!")
            elif has_websearch and not has_tavily:
                logger.warning("⚠️ Web search configured but NO Tavily API key - will not work")
            elif not has_websearch and has_tavily:
                logger.warning("⚠️ Tavily API key configured but no websearch tool - check agent config")
            else:
                logger.warning("⚠️ Neither web search tool nor Tavily API key configured")
            
        except Exception as e:
            logger.error(f" Failed to setup SyncAI Search Agent: {e}")
            logger.warning("⚠️ SyncAI Search functionality will be disabled")
            app.state.sync_search_agent = None
    else:
        logger.warning(f"⚠️ SyncAI Search agent '{sync_search_agent_name}' not found in config")
        app.state.sync_search_agent = None

    # === File and Vector DB setup ===
    
    # File upload directory
    upload_dir = config_loader.get_upload_dir()
    os.makedirs(upload_dir, exist_ok=True)
    set_upload_dir(upload_dir)
    logger.info(f"📁 File upload directory: {upload_dir}")

    # Vector DB client
    try:
        vector_config = config_loader.get_vector_db_config()
        default_db_id = vector_config.get("default_db_id", "ai_info")
        default_chunk_size = vector_config.get("default_chunk_size", 512)
        set_vector_db_client(
            injected_client=client,
            default_vector_db_id=default_db_id,
            default_chunk_size=default_chunk_size
        )
        logger.info(f"🗄️ Vector DB ready: {default_db_id}")
    except Exception as e:
        logger.warning(f"⚠️ Vector DB setup failed: {e}")

    logger.info(" SyncAI API startup complete")
    
    # FINAL STATUS SUMMARY
    logger.info("=" * 60)
    logger.info("🎯 SYNCAI STARTUP SUMMARY")
    logger.info("=" * 60)
    logger.info(f"📡 LlamaStack URL: {llamastack_base_url}")
    logger.info(f"🔑 Tavily API Key: {'Configured ' if tavily_api_key else 'Missing '}")
    logger.info(f"🤖 Agents Registered: {len(registered_agents)}")
    logger.info(f"🔍 SyncAI Search: {'Enabled ' if sync_search_agent_name in registered_agents else 'Disabled '}")
    
    if sync_search_agent_name in registered_agents:
        sync_tools = registered_agents[sync_search_agent_name]["config"].get("tools", [])
        logger.info(f"🛠️ SyncSearch Tools: {sync_tools}")
        
        web_search_status = " Ready" if ("builtin::websearch" in sync_tools and tavily_api_key) else " Not Working"
        logger.info(f"🌐 Web Search Status: {web_search_status}")
    
    logger.info("=" * 60)
    
    yield
    
    # Cleanup on shutdown
    logger.info("🛑 Shutting down SyncAI API")

app = FastAPI(
    title="SyncAI API",
    version="1.0.0", 
    description="Professional intelligence platform for staying synchronized with technology developments through persona-driven search",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(admin_router, prefix="/api")
app.include_router(files_router, prefix="/api")
app.include_router(vector_db_router, prefix="/api")

# Include SyncAI Search router
app.include_router(sync_search_router, prefix="/api")

@app.get("/")
async def root():
    registry_status = agent_registry.get_status() if agent_registry else {}
    registered_info = getattr(app.state, 'registered_agents', {})
    
    # Check SyncAI Search status
    sync_search_status = "disabled"
    sync_search_personas = []
    web_search_working = False
    
    if hasattr(app.state, 'sync_search_agent') and app.state.sync_search_agent:
        sync_search_status = "enabled"
        if hasattr(app.state, 'persona_config_loader'):
            sync_search_personas = app.state.persona_config_loader.get_available_personas()
        
        # Check if web search should be working
        if "sync_search" in registered_info:
            sync_config = registered_info["sync_search"]["config"]
            has_websearch = "builtin::websearch" in sync_config.get("tools", [])
            has_tavily = bool(config_loader.get_tavily_api_key())
            web_search_working = has_websearch and has_tavily
    
    return {
        "service": "SyncAI API",
        "status": "operational",
        "message": "🔄 Professional intelligence platform for technology synchronization",
        "version": "1.0.0",
        "agents": list(registered_info.keys()),
        "registry_status": registry_status,
        "capabilities": {
            "sync_search": {
                "status": sync_search_status,
                "personas": sync_search_personas,
                "features": ["web_search", "knowledge_base", "persona_optimization", "streaming"],
                "pattern": "single_agent_dual_tools",
                "web_search_working": web_search_working
            }
        },
        "services": [
            "admin - Agent management",
            "files - File upload/management", 
            "vector-db - Knowledge base management",
            "sync-search - 🔄 Persona-driven intelligence synchronization"
        ]
    }

@app.get("/api/agents/status")
async def get_agents_status():
    """Get detailed status for ALL agents including SyncAI Search"""
    if not agent_registry:
        return {"error": "Agent registry not initialized"}
    
    registry_status = agent_registry.get_status()
    registered_info = getattr(app.state, 'registered_agents', {})
    
    # Get individual agent statuses
    agent_details = {}
    for agent_name, info in registered_info.items():
        agent_details[agent_name] = {
            "agent_id": info["agent_id"],
            "session_id": info["session_id"],
            "status": "ready",
            "pattern": "Registry-based",
            "tools": info["config"].get("tools", [])
        }
    
    # Add SyncAI Search Agent info
    specialized_agents = {}
    if hasattr(app.state, 'sync_search_agent') and app.state.sync_search_agent:
        sync_agent_info = registered_info.get("sync_search", {})
        
        # Check web search configuration
        has_websearch = "builtin::websearch" in sync_agent_info.get("config", {}).get("tools", [])
        has_tavily = bool(config_loader.get_tavily_api_key())
        web_search_status = "working" if (has_websearch and has_tavily) else "not_working"
        
        specialized_agents["sync_search"] = {
            "type": "SyncSearchAgent",
            "tools": ["builtin::websearch", "builtin::rag"],
            "pattern": "Single Agent with Dual Tools (Web Search + RAG)",
            "agent_id": sync_agent_info.get("agent_id", "unknown"),
            "session_id": sync_agent_info.get("session_id", "unknown"),
            "status": "ready",
            "web_search_status": web_search_status,
            "tavily_configured": has_tavily,
            "websearch_tool_configured": has_websearch,
            "personas": app.state.persona_config_loader.get_available_personas() if hasattr(app.state, 'persona_config_loader') else [],
            "capabilities": [
                "Persona-driven search optimization",
                "Unified web search and RAG in single agent",
                "Real-time information synthesis", 
                "Configurable response formatting",
                "Streaming support",
                "Quality validation"
            ]
        }
    else:
        specialized_agents["sync_search"] = {
            "type": "SyncSearchAgent",
            "status": "disabled",
            "reason": "SyncAI Search agent 'sync_search' not configured in agents config"
        }
    
    return {
        "registry": registry_status,
        "agents": agent_details,
        "specialized_agents": specialized_agents,
        "llamastack_url": llamastack_base_url,
        "pattern": "Single Agent Pattern with Dual Tools",
        "sync_search_enabled": bool(hasattr(app.state, 'sync_search_agent') and app.state.sync_search_agent),
        "tavily_api_key_configured": bool(config_loader.get_tavily_api_key()),
        "summary": {
            "total_agents": len(registry_status["agents"]),
            "active_sessions": len(registry_status["sessions"]),
            "specialized_wrappers": len(specialized_agents),
            "sync_search_personas": len(specialized_agents.get("sync_search", {}).get("personas", [])),
            "architecture": "single_agent_dual_tools"
        }
    }

@app.get("/api/sync-search/status")
async def get_sync_search_status():
    """Get detailed SyncAI Search agent status"""
    if not hasattr(app.state, 'sync_search_agent') or not app.state.sync_search_agent:
        return {
            "enabled": False,
            "error": "SyncAI Search agent not initialized",
            "required_agent": "sync_search",
            "setup_instructions": "Add 'sync_search' agent with both 'builtin::websearch' and 'builtin::rag' tools to your agents configuration"
        }
    
    sync_search_agent = app.state.sync_search_agent
    persona_config_loader = getattr(app.state, 'persona_config_loader', None)
    registered_info = getattr(app.state, 'registered_agents', {})
    sync_agent_info = registered_info.get("sync_search", {})
    
    # Check web search configuration
    has_tavily = bool(config_loader.get_tavily_api_key())
    tools = sync_agent_info.get("config", {}).get("tools", [])
    has_websearch = "builtin::websearch" in tools
    web_search_working = has_websearch and has_tavily
    
    status = {
        "enabled": True,
        "agent_pattern": "single_agent_dual_tools",
        "agent_id": sync_agent_info.get("agent_id", "unknown"),
        "session_id": sync_agent_info.get("session_id", "unknown"),
        "tools": tools,
        "model": sync_agent_info.get("config", {}).get("model", "unknown"),
        "web_search_working": web_search_working,
        "tavily_configured": has_tavily,
        "websearch_tool_configured": has_websearch
    }
    
    if persona_config_loader:
        status["configuration_summary"] = persona_config_loader.get_config_summary()
        status["persona_display_info"] = persona_config_loader.get_persona_display_info()
    
    return {
        "enabled": True,
        "agent_status": status,
        "web_search_diagnosis": {
            "expected_to_work": web_search_working,
            "tavily_api_key": "configured" if has_tavily else "missing",
            "websearch_tool": "configured" if has_websearch else "missing",
            "issues": [
                "Missing Tavily API key" if not has_tavily else None,
                "Missing builtin::websearch tool" if not has_websearch else None
            ]
        },
        "endpoints": {
            "search": "/api/sync-search/search/{persona}",
            "search_stream": "/api/sync-search/search/{persona}/stream",
            "personas": "/api/sync-search/personas",
            "health": "/api/sync-search/health"
        },
        "architecture": "single_agent_with_dual_tools",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"🌐 Starting SyncAI server on {host}:{port}")
    logger.info(f"🔧 Debug mode: {debug}")
    logger.info(f"🤖 Architecture: Single Agent with Dual Tools")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )