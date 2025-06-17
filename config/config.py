"""
Configuration Loader - Complete Working Implementation for SyncAI
Updated for Single Agent Pattern and Search Configuration
"""

import yaml
import os
from pathlib import Path
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ConfigLoader")

class ConfigLoader:
    """Complete configuration loader for SyncAI"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration loader
        
        Args:
            config_path: Path to the main configuration YAML file
        """
        self.config_path = Path(config_path)
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    self.config = yaml.safe_load(file) or {}
                logger.info(f" Configuration loaded from {self.config_path}")
            else:
                logger.warning(f"⚠️ Config file not found: {self.config_path}, using defaults")
                self.config = self._get_default_config()
        except Exception as e:
            logger.error(f" Failed to load config: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration if file doesn't exist - Updated for Single Agent Pattern"""
        return {
            "llamastack": {
                "base_url": "http://localhost:5001",
                "default_model": "meta-llama/Llama-3.1-8B-Instruct",
                "timeout": 60
            },
            "api_keys": {
                "tavily_search_api_key": ""
            },
            "agents": [
                {
                    "name": "sync_search",
                    "model": "meta-llama/Llama-3.1-8B-Instruct",
                    "instructions": """You are SyncAI, a professional intelligence assistant that combines real-time web search with curated knowledge base information.
      
You have access to TWO powerful tools:
1. Web Search - for the latest developments, news, and trends
2. Knowledge Base (RAG) - for established best practices and proven methodologies

CRITICAL INSTRUCTIONS:
- ALWAYS use BOTH tools when possible to provide comprehensive information
- Clearly distinguish between real-time information (web search) and established knowledge (knowledge base)
- Start with knowledge base for foundational context, then add latest developments from web search
- Cite sources and provide timestamps when available
- Never hallucinate - only use information from your search results
- Format responses professionally with clear sections for different source types

Response Format:
## 📚 Knowledge Base Insights
[Established information from RAG - proven practices, foundational concepts]

## 🌐 Latest Developments  
[Recent information from web search - news, trends, announcements]

## 💡 Strategic Synthesis
[Combined insights, actionable recommendations, and next steps]""",
                    "tools": [
                        "builtin::websearch",
                        {
                            "name": "builtin::rag",
                            "args": {"vector_db_ids": ["ai_info"]}
                        }
                    ],
                    "sampling_params": {
                        "strategy": {"type": "greedy"},
                        "max_tokens": 4096
                    },
                    "max_infer_iters": 8
                },
                {
                    "name": "admin",
                    "model": "meta-llama/Llama-3.1-8B-Instruct",
                    "instructions": """You are an administrative assistant for SyncAI system management.
Help with system monitoring, configuration management, and operational tasks.
Provide clear, actionable responses for administrative queries.""",
                    "tools": [],
                    "sampling_params": {
                        "strategy": {"type": "greedy"},
                        "max_tokens": 2048
                    }
                }
            ],
            "vector_db": {
                "default_db_id": "ai_info",
                "default_chunk_size": 512,
                "collections": {
                    "ai_info": {
                        "description": "Curated AI and technology information",
                        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                        "chunk_size": 512,
                        "overlap": 50,
                        "vector_dimension": 384
                    }
                }
            },
            "file_storage": {
                "upload_dir": "./uploads",
                "max_file_size": 10485760,
                "allowed_extensions": [".txt", ".md", ".yaml", ".yml", ".json", ".py", ".pdf", ".docx", ".csv"]
            },
            "search": {
                "max_focus_areas": 10,
                "max_query_length": 500,
                "max_queries_per_persona": 8,
                "timeout_seconds": 60,
                "enable_query_enhancement": True,
                "enable_alternative_queries": True,
                "enable_persona_optimization": True,
                "parallel_processing": False
            },
            "app": {
                "title": "SyncAI API",
                "version": "1.0.0",
                "description": "Professional intelligence platform for technology synchronization",
                "debug": False,
                "host": "0.0.0.0",
                "port": 8000
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "file": "./logs/syncai.log",
                "max_size": "10MB",
                "backup_count": 5
            },
            "cors": {
                "allow_origins": ["*"],
                "allow_credentials": True,
                "allow_methods": ["*"],
                "allow_headers": ["*"]
            },
            "performance": {
                "worker_processes": 1,
                "max_requests": 1000,
                "timeout": 60,
                "keepalive": 2
            },
            "security": {
                "api_key_header": "X-API-Key",
                "rate_limit": {
                    "requests_per_minute": 60,
                    "burst_size": 10
                }
            },
            "monitoring": {
                "health_check_interval": 30,
                "metrics_enabled": True,
                "prometheus_port": 9090
            },
            "environments": {
                "development": {
                    "debug": True,
                    "logging": {"level": "DEBUG"},
                    "cors": {"allow_origins": ["http://localhost:3000", "http://localhost:8080"]}
                },
                "production": {
                    "debug": False,
                    "cors": {"allow_origins": ["https://your-domain.com"]},
                    "security": {"rate_limit": {"requests_per_minute": 30}},
                    "logging": {"level": "INFO"}
                },
                "testing": {
                    "debug": True,
                    "logging": {"level": "DEBUG"},
                    "file_storage": {"upload_dir": "./test_uploads"}
                }
            }
        }
    
    def get_llamastack_base_url(self) -> str:
        """Get LlamaStack base URL"""
        return self.config.get("llamastack", {}).get("base_url", "http://localhost:5001")
    
    def get_llamastack_timeout(self) -> int:
        """Get LlamaStack timeout"""
        return self.config.get("llamastack", {}).get("timeout", 60)
    
    def get_llamastack_default_model(self) -> str:
        """Get default LlamaStack model"""
        return self.config.get("llamastack", {}).get("default_model", "meta-llama/Llama-3.1-8B-Instruct")
    
    def get_agents_config(self) -> List[Dict[str, Any]]:
        """Get agents configuration"""
        return self.config.get("agents", [])
    
    def get_tavily_api_key(self) -> Optional[str]:
        """Get Tavily API key"""
        api_key = self.config.get("api_keys", {}).get("tavily_search_api_key")
        if not api_key or api_key == "":
            # Try environment variable as fallback
            api_key = os.getenv("TAVILY_SEARCH_API_KEY")
        return api_key if api_key and api_key != "" else None
    
    def get_vector_db_config(self) -> Dict[str, Any]:
        """Get vector database configuration"""
        return self.config.get("vector_db", {
            "default_db_id": "ai_info",
            "default_chunk_size": 512
        })
    
    def get_upload_dir(self) -> str:
        """Get file upload directory"""
        upload_dir = self.config.get("file_storage", {}).get("upload_dir", "./uploads")
        # Try environment variable as fallback
        if not upload_dir:
            upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        return os.path.abspath(upload_dir)
    
    def get_file_storage_config(self) -> Dict[str, Any]:
        """Get file storage configuration"""
        return self.config.get("file_storage", {
            "upload_dir": "./uploads",
            "max_file_size": 10485760,
            "allowed_extensions": [".txt", ".md", ".yaml", ".yml", ".json", ".py", ".pdf"]
        })
    
    def get_search_config(self) -> Dict[str, Any]:
        """Get search configuration - Required by SearchPreprocessor"""
        return self.config.get("search", {
            "max_focus_areas": 10,
            "max_query_length": 500,
            "max_queries_per_persona": 8,
            "timeout_seconds": 60,
            "enable_query_enhancement": True,
            "enable_alternative_queries": True,
            "enable_persona_optimization": True,
            "parallel_processing": False
        })
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration"""
        return self.config.get("app", {
            "title": "SyncAI API",
            "version": "1.0.0",
            "debug": False,
            "host": "0.0.0.0",
            "port": 8000
        })
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config.get("logging", {
            "level": "INFO",
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        })
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration"""
        return self.config.get("cors", {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"]
        })
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return self.config.get("performance", {
            "worker_processes": 1,
            "max_requests": 1000,
            "timeout": 60,
            "keepalive": 2
        })
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.config.get("security", {
            "api_key_header": "X-API-Key",
            "rate_limit": {
                "requests_per_minute": 60,
                "burst_size": 10
            }
        })
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self.config.get("monitoring", {
            "health_check_interval": 30,
            "metrics_enabled": True,
            "prometheus_port": 9090
        })
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get all API keys"""
        return self.config.get("api_keys", {})
    
    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        env = os.getenv("ENVIRONMENT", "development")
        return self.config.get("environments", {}).get(env, {})
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        # Check environment variable first
        debug_env = os.getenv("DEBUG", "").lower()
        if debug_env in ["true", "1", "yes"]:
            return True
        elif debug_env in ["false", "0", "no"]:
            return False
        
        # Fall back to config file
        return self.config.get("app", {}).get("debug", False)
    
    def get_host_and_port(self) -> tuple[str, int]:
        """Get host and port for the application"""
        host = os.getenv("HOST") or self.config.get("app", {}).get("host", "0.0.0.0")
        port = int(os.getenv("PORT", "0")) or self.config.get("app", {}).get("port", 8000)
        return host, port
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return validation report"""
        validation = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check required fields
        required_sections = ["llamastack", "agents"]
        for section in required_sections:
            if section not in self.config:
                validation["errors"].append(f"Missing required section: {section}")
                validation["valid"] = False
        
        # Check LlamaStack URL
        base_url = self.get_llamastack_base_url()
        if not base_url or not base_url.startswith("http"):
            validation["errors"].append("Invalid LlamaStack base_url")
            validation["valid"] = False
        
        # Check agents configuration
        agents = self.get_agents_config()
        if not agents:
            validation["warnings"].append("No agents configured")
        else:
            sync_search_found = False
            for agent in agents:
                if "name" not in agent:
                    validation["errors"].append("Agent missing name field")
                    validation["valid"] = False
                if "model" not in agent:
                    validation["errors"].append(f"Agent {agent.get('name', 'unknown')} missing model field")
                    validation["valid"] = False
                
                # Check for sync_search agent specifically
                if agent.get("name") == "sync_search":
                    sync_search_found = True
                    tools = agent.get("tools", [])
                    has_websearch = any("websearch" in str(tool) for tool in tools)
                    has_rag = any("rag" in str(tool) for tool in tools)
                    
                    if not has_websearch:
                        validation["warnings"].append("sync_search agent missing websearch tool")
                    if not has_rag:
                        validation["warnings"].append("sync_search agent missing rag tool")
            
            if not sync_search_found:
                validation["warnings"].append("No 'sync_search' agent found - SyncAI search functionality will be disabled")
        
        # Check Tavily API key
        tavily_key = self.get_tavily_api_key()
        if not tavily_key:
            validation["warnings"].append("Tavily API key not configured - web search may not work")
        
        # Check upload directory
        upload_dir = self.get_upload_dir()
        try:
            os.makedirs(upload_dir, exist_ok=True)
        except Exception as e:
            validation["warnings"].append(f"Cannot create upload directory {upload_dir}: {e}")
        
        # Check search configuration
        search_config = self.get_search_config()
        if search_config.get("max_focus_areas", 0) < 1:
            validation["warnings"].append("max_focus_areas should be at least 1")
        
        if search_config.get("timeout_seconds", 0) < 10:
            validation["warnings"].append("search timeout_seconds might be too low")
        
        return validation
    
    def reload_config(self) -> bool:
        """Reload configuration from file"""
        try:
            old_config = self.config.copy()
            self._load_config()
            
            if self.config != old_config:
                logger.info(" Configuration reloaded successfully")
                return True
            else:
                logger.info("ℹ️ Configuration unchanged")
                return True
                
        except Exception as e:
            logger.error(f" Failed to reload configuration: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        agents = self.get_agents_config()
        
        return {
            "config_file": str(self.config_path),
            "config_exists": self.config_path.exists(),
            "llamastack_url": self.get_llamastack_base_url(),
            "agents_configured": len(agents),
            "agent_names": [agent.get("name", "unknown") for agent in agents],
            "tavily_api_configured": bool(self.get_tavily_api_key()),
            "vector_db_id": self.get_vector_db_config().get("default_db_id"),
            "upload_dir": self.get_upload_dir(),
            "debug_mode": self.is_debug_mode(),
            "search_config_available": bool(self.get_search_config()),
            "validation": self.validate_config()
        }
    
    def update_config_value(self, section: str, key: str, value: Any) -> bool:
        """Update a configuration value and save to file"""
        try:
            if section not in self.config:
                self.config[section] = {}
            
            self.config[section][key] = value
            
            # Save back to file
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, default_flow_style=False)
            
            logger.info(f" Updated config: {section}.{key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f" Failed to update config: {e}")
            return False
    
    def get_single_agent_config(self) -> Optional[Dict[str, Any]]:
        """Get the single sync_search agent configuration"""
        agents = self.get_agents_config()
        for agent in agents:
            if agent.get("name") == "sync_search":
                return agent
        return None
    
    def is_single_agent_configured(self) -> bool:
        """Check if single agent pattern is properly configured"""
        agent = self.get_single_agent_config()
        if not agent:
            return False
        
        tools = agent.get("tools", [])
        has_websearch = any("websearch" in str(tool) for tool in tools)
        has_rag = any("rag" in str(tool) for tool in tools)
        
        return has_websearch and has_rag