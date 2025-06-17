"""
Search Preprocessor Module - Configuration-Driven Implementation
Handles all query preprocessing, validation, and enhancement logic
All behavior driven by persona configuration files
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
import re

logger = logging.getLogger("SearchPreprocessor")

class SearchQueryPreprocessor:
    """
    Handles preprocessing of search queries before execution
    Fully configuration-driven using PersonaConfigLoader
    """
    
    def __init__(self, config_loader, persona_engine=None):
        """
        Initialize preprocessor with configuration
        
        Args:
            config_loader: PersonaConfigLoader instance
            persona_engine: Optional persona engine instance (for future use)
        """
        self.config_loader = config_loader
        self.persona_engine = persona_engine
        
        # Get search configuration from main config if available
        self.search_config = getattr(config_loader, 'get_search_config', lambda: {})()
        
        # Default limits (can be overridden by configuration)
        self.max_focus_areas = self.search_config.get("max_focus_areas", 10)
        self.max_query_length = self.search_config.get("max_query_length", 500)
        self.max_queries_per_persona = self.search_config.get("max_queries_per_persona", 8)
        
        logger.info("🔧 SearchQueryPreprocessor initialized (Configuration-Driven)")
        
    def validate_and_prepare_request(
        self,
        persona: str,
        focus_areas: Optional[List[str]] = None,
        time_range: str = "30d",
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate and prepare search request parameters using persona configuration
        """
        start_time = time.time()
        
        # Generate correlation ID if not provided
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Validate persona
        available_personas = self.config_loader.get_available_personas()
        if persona not in available_personas:
            raise ValueError(f"Unknown persona: {persona}. Available: {available_personas}")
        
        # Get persona configuration
        try:
            persona_config = self.config_loader.get_persona_config(persona)
        except Exception as e:
            logger.error(f"Failed to get persona config: {e}")
            raise ValueError(f"Could not load configuration for persona: {persona}")
        
        # Prepare and validate focus areas using persona config
        processed_focus_areas = self._process_focus_areas_from_config(focus_areas, persona_config)
        
        # Validate time range
        validated_time_range = self._validate_time_range(time_range)
        
        # Generate search context using persona configuration
        search_context = self._generate_search_context_from_config(
            persona, persona_config, processed_focus_areas, validated_time_range
        )
        
        # Log preprocessing details
        processing_time = time.time() - start_time
        self._log_preprocessing(persona, processed_focus_areas, validated_time_range, correlation_id, processing_time)
        
        return {
            "persona": persona,
            "focus_areas": processed_focus_areas,
            "time_range": validated_time_range,
            "correlation_id": correlation_id,
            "persona_config": persona_config,
            "search_context": search_context,
            "processing_metadata": {
                "preprocessing_time": processing_time,
                "timestamp": datetime.utcnow().isoformat(),
                "validation_passed": True
            }
        }
    
    def generate_search_queries(self, prepared_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate optimized search queries using persona configuration
        """
        start_time = time.time()
        
        persona = prepared_request["persona"]
        focus_areas = prepared_request["focus_areas"]
        time_range = prepared_request["time_range"]
        search_context = prepared_request["search_context"]
        persona_config = prepared_request["persona_config"]
        
        # Generate comprehensive query using persona configuration
        unified_query = self._build_unified_search_query_from_config(
            persona, persona_config, focus_areas, time_range, search_context
        )
        
        # Generate alternative queries using persona's search patterns
        alternative_queries = self._generate_alternative_queries_from_config(
            persona_config, focus_areas
        )
        
        # Get persona-specific instructions from configuration
        persona_instructions = self._get_enhanced_instructions_from_config(persona_config)
        
        # Build query metadata
        query_metadata = self._build_query_metadata_from_config(persona_config, focus_areas, time_range)
        
        processing_time = time.time() - start_time
        
        query_data = {
            "primary_query": unified_query,
            "alternative_queries": alternative_queries,
            "persona_instructions": persona_instructions,
            "query_metadata": query_metadata,
            "search_strategy": "unified_agent_dual_tools",
            "processing_info": {
                "query_generation_time": processing_time,
                "total_queries_generated": 1 + len(alternative_queries),
                "generation_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        self._log_query_generation(query_data, prepared_request["correlation_id"])
        
        return query_data
    
    def _process_focus_areas_from_config(self, focus_areas: Optional[List[str]], persona_config) -> List[str]:
        """Process and validate focus areas using persona configuration"""
        if not focus_areas:
            # Use persona's configured focus areas
            default_areas = persona_config.focus_areas[:8]  # Limit for performance
            logger.info(f"Using persona's configured focus areas: {len(default_areas)} areas")
            return default_areas
        
        # Clean and validate provided focus areas
        cleaned_areas = []
        for area in focus_areas:
            if not area or not isinstance(area, str):
                continue
                
            # Clean the area string
            cleaned_area = self._clean_focus_area(area)
            if cleaned_area and len(cleaned_area) >= 3:  # Minimum length check
                cleaned_areas.append(cleaned_area)
        
        # Limit number of focus areas for performance
        if len(cleaned_areas) > self.max_focus_areas:
            logger.warning(f"Limiting focus areas from {len(cleaned_areas)} to {self.max_focus_areas}")
            cleaned_areas = cleaned_areas[:self.max_focus_areas]
        
        # Fallback to persona defaults if no valid areas
        if not cleaned_areas:
            logger.warning("No valid focus areas provided, using persona's configured defaults")
            return persona_config.focus_areas[:8]
        
        logger.info(f"Processed {len(cleaned_areas)} focus areas")
        return cleaned_areas
    
    def _clean_focus_area(self, area: str) -> str:
        """Clean and normalize a focus area string"""
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', area.strip())
        
        # Remove special characters that might interfere with search
        cleaned = re.sub(r'[^\w\s\-\.]', '', cleaned)
        
        # Capitalize properly
        if len(cleaned) > 0:
            cleaned = cleaned[0].upper() + cleaned[1:].lower()
        
        return cleaned
    
    def _validate_time_range(self, time_range: str) -> str:
        """Validate and normalize time range parameter"""
        valid_ranges = {
            "7d": "7d",
            "30d": "30d", 
            "90d": "90d",
            "6m": "6m",
            "1y": "1y",
            "week": "7d",
            "month": "30d",
            "quarter": "90d",
            "year": "1y"
        }
        
        normalized_range = time_range.lower().strip()
        
        if normalized_range in valid_ranges:
            return valid_ranges[normalized_range]
        
        logger.warning(f"Invalid time range '{time_range}', defaulting to '30d'")
        return "30d"
    
    def _generate_search_context_from_config(
        self, 
        persona: str, 
        persona_config, 
        focus_areas: List[str], 
        time_range: str
    ) -> Dict[str, Any]:
        """Generate search context using persona configuration"""
        return {
            "persona_display": persona_config.display_name,
            "persona_description": persona_config.description,
            "focus_summary": ', '.join(focus_areas),
            "time_context": self._get_time_context(time_range),
            "search_scope": "comprehensive_dual_source",
            "priority": "balanced_rag_and_web",
            "technical_depth": persona_config.instructions.get("technical_depth", "balanced"),
            "core_objectives": persona_config.instructions.get("core_objectives", []),
            "output_style": persona_config.output_format.get("style", "balanced")
        }
    
    def _get_time_context(self, time_range: str) -> str:
        """Get human-readable time context"""
        time_contexts = {
            "7d": "past week",
            "30d": "past month", 
            "90d": "past quarter",
            "6m": "past 6 months",
            "1y": "past year"
        }
        return time_contexts.get(time_range, "recent period")
    
    def _build_unified_search_query_from_config(
        self, 
        persona: str, 
        persona_config, 
        focus_areas: List[str], 
        time_range: str, 
        search_context: Dict[str, Any]
    ) -> str:
        """Build comprehensive search query using persona configuration"""
        persona_display = persona_config.display_name
        time_context = search_context["time_context"]
        
        # Get persona-specific search guidance from configuration
        persona_guidance = self._get_persona_search_guidance_from_config(persona_config)
        
        # Get core objectives from configuration
        core_objectives = persona_config.instructions.get("core_objectives", [])
        objectives_text = f"Core objectives: {', '.join(core_objectives)}" if core_objectives else ""
        
        # Get technical depth from configuration
        technical_depth = persona_config.instructions.get("technical_depth", "balanced")
        
        # Build the query using configuration data
        query = f"""I need a comprehensive intelligence report for a {persona_display} about: {', '.join(focus_areas)}

SEARCH INSTRUCTIONS:
1. First, search your knowledge base for established information, best practices, and proven methodologies about these topics
2. Then, search the web for the latest developments, news, and trends from the {time_context}
3. Combine both sources to provide a complete picture

PERSONA FOCUS:
{persona_guidance}

{objectives_text}

TECHNICAL DEPTH: {technical_depth}

TIME RANGE: Focus on developments from the last {time_range} for web search.

RESPONSE STRUCTURE:
Please organize your response as follows:

## 📚 Knowledge Base Insights
[Established information from your knowledge base - proven practices, foundational concepts]

## 🌐 Latest Developments
[Recent information from web search - news, trends, announcements from the {time_context}]

## 💡 Strategic Synthesis for {persona_display}
[Combined insights, actionable recommendations, and next steps specifically relevant to {persona_display}]

IMPORTANT: Use BOTH your knowledge base search AND web search capabilities. Clearly distinguish between established knowledge and recent developments."""

        return query
    
    def _get_persona_search_guidance_from_config(self, persona_config) -> str:
        """Get persona-specific search guidance from configuration"""
        guidance_parts = []
        
        # Add description as primary guidance
        if persona_config.description:
            guidance_parts.append(f"- {persona_config.description}")
        
        # Add core objectives
        core_objectives = persona_config.instructions.get("core_objectives", [])
        if core_objectives:
            guidance_parts.append(f"- Focus on: {', '.join(core_objectives)}")
        
        # Add primary role guidance
        primary_role = persona_config.instructions.get("primary_role", "")
        if primary_role and "assistant" not in primary_role.lower():
            guidance_parts.append(f"- Role context: {primary_role}")
        
        # Add search patterns as guidance
        if persona_config.search_patterns:
            top_patterns = persona_config.search_patterns[:3]
            guidance_parts.append(f"- Key search areas: {', '.join(top_patterns)}")
        
        # Add topic categories as guidance
        if persona_config.topic_categories:
            categories = list(persona_config.topic_categories.keys())[:3]
            guidance_parts.append(f"- Topic categories: {', '.join(categories)}")
        
        return "\n".join(guidance_parts) if guidance_parts else f"Provide comprehensive information relevant to {persona_config.display_name}."
    
    def _generate_alternative_queries_from_config(self, persona_config, focus_areas: List[str]) -> List[str]:
        """Generate alternative queries using persona's search patterns"""
        alternatives = []
        
        # Use persona's configured search patterns
        if persona_config.search_patterns and len(persona_config.search_patterns) > 0:
            # Use first search pattern as alternative
            alternatives.append(persona_config.search_patterns[0])
        
        # Use search modifiers from configuration
        if persona_config.search_modifiers and focus_areas:
            primary_area = focus_areas[0]
            
            # Try to find relevant modifiers
            for modifier_type, modifiers in persona_config.search_modifiers.items():
                if modifiers and len(alternatives) < 2:
                    modifier = modifiers[0]
                    alternatives.append(f"{modifier} {primary_area}")
        
        # Fallback to simple alternatives if no patterns configured
        if not alternatives and len(focus_areas) > 1:
            primary_area = focus_areas[0]
            alternatives.append(f"Latest developments in {primary_area} for {persona_config.display_name}")
        
        # Trend-focused query using focus areas
        if len(alternatives) < 2:
            alternatives.append(f"Current trends and innovations in {', '.join(focus_areas[:3])}")
        
        return alternatives[:2]  # Limit to 2 alternatives
    
    def _get_enhanced_instructions_from_config(self, persona_config) -> str:
        """Get enhanced instructions using persona configuration"""
        base_instructions = """
You are SyncAI, a professional intelligence assistant. You have access to both a knowledge base (RAG) and web search.

CRITICAL REQUIREMENTS:
- ALWAYS use BOTH tools when responding to comprehensive intelligence requests
- Clearly distinguish between established knowledge (knowledge base) and recent developments (web search)
- Provide actionable insights specific to the user's role
- Include source attribution when possible
- Format responses professionally with clear sections
"""
        
        # Get role-specific focus from configuration
        primary_role = persona_config.instructions.get("primary_role", f"AI search assistant for {persona_config.display_name}")
        core_objectives = persona_config.instructions.get("core_objectives", [])
        
        role_specific = f"PRIMARY ROLE: {primary_role}"
        if core_objectives:
            role_specific += f"\nCORE OBJECTIVES: {', '.join(core_objectives)}"
        
        return f"{base_instructions}\n{role_specific}"
    
    def _build_query_metadata_from_config(self, persona_config, focus_areas: List[str], time_range: str) -> Dict[str, Any]:
        """Build metadata using persona configuration"""
        return {
            "persona": persona_config.name,
            "persona_display": persona_config.display_name,
            "focus_area_count": len(focus_areas),
            "time_range": time_range,
            "query_complexity": "comprehensive",
            "expected_sources": ["knowledge_base", "web_search"],
            "search_mode": "unified_agent",
            "quality_requirements": ["source_attribution", "recency_indication", "actionable_insights"],
            "technical_depth": persona_config.instructions.get("technical_depth", "balanced"),
            "output_style": persona_config.output_format.get("style", "balanced"),
            "configured_patterns": len(persona_config.search_patterns),
            "configured_categories": len(persona_config.topic_categories)
        }
    
    def _log_preprocessing(self, persona: str, focus_areas: List[str], 
                          time_range: str, correlation_id: str, processing_time: float):
        """Log preprocessing details"""
        logger.info(f"🔍 Preprocessing completed for persona: {persona}")
        logger.info(f"📥 Focus areas ({len(focus_areas)}): {', '.join(focus_areas[:3])}{'...' if len(focus_areas) > 3 else ''}")
        logger.info(f"⏰ Time range: {time_range}")
        logger.info(f"🆔 Correlation ID: {correlation_id}")
        logger.info(f"⚡ Processing time: {processing_time:.3f}s")
        
        # Debug logging if enabled
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"All focus areas: {focus_areas}")
    
    def _log_query_generation(self, query_data: Dict[str, Any], correlation_id: str):
        """Log query generation details"""
        processing_info = query_data["processing_info"]
        
        logger.info(f"📋 Query generation completed for correlation: {correlation_id}")
        logger.info(f"⚡ Generation time: {processing_info['query_generation_time']:.3f}s")
        logger.info(f"📝 Queries generated: {processing_info['total_queries_generated']}")
        logger.info(f"🔧 Strategy: {query_data['search_strategy']}")
        
        # Debug logging for query content
        if logger.isEnabledFor(logging.DEBUG):
            primary_query = query_data["primary_query"]
            logger.debug(f"Primary query length: {len(primary_query)} characters")
            logger.debug(f"Query preview: {primary_query[:200]}...")

