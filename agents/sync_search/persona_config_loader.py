"""
Persona Configuration Loader - Enhanced Working Implementation
Minor improvements for better SyncSearchAgent integration
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger("PersonaConfigLoader")

@dataclass
class PersonaConfig:
    """Simple persona configuration"""
    name: str
    display_name: str
    description: str
    focus_areas: List[str]
    search_patterns: List[str]
    topic_categories: Dict[str, List[str]]
    search_modifiers: Dict[str, List[str]]
    output_format: Dict[str, Any]
    instructions: Dict[str, Any]

class PersonaConfigLoader:
    """
    Simple persona configuration loader with fallback defaults
    Enhanced for better SyncSearchAgent integration
    """
    
    def __init__(self, config_path: str = "persona_config.yaml"):
        """Initialize with config path"""
        self.config_path = Path(config_path)
        self.config_data = None
        self.personas = {}
        
        self._load_config()
        self._parse_personas()
    
    def _load_config(self):
        """Load configuration from YAML file or use defaults"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    self.config_data = yaml.safe_load(file) or {}
                logger.info(f" Persona configuration loaded from {self.config_path}")
            else:
                logger.warning(f"⚠️ Persona config file not found: {self.config_path}, using defaults")
                self.config_data = self._get_default_config()
        except Exception as e:
            logger.error(f" Failed to load persona config: {e}")
            logger.info("🔄 Using default persona configuration")
            self.config_data = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default persona configuration"""
        return {
            "personas": {
                "devops_engineer": {
                    "display_name": "DevOps Engineer",
                    "description": "Infrastructure and deployment focused AI search",
                    "focus_areas": [
                        "MLOps platform updates",
                        "AI infrastructure scaling",
                        "GPU cluster management",
                        "Container orchestration for AI",
                        "AI model deployment tools",
                        "Cost optimization strategies",
                        "Monitoring and observability",
                        "CI/CD for AI models",
                        "Infrastructure as Code for AI"
                    ],
                    "search_patterns": [
                        "latest MLOps platforms",
                        "GPU infrastructure updates",
                        "AI deployment tools",
                        "container AI orchestration",
                        "AI model serving platforms",
                        "GPU cost optimization"
                    ],
                    "topic_categories": {
                        "infrastructure": ["GPU clusters", "TPU management", "distributed training"],
                        "platforms": ["MLOps platforms", "model registries", "experiment tracking"],
                        "cost_optimization": ["spot instances", "GPU sharing", "resource scheduling"]
                    },
                    "search_modifiers": {
                        "urgency": ["breaking", "latest", "urgent"],
                        "implementation": ["how to", "tutorial", "guide"]
                    },
                    "output_format": {
                        "structure": "infrastructure_focused",
                        "style": "technical_detailed"
                    },
                    "instructions": {
                        "primary_role": "AI search assistant for DevOps Engineers",
                        "core_objectives": ["Infrastructure insights", "Cost optimization", "Scalability"],
                        "technical_depth": "advanced"
                    }
                },
                
                "software_engineer": {
                    "display_name": "Software Engineer",
                    "description": "Development frameworks and APIs focused AI search",
                    "focus_areas": [
                        "AI development frameworks",
                        "LLM integration APIs",
                        "AI coding assistants",
                        "Generative AI SDKs",
                        "AI testing frameworks",
                        "Prompt engineering tools",
                        "AI debugging solutions",
                        "Vector databases",
                        "Embedding models"
                    ],
                    "search_patterns": [
                        "new AI development frameworks",
                        "LLM API updates",
                        "AI coding tools",
                        "generative AI SDKs",
                        "AI testing libraries"
                    ],
                    "topic_categories": {
                        "frameworks": ["LangChain", "LlamaIndex", "Haystack"],
                        "apis_and_sdks": ["OpenAI API", "Anthropic API", "Google Gemini API"],
                        "development_tools": ["AI coding assistants", "code completion", "AI debuggers"]
                    },
                    "search_modifiers": {
                        "implementation": ["tutorial", "example", "documentation"],
                        "comparison": ["vs", "comparison", "benchmark"]
                    },
                    "output_format": {
                        "structure": "development_focused",
                        "style": "practical_technical"
                    },
                    "instructions": {
                        "primary_role": "AI search assistant for Software Engineers",
                        "core_objectives": ["Development guidance", "API updates", "Best practices"],
                        "technical_depth": "implementation_focused"
                    }
                },
                
                "ai_engineer": {
                    "display_name": "AI Engineer",
                    "description": "Research and ML engineering focused AI search",
                    "focus_areas": [
                        "LLM architectures",
                        "Model training techniques",
                        "Fine-tuning methodologies",
                        "AI research papers",
                        "Neural network innovations",
                        "Model optimization",
                        "Evaluation frameworks",
                        "Transformer improvements",
                        "Multi-modal models"
                    ],
                    "search_patterns": [
                        "latest LLM research papers",
                        "new neural architectures",
                        "model training techniques",
                        "fine-tuning methods",
                        "AI model optimization"
                    ],
                    "topic_categories": {
                        "architectures": ["transformer variants", "attention mechanisms", "encoder-decoder"],
                        "training_techniques": ["supervised learning", "self-supervised", "reinforcement learning"],
                        "optimization": ["gradient descent variants", "regularization techniques", "pruning"]
                    },
                    "search_modifiers": {
                        "research": ["paper", "study", "research", "experiment"],
                        "technical": ["architecture", "method", "algorithm"]
                    },
                    "output_format": {
                        "structure": "research_focused",
                        "style": "academic_technical"
                    },
                    "instructions": {
                        "primary_role": "AI search assistant for AI Engineers and Researchers",
                        "core_objectives": ["Research insights", "Technical methodologies", "Innovations"],
                        "technical_depth": "research_level"
                    }
                },
                
                "product_owner": {
                    "display_name": "Product Owner",
                    "description": "Product features and user experience focused AI search",
                    "focus_areas": [
                        "AI product features",
                        "User experience improvements",
                        "Market adoption trends",
                        "Competitive analysis",
                        "Feature development costs",
                        "Success metrics",
                        "User feedback patterns",
                        "AI accessibility",
                        "Product roadmap planning"
                    ],
                    "search_patterns": [
                        "AI product features trends",
                        "user experience AI",
                        "AI adoption rates",
                        "competitive AI features",
                        "AI product success metrics"
                    ],
                    "topic_categories": {
                        "user_experience": ["UI/UX design", "accessibility", "usability testing"],
                        "feature_development": ["feature prioritization", "MVP planning", "user stories"],
                        "market_analysis": ["market research", "competitor analysis", "user surveys"]
                    },
                    "search_modifiers": {
                        "user_focused": ["user", "customer", "experience", "feedback"],
                        "market_focused": ["market", "competitive", "trends", "adoption"]
                    },
                    "output_format": {
                        "structure": "product_focused",
                        "style": "strategic_user_centric"
                    },
                    "instructions": {
                        "primary_role": "AI search assistant for Product Owners",
                        "core_objectives": ["User insights", "Market trends", "Feature opportunities"],
                        "technical_depth": "product_focused"
                    }
                },
                
                "product_manager": {
                    "display_name": "Product Manager",
                    "description": "Business strategy and market opportunity focused AI search",
                    "focus_areas": [
                        "AI business strategy",
                        "Market opportunities",
                        "Business model innovations",
                        "Monetization strategies",
                        "Enterprise adoption",
                        "ROI measurements",
                        "Strategic partnerships",
                        "Investment trends",
                        "Competitive positioning"
                    ],
                    "search_patterns": [
                        "AI business strategy",
                        "AI market opportunities",
                        "AI monetization models",
                        "enterprise AI adoption",
                        "AI partnership deals"
                    ],
                    "topic_categories": {
                        "business_strategy": ["strategic planning", "market positioning", "competitive advantage"],
                        "financial_metrics": ["revenue models", "pricing strategies", "ROI analysis"],
                        "partnerships": ["strategic alliances", "joint ventures", "technology partnerships"]
                    },
                    "search_modifiers": {
                        "strategic": ["strategy", "strategic", "planning", "vision"],
                        "financial": ["revenue", "profit", "ROI", "investment"]
                    },
                    "output_format": {
                        "structure": "business_focused",
                        "style": "executive_strategic"
                    },
                    "instructions": {
                        "primary_role": "AI search assistant for Product Managers",
                        "core_objectives": ["Strategic insights", "Business opportunities", "Market intelligence"],
                        "technical_depth": "business_strategic"
                    }
                }
            }
        }
    
    def _parse_personas(self):
        """Parse persona configurations"""
        personas_config = self.config_data.get("personas", {})
        
        for persona_name, persona_data in personas_config.items():
            try:
                persona_config = PersonaConfig(
                    name=persona_name,
                    display_name=persona_data.get("display_name", persona_name.replace("_", " ").title()),
                    description=persona_data.get("description", ""),
                    focus_areas=persona_data.get("focus_areas", []),
                    search_patterns=persona_data.get("search_patterns", []),
                    topic_categories=persona_data.get("topic_categories", {}),
                    search_modifiers=persona_data.get("search_modifiers", {}),
                    output_format=persona_data.get("output_format", {}),
                    instructions=persona_data.get("instructions", {})
                )
                
                self.personas[persona_name] = persona_config
                logger.debug(f" Parsed persona: {persona_name}")
                
            except Exception as e:
                logger.error(f" Failed to parse persona '{persona_name}': {e}")
        
        logger.info(f" Loaded {len(self.personas)} persona configurations")
    
    def get_persona_config(self, persona: str) -> PersonaConfig:
        """Get configuration for a specific persona"""
        if persona not in self.personas:
            available = list(self.personas.keys())
            raise ValueError(f"Unknown persona: {persona}. Available: {available}")
        
        return self.personas[persona]
    
    def get_available_personas(self) -> List[str]:
        """Get list of available persona names"""
        return list(self.personas.keys())
    
    def get_persona_display_info(self) -> Dict[str, Dict[str, str]]:
        """Get display information for all personas"""
        display_info = {}
        for name, config in self.personas.items():
            display_info[name] = {
                "display_name": config.display_name,
                "description": config.description,
                "focus_count": len(config.focus_areas),
                "search_patterns_count": len(config.search_patterns)
            }
        return display_info
    
    def validate_persona_request(self, persona: str, focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """Validate a persona request"""
        validation = {
            "valid": True,
            "warnings": [],
            "suggestions": []
        }
        
        # Check persona exists
        if persona not in self.personas:
            validation["valid"] = False
            validation["warnings"].append(f"Unknown persona: {persona}")
            validation["suggestions"].append(f"Available personas: {', '.join(self.get_available_personas())}")
            return validation
        
        # Validate focus areas if provided
        if focus_areas and len(focus_areas) > 10:
            validation["warnings"].append("Too many focus areas (>10), performance may be affected")
        
        return validation
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        return {
            "config_file": str(self.config_path),
            "config_exists": self.config_path.exists(),
            "personas_loaded": len(self.personas),
            "available_personas": list(self.personas.keys()),
            "configuration_valid": True
        }
    
    # Additional methods for better SyncSearchAgent integration
    
    def get_persona_search_context(self, persona: str, focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get comprehensive search context for a persona
        Used by SyncSearchAgent for dynamic query building
        """
        if persona not in self.personas:
            return {}
        
        config = self.personas[persona]
        
        # Use provided focus areas or get from config
        effective_focus_areas = focus_areas or config.focus_areas
        
        return {
            "persona_name": persona,
            "display_name": config.display_name,
            "description": config.description,
            "focus_areas": effective_focus_areas,
            "search_patterns": config.search_patterns,
            "topic_categories": config.topic_categories,
            "search_modifiers": config.search_modifiers,
            "output_format": config.output_format,
            "instructions": config.instructions,
            "primary_role": config.instructions.get("primary_role", f"AI search assistant for {config.display_name}"),
            "core_objectives": config.instructions.get("core_objectives", []),
            "technical_depth": config.instructions.get("technical_depth", "balanced")
        }
    
    def get_search_enhancement_keywords(self, persona: str) -> List[str]:
        """
        Get keywords for enhancing search queries based on persona
        """
        if persona not in self.personas:
            return []
        
        config = self.personas[persona]
        keywords = []
        
        # Add search patterns
        keywords.extend(config.search_patterns)
        
        # Add topic categories keywords
        for category_list in config.topic_categories.values():
            keywords.extend(category_list)
        
        # Add search modifiers
        for modifier_list in config.search_modifiers.values():
            keywords.extend(modifier_list)
        
        # Remove duplicates and return
        return list(set(keywords))
    
    def get_response_formatting_rules(self, persona: str) -> Dict[str, Any]:
        """
        Get response formatting rules for a specific persona
        Used by post-processor for persona-specific formatting
        """
        if persona not in self.personas:
            return {"structure": "default", "style": "balanced"}
        
        config = self.personas[persona]
        output_format = config.output_format
        
        return {
            "structure": output_format.get("structure", "default"),
            "style": output_format.get("style", "balanced"),
            "technical_depth": config.instructions.get("technical_depth", "balanced"),
            "core_objectives": config.instructions.get("core_objectives", []),
            "focus_areas": config.focus_areas,
            "display_name": config.display_name,
            "description": config.description
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the entire configuration
        Enhanced validation for SyncSearchAgent compatibility
        """
        validation = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check if any personas loaded
        if not self.personas:
            validation["errors"].append("No personas configured")
            validation["valid"] = False
            return validation
        
        # Validate each persona
        for persona_name, config in self.personas.items():
            persona_issues = []
            
            # Check required fields
            if not config.display_name:
                persona_issues.append("Missing display_name")
            
            if not config.focus_areas:
                persona_issues.append("No focus_areas defined")
            
            if not config.instructions.get("primary_role"):
                persona_issues.append("Missing primary_role in instructions")
            
            if not config.instructions.get("core_objectives"):
                persona_issues.append("Missing core_objectives in instructions")
            
            if persona_issues:
                validation["warnings"].append(f"Persona '{persona_name}': {', '.join(persona_issues)}")
        
        # Check for duplicate display names
        display_names = [config.display_name for config in self.personas.values()]
        if len(display_names) != len(set(display_names)):
            validation["warnings"].append("Duplicate display names found")
        
        return validation
    
    def reload_config(self) -> bool:
        """
        Reload configuration from file
        Returns True if successful, False otherwise
        """
        try:
            old_personas_count = len(self.personas)
            
            # Reload configuration
            self._load_config()
            self._parse_personas()
            
            new_personas_count = len(self.personas)
            logger.info(f"🔄 Configuration reloaded: {old_personas_count} -> {new_personas_count} personas")
            
            return True
            
        except Exception as e:
            logger.error(f" Failed to reload configuration: {e}")
            return False