class SearchRequestValidator:
    """
    Handles validation of search requests and parameters
    """
    
    @staticmethod
    def validate_persona(persona: str, available_personas: List[str]) -> None:
        """Validate persona parameter"""
        if not persona:
            raise ValueError("Persona is required")
        
        if not isinstance(persona, str):
            raise ValueError("Persona must be a string")
        
        if persona not in available_personas:
            raise ValueError(f"Unknown persona: {persona}. Available: {available_personas}")
    
    @staticmethod
    def validate_focus_areas(focus_areas: Optional[List[str]]) -> List[str]:
        """Validate and clean focus areas"""
        if not focus_areas:
            return []
        
        if not isinstance(focus_areas, list):
            raise ValueError("Focus areas must be a list")
        
        # Clean and validate each area
        cleaned_areas = []
        for area in focus_areas:
            if not isinstance(area, str):
                continue
                
            cleaned_area = area.strip()
            if cleaned_area and len(cleaned_area) >= 3:
                cleaned_areas.append(cleaned_area)
        
        return cleaned_areas
    
    @staticmethod
    def validate_time_range(time_range: str) -> str:
        """Validate time range parameter"""
        valid_ranges = ["7d", "30d", "90d", "6m", "1y"]
        
        if not time_range:
            return "30d"  # Default
        
        if not isinstance(time_range, str):
            raise ValueError("Time range must be a string")
        
        normalized = time_range.lower().strip()
        
        # Allow some variations
        range_map = {
            "week": "7d",
            "month": "30d", 
            "quarter": "90d",
            "year": "1y"
        }
        
        if normalized in range_map:
            return range_map[normalized]
        
        if normalized not in valid_ranges:
            raise ValueError(f"Invalid time range: {time_range}. Valid options: {valid_ranges}")
        
        return normalized
    
    @staticmethod
    def validate_correlation_id(correlation_id: Optional[str]) -> str:
        """Validate or generate correlation ID"""
        if correlation_id:
            if not isinstance(correlation_id, str):
                raise ValueError("Correlation ID must be a string")
                
            if len(correlation_id) < 8:
                raise ValueError("Correlation ID must be at least 8 characters")
                
            # Check for valid characters (alphanumeric, dash, underscore)
            if not re.match(r'^[a-zA-Z0-9_-]+$', correlation_id):
                raise ValueError("Correlation ID contains invalid characters")
                
            return correlation_id
        
        return str(uuid.uuid4())

class SearchConfigurationManager:
    """
    Manages search configuration and optimization settings
    """
    
    def __init__(self, config_loader):
        """Initialize with configuration loader"""
        self.config_loader = config_loader
        self.search_config = getattr(config_loader, 'get_search_config', lambda: {})()
    
    def get_search_limits(self) -> Dict[str, int]:
        """Get search limits and constraints"""
        return {
            "max_focus_areas": self.search_config.get("max_focus_areas", 10),
            "max_query_length": self.search_config.get("max_query_length", 500),
            "max_queries_per_request": self.search_config.get("max_queries_per_request", 3),
            "timeout_seconds": self.search_config.get("timeout_seconds", 60)
        }
    
    def get_optimization_settings(self) -> Dict[str, Any]:
        """Get optimization settings for search"""
        return {
            "enable_query_enhancement": self.search_config.get("enable_query_enhancement", True),
            "enable_alternative_queries": self.search_config.get("enable_alternative_queries", True),
            "enable_persona_optimization": self.search_config.get("enable_persona_optimization", True),
            "parallel_processing": self.search_config.get("parallel_processing", False)  # Single agent doesn't need this
        }
    
    def get_quality_settings(self) -> Dict[str, Any]:
        """Get quality control settings"""
        return {
            "require_source_attribution": True,
            "require_recency_indication": True,
            "require_actionable_insights": True,
            "minimum_response_length": 200,
            "maximum_response_length": 5000
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration"""
        validation = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check basic configuration
        try:
            personas = self.config_loader.get_available_personas()
            if not personas:
                validation["errors"].append("No personas configured")
                validation["valid"] = False
            else:
                validation["personas_count"] = len(personas)
        except Exception as e:
            validation["errors"].append(f"Failed to load personas: {e}")
            validation["valid"] = False
        
        # Check search limits
        limits = self.get_search_limits()
        if limits["max_focus_areas"] < 1:
            validation["warnings"].append("max_focus_areas is too low")
        
        if limits["timeout_seconds"] < 10:
            validation["warnings"].append("timeout_seconds might be too low")
        
        return validation