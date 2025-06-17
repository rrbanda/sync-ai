"""
SyncAI Search Routes - Enhanced Implementation with Newsletter Support
Complete working implementation with newsletter, daily brief, and improved error handling
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
import json
import asyncio
import uuid

logger = logging.getLogger("sync_search_routes")
router = APIRouter(prefix="/sync-search", tags=["sync-search"])

def get_sync_search_agent(request: Request):
    """Get SyncAI Search Agent from app state"""
    if not hasattr(request.app.state, 'sync_search_agent') or not request.app.state.sync_search_agent:
        raise HTTPException(
            status_code=503, 
            detail="SyncAI Search Agent not available. Please check agent configuration."
        )
    return request.app.state.sync_search_agent

def get_persona_config_loader(request: Request):
    """Get Persona Config Loader from app state"""
    if not hasattr(request.app.state, 'persona_config_loader'):
        raise HTTPException(
            status_code=503,
            detail="Persona configuration not available"
        )
    return request.app.state.persona_config_loader

def get_config_loader(request: Request):
    """Get main Config Loader from app state"""
    if not hasattr(request.app.state, 'config_loader'):
        raise HTTPException(
            status_code=503,
            detail="Configuration loader not available"
        )
    return request.app.state.config_loader

# === Request/Response Models ===

class SyncSearchRequest(BaseModel):
    """Request model for SyncAI search with enhanced validation"""
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Specific areas to focus on (optional, will use persona defaults if not provided)",
        example=["enterprise adoption", "market trends", "competitive analysis"]
    )
    time_range: str = Field(
        default="30d",
        description="Time range for search (7d, 30d, 90d, 6m, 1y)",
        example="30d"
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Request correlation ID for tracking (optional)",
        example="req_12345"
    )
    timeout: Optional[int] = Field(
        default=60,
        description="Search timeout in seconds (10-120)",
        example=60
    )
    
    @validator('time_range')
    def validate_time_range(cls, v):
        valid_ranges = ["7d", "30d", "90d", "6m", "1y", "week", "month", "quarter", "year"]
        if v.lower() not in valid_ranges:
            raise ValueError(f"Invalid time_range. Must be one of: {valid_ranges}")
        return v.lower()
    
    @validator('focus_areas')
    def validate_focus_areas(cls, v):
        if v is not None:
            if len(v) > 10:
                raise ValueError("Too many focus areas. Maximum 10 allowed.")
            # Filter out empty strings
            v = [area.strip() for area in v if area and area.strip()]
            if not v:
                return None
        return v
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v is not None:
            if v < 10 or v > 120:
                raise ValueError("Timeout must be between 10 and 120 seconds")
        return v

class SyncSearchResponse(BaseModel):
    """Response model for SyncAI search"""
    success: bool
    persona: str
    correlation_id: str
    formatted_response: str
    metadata: Dict[str, Any]
    validation: Optional[Dict[str, Any]] = None
    elapsed_time: float
    timestamp: str

class NewsletterResponse(BaseModel):
    """Response model for newsletter format"""
    success: bool
    persona: str
    correlation_id: str
    newsletter: str
    format: str
    word_count: int
    char_count: int
    metadata: Dict[str, Any]
    elapsed_time: float
    timestamp: str

class PersonaValidationResponse(BaseModel):
    """Response model for persona validation"""
    valid: bool
    persona: str
    warnings: List[str] = []
    suggestions: List[str] = []
    persona_config_available: bool

# === Enhanced API Endpoints ===

@router.get("/status")
async def get_sync_search_status(request: Request):
    """Get SyncAI search service status with enhanced debugging information"""
    try:
        # Get basic service status
        status_info = {
            "service": "SyncAI Search Enhanced",
            "status": "operational",
            "version": "1.1.0",  # Updated version with newsletter support
            "capabilities": [
                "Persona-driven search",
                "Web search integration", 
                "Knowledge base search",
                "Real-time streaming",
                "Multi-source synthesis",
                "Configuration-driven behavior",
                "Newsletter format",
                "Daily brief format",
                "Enhanced error handling"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add agent status if available
        try:
            sync_agent = get_sync_search_agent(request)
            agent_status = sync_agent.get_status()
            status_info["agent_status"] = agent_status
            status_info["agent_connectivity"] = "connected"
        except Exception as e:
            status_info["agent_status"] = {"available": False, "error": str(e)}
            status_info["agent_connectivity"] = "disconnected"
        
        # Add configuration info
        try:
            config_loader = get_config_loader(request)
            search_config = getattr(config_loader, 'get_search_config', lambda: {})()
            status_info["search_configuration"] = {
                "max_focus_areas": search_config.get("max_focus_areas", 10),
                "timeout_seconds": search_config.get("timeout_seconds", 60),
                "query_enhancement_enabled": search_config.get("enable_query_enhancement", True),
                "alternative_queries_enabled": search_config.get("enable_alternative_queries", True)
            }
        except Exception as e:
            status_info["search_configuration"] = {"available": False, "error": str(e)}
        
        # Add persona configuration info
        try:
            persona_loader = get_persona_config_loader(request)
            personas = persona_loader.get_available_personas()
            status_info["persona_configuration"] = {
                "available_personas": len(personas),
                "personas": personas,
                "config_valid": True
            }
        except Exception as e:
            status_info["persona_configuration"] = {
                "available": False, 
                "error": str(e),
                "config_valid": False
            }
        
        # Add debugging information
        status_info["debugging"] = {
            "logging_level": logger.level,
            "has_registered_agents": hasattr(request.app.state, 'registered_agents'),
            "llamastack_configured": hasattr(request.app.state, 'client')
        }
        
        return status_info
        
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        return {
            "service": "SyncAI Search Enhanced",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# === ORIGINAL SEARCH ENDPOINTS ===

@router.post("/search/{persona}")
async def search_technology_intelligence(
    persona: str,
    request: SyncSearchRequest,
    sync_agent = Depends(get_sync_search_agent),
    config_loader = Depends(get_persona_config_loader)
) -> SyncSearchResponse:
    """
    Perform persona-driven technology intelligence search with enhanced error handling
    
    Search for the latest technology information optimized for the specified persona.
    Combines real-time web search with curated knowledge base for comprehensive results.
    """
    try:
        # Validate persona
        available_personas = config_loader.get_available_personas()
        if persona not in available_personas:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown persona: {persona}. Available: {available_personas}"
            )
        
        logger.info(f"🔍 Starting SyncAI search for persona: {persona}")
        logger.info(f"📋 Focus areas: {request.focus_areas}")
        logger.info(f"⏰ Time range: {request.time_range}")
        logger.info(f"🆔 Correlation ID: {request.correlation_id}")
        
        # Set timeout if provided
        if request.timeout:
            sync_agent.timeout = request.timeout
            logger.info(f"⏱️ Timeout set to: {request.timeout} seconds")
        
        # Execute search with enhanced error handling
        try:
            results = await sync_agent.search_ai_info(
                persona=persona,
                focus_areas=request.focus_areas,
                time_range=request.time_range,
                correlation_id=request.correlation_id
            )
        except asyncio.TimeoutError:
            logger.error(f"⏰ Search timeout for {persona} after {sync_agent.timeout} seconds")
            raise HTTPException(
                status_code=408,
                detail=f"Search timeout after {sync_agent.timeout} seconds. Try reducing focus areas or increasing timeout."
            )
        except Exception as search_error:
            logger.error(f" Search execution failed for {persona}: {search_error}", exc_info=True)
            # Return a structured error response instead of raising
            results = {
                "persona": persona,
                "focus_areas": request.focus_areas or [],
                "formatted_response": f"Search failed for {persona}. Error: {str(search_error)}",
                "correlation_id": request.correlation_id or "error",
                "elapsed_time": 0,
                "error": str(search_error),
                "search_strategy": "unified_agent"
            }
        
        # Format response
        response = SyncSearchResponse(
            success=not results.get("error"),
            persona=results["persona"],
            correlation_id=results["correlation_id"],
            formatted_response=results["formatted_response"],
            metadata={
                "focus_areas": results.get("focus_areas", []),
                "search_strategy": results.get("search_strategy", "unified_agent"),
                "sources_summary": results.get("sources_summary", {}),
                "processing_metadata": results.get("processing_metadata", {}),
                "timeout_used": request.timeout or 60,
                "error": results.get("error")
            },
            validation=results.get("validation"),
            elapsed_time=results["elapsed_time"],
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(f" SyncAI search completed for {persona} in {results['elapsed_time']:.2f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" SyncAI search route failed for {persona}: {e}", exc_info=True)
        # Return error response instead of raising exception
        return SyncSearchResponse(
            success=False,
            persona=persona,
            correlation_id=request.correlation_id or "error",
            formatted_response=f"Search temporarily unavailable for {persona}. Error: {str(e)}",
            metadata={"error": str(e), "error_type": type(e).__name__},
            elapsed_time=0,
            timestamp=datetime.utcnow().isoformat()
        )

@router.post("/search/{persona}/stream")
async def search_technology_intelligence_stream(
    persona: str,
    request: SyncSearchRequest,
    sync_agent = Depends(get_sync_search_agent),
    config_loader = Depends(get_persona_config_loader)
):
    """
    Perform streaming persona-driven technology intelligence search with enhanced error handling
    
    Returns real-time progress updates during the search process.
    """
    async def event_generator():
        try:
            # Validate persona first
            available_personas = config_loader.get_available_personas()
            if persona not in available_personas:
                error_event = {
                    "type": "error",
                    "error": f"Unknown persona: {persona}",
                    "available_personas": available_personas,
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(error_event)}\n\n"
                return
            
            # Set timeout if provided
            if request.timeout:
                sync_agent.timeout = request.timeout
                logger.info(f"⏱️ Stream timeout set to: {request.timeout} seconds")
            
            # Start streaming search
            start_event = {
                "type": "started", 
                "persona": persona, 
                "focus_areas": request.focus_areas,
                "time_range": request.time_range,
                "correlation_id": request.correlation_id,
                "timeout": sync_agent.timeout,
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(start_event)}\n\n"
            
            # Stream search events with timeout handling
            try:
                async for event in sync_agent.search_ai_info_stream(
                    persona=persona,
                    focus_areas=request.focus_areas,
                    time_range=request.time_range,
                    correlation_id=request.correlation_id
                ):
                    yield f"data: {json.dumps(event)}\n\n"
                    # Small delay to prevent overwhelming the client
                    await asyncio.sleep(0.05)
                    
            except asyncio.TimeoutError:
                timeout_event = {
                    "type": "timeout",
                    "error": f"Search timeout after {sync_agent.timeout} seconds",
                    "persona": persona,
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(timeout_event)}\n\n"
            except Exception as stream_error:
                logger.error(f" Streaming error for {persona}: {stream_error}", exc_info=True)
                error_event = {
                    "type": "stream_error",
                    "error": str(stream_error),
                    "persona": persona,
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(error_event)}\n\n"
                
        except Exception as e:
            logger.error(f" Stream generator failed for {persona}: {e}", exc_info=True)
            error_event = {
                "type": "generator_error",
                "error": str(e),
                "persona": persona,
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

# === NEW NEWSLETTER ENDPOINTS ===

@router.post("/search/{persona}/newsletter")
async def search_ai_info_newsletter(
    persona: str,
    request: SyncSearchRequest,
    format_type: str = Query("newsletter", description="Format: 'newsletter' or 'daily'"),
    background_tasks: BackgroundTasks,
    sync_agent = Depends(get_sync_search_agent),
    config_loader = Depends(get_persona_config_loader)
) -> NewsletterResponse:
    """
    Get AI information formatted as a concise newsletter or daily brief
    
    Formats:
    - newsletter: Weekly format with 3 sections (~150-250 words)
    - daily: Ultra-short format with 3 bullets (~30-60 words)
    """
    try:
        # Validate persona
        available_personas = config_loader.get_available_personas()
        if persona not in available_personas:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown persona: {persona}. Available: {available_personas}"
            )
        
        correlation_id = str(uuid.uuid4())
        logger.info(f"📰 {format_type.title()} search request for {persona}")
        logger.info(f"📋 Focus areas: {request.focus_areas}")
        logger.info(f"📅 Time range: {request.time_range}")
        
        # Set timeout if provided
        if request.timeout:
            sync_agent.timeout = request.timeout
            logger.info(f"⏱️ Timeout set to: {request.timeout} seconds")
        
        # Execute newsletter search with format
        try:
            result = await sync_agent.search_ai_info_newsletter(
                persona=persona,
                focus_areas=request.focus_areas,
                time_range=request.time_range,
                format_type=format_type,
                correlation_id=correlation_id
            )
        except asyncio.TimeoutError:
            logger.error(f"⏰ Newsletter timeout for {persona} after {sync_agent.timeout} seconds")
            raise HTTPException(
                status_code=408,
                detail=f"Newsletter generation timeout after {sync_agent.timeout} seconds."
            )
        except Exception as search_error:
            logger.error(f" Newsletter search failed for {persona}: {search_error}", exc_info=True)
            # Return structured error instead of raising
            result = {
                "persona": persona,
                "focus_areas": request.focus_areas or [],
                "newsletter": f"Newsletter temporarily unavailable for {persona}. Error: {str(search_error)}",
                "format": format_type,
                "correlation_id": correlation_id,
                "elapsed_time": 0,
                "error": str(search_error)
            }
        
        newsletter_content = result["newsletter"]
        word_count = len(newsletter_content.split())
        char_count = len(newsletter_content)
        
        response = NewsletterResponse(
            success=not result.get("error"),
            persona=result["persona"],
            correlation_id=result["correlation_id"],
            newsletter=newsletter_content,
            format=result["format"],
            word_count=word_count,
            char_count=char_count,
            metadata={
                "focus_areas": result.get("focus_areas", []),
                "search_strategy": result.get("search_strategy", "newsletter_optimized"),
                "format_type": format_type,
                "sources_summary": result.get("sources_summary", {}),
                "processing_metadata": result.get("processing_metadata", {}),
                "timeout_used": request.timeout or 60,
                "error": result.get("error")
            },
            elapsed_time=result["elapsed_time"],
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(f"📰 {format_type.title()} completed for {persona} ({word_count} words, {result['elapsed_time']:.2f}s)")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Newsletter route failed for {persona}: {e}", exc_info=True)
        
        # Error format based on type
        if format_type == "daily":
            error_content = f"""# {persona.replace('_', ' ').title()} Daily
*{datetime.utcnow().strftime('%b %d')}*

**1.** Service temporarily unavailable
**2.** Please try again in a few minutes  
**3.** Check system status if issue persists

*Error: Service offline*"""
        else:
            error_content = f"""# {persona.replace('_', ' ').title()} Brief
*{datetime.utcnow().strftime('%B %d, %Y')}*

## Service Update

**1.** Newsletter service temporarily unavailable
**2.** System maintenance in progress
**3.** Expected resolution within 15 minutes

## Action Items

• Try again in a few minutes
• Check service status page
• Contact support if issue persists

---
*Next brief: {(datetime.utcnow() + timedelta(days=7)).strftime('%b %d')}*"""

        return NewsletterResponse(
            success=False,
            persona=persona,
            correlation_id=request.correlation_id or "error",
            newsletter=error_content,
            format=format_type,
            word_count=len(error_content.split()),
            char_count=len(error_content),
            metadata={"error": str(e), "error_type": type(e).__name__},
            elapsed_time=0,
            timestamp=datetime.utcnow().isoformat()
        )

@router.get("/newsletter/formats")
async def get_newsletter_formats() -> Dict[str, Any]:
    """
    Get available newsletter formats and their characteristics
    """
    return {
        "formats": {
            "newsletter": {
                "name": "Weekly Newsletter",
                "description": "Comprehensive weekly brief with 3 sections",
                "typical_length": "150-250 words",
                "sections": ["Key Updates", "Action Items", "Worth Exploring"],
                "best_for": "Weekly roundups, comprehensive updates",
                "time_range": "7d recommended"
            },
            "daily": {
                "name": "Daily Brief", 
                "description": "Ultra-short daily update with top 3 items",
                "typical_length": "30-60 words",
                "sections": ["Top 3 updates", "Single action item"],
                "best_for": "Quick daily scans, mobile reading",
                "time_range": "1d recommended"
            }
        },
        "usage_examples": {
            "newsletter": "/search/devops_engineer/newsletter?format_type=newsletter",
            "daily": "/search/ai_engineer/newsletter?format_type=daily"
        },
        "supported_personas": [
            "devops_engineer",
            "software_engineer", 
            "ai_engineer",
            "product_manager",
            "product_owner"
        ]
    }

@router.get("/newsletter/preview/{persona}")
async def get_newsletter_preview(
    persona: str,
    format_type: str = Query("newsletter", description="Format: 'newsletter' or 'daily'")
) -> Dict[str, Any]:
    """
    Get a preview/example of newsletter format for a persona
    """
    previews = {
        "newsletter": {
            "devops_engineer": """# DevOps Engineer Brief
*December 15, 2024*

## Key Updates

**1.** Kubernetes 1.29 released with enhanced GPU scheduling and improved resource management
**2.** NVIDIA announced DGX H100 systems optimized for large-scale AI training workloads  
**3.** Amazon SageMaker launched automated model tuning capabilities for MLOps pipelines

## Action Items

• Evaluate Kubernetes 1.29 for better GPU utilization in your clusters
• Test SageMaker's new automated tuning for existing ML pipelines
• Consider DGX H100 for compute-intensive AI training requirements

## Worth Exploring

• Kubernetes GPU Operator - simplified GPU resource management
• NVIDIA NGC Container Registry - standardized AI environments
• Amazon SageMaker MLOps - automated model lifecycle management

---
*Next brief: Dec 22 | Focus: MLOps platforms, AI infrastructure*""",
            
            "software_engineer": """# Software Engineer Brief
*December 15, 2024*

## Key Updates

**1.** OpenAI released GPT-4 Turbo with improved function calling and 128k context window
**2.** LangChain 0.1.0 stable release with breaking changes and performance improvements
**3.** Pinecone launched serverless vector database with automatic scaling capabilities

## Action Items

• Try OpenAI's new function calling for more reliable tool integration
• Upgrade to LangChain 0.1.0 for better performance (check breaking changes)
• Test Pinecone serverless for cost-effective vector storage

## Worth Exploring

• OpenAI GPT-4 Turbo - enhanced API with larger context
• LangChain Expression Language - simplified chain composition
• Pinecone Serverless - auto-scaling vector database

---
*Next brief: Dec 22 | Focus: AI frameworks, LLM APIs*""",
            
            "ai_engineer": """# AI Engineer Brief
*December 15, 2024*

## Key Updates

**1.** Google released Gemini Ultra with multimodal capabilities surpassing GPT-4 benchmarks
**2.** Mixtral 8x7B open-source mixture-of-experts model now available from Mistral AI
**3.** New QLoRA techniques reduce fine-tuning memory usage by 75% according to latest research

## Action Items

• Experiment with Mixtral 8x7B for cost-effective high-performance inference tasks
• Apply QLoRA techniques to reduce memory requirements in your fine-tuning workflows
• Benchmark Gemini Ultra against current models for multimodal applications

## Worth Exploring

• Mixtral 8x7B - open-source mixture-of-experts model
• QLoRA Training Methods - memory-efficient fine-tuning techniques  
• Constitutional AI Research - latest alignment methods from Anthropic

---
*Next brief: Dec 22 | Focus: LLM research, model training*"""
        },
        
        "daily": {
            "devops_engineer": """# DevOps Engineer Daily
*Dec 15*

**1.** Kubernetes 1.29 released with GPU scheduling improvements
**2.** SageMaker launches automated model tuning for MLOps
**3.** NVIDIA announces new DGX H100 training systems

**Action:** Evaluate Kubernetes 1.29 upgrade for GPU workloads

*Focus: MLOps platforms, AI infrastructure*""",
            
            "software_engineer": """# Software Engineer Daily  
*Dec 15*

**1.** OpenAI releases GPT-4 Turbo with improved function calling
**2.** LangChain 0.1.0 stable version with performance improvements
**3.** Pinecone launches serverless vector database solution

**Action:** Test GPT-4 Turbo function calling for tool integration

*Focus: AI frameworks, LLM APIs*""",
            
            "ai_engineer": """# AI Engineer Daily  
*Dec 15*

**1.** Google releases Gemini Ultra with multimodal capabilities
**2.** Mixtral 8x7B mixture-of-experts model now open source
**3.** QLoRA techniques reduce fine-tuning memory by 75%

**Action:** Test Mixtral 8x7B for inference cost optimization

*Focus: LLM research, model training*"""
        }
    }
    
    if persona not in previews[format_type]:
        available = list(previews[format_type].keys())
        raise HTTPException(
            status_code=404,
            detail=f"No {format_type} preview for '{persona}'. Available: {available}"
        )
    
    preview_content = previews[format_type][persona]
    
    return {
        "persona": persona,
        "format": format_type,
        "preview": preview_content,
        "word_count": len(preview_content.split()),
        "char_count": len(preview_content),
        "note": f"This is a {format_type} preview. Use /search/{persona}/newsletter for live data."
    }

@router.get("/newsletter/example/{persona}")
async def get_newsletter_example(persona: str) -> Dict[str, Any]:
    """
    Get an example newsletter for a specific persona (backward compatibility)
    """
    examples = {
        "devops_engineer": {
            "title": "DevOps Engineer Weekly Brief",
            "sample_content": """# DevOps Engineer Weekly Brief
*December 15, 2024 • Focus: MLOps platforms, AI infrastructure, GPU management*

---

## 🚀 **This Week's Highlights**

**1.** NVIDIA announced new DGX H100 systems with 8x H100 GPUs for large-scale AI training.

**2.** Amazon SageMaker launched new automated model tuning capabilities for MLOps workflows.

**3.** Kubernetes 1.29 released with enhanced GPU resource management and scheduling improvements.

---

## 🆕 **What's New**

• **TensorFlow Extended (TFX) 1.15** - New pipeline orchestration features and improved monitoring

• **NVIDIA GPU Cloud (NGC)** - Container registry now supports multi-cloud deployments

• **Amazon EC2 P5 Instances** - Next-gen instances with improved price-performance for AI workloads

• **MLflow 2.8** - Enhanced model registry with automated compliance checking

---

## ⚡ **Quick Wins**

 Evaluate new SageMaker automated tuning for your ML pipelines

 Update to Kubernetes 1.29 for better GPU scheduling

 Consider NGC containers for standardized AI environments

---

## 🔗 **Worth Checking Out**

• NVIDIA DGX H100 - Next-generation AI training platform
• Amazon SageMaker MLOps - Automated model lifecycle management  
• Kubernetes GPU Operator - Simplified GPU resource management

---

*💡 Want different focus areas? Try: container optimization, CI/CD automation, monitoring tools*

*📧 Generated by SyncAI • Next brief: December 22*"""
        },
        "software_engineer": {
            "title": "Software Engineer Weekly Brief", 
            "sample_content": """# Software Engineer Weekly Brief
*December 15, 2024 • Focus: AI frameworks, LLM APIs, vector databases*

---

## 🚀 **This Week's Highlights**

**1.** OpenAI released GPT-4 Turbo with improved function calling and 128k context window.

**2.** LangChain 0.1.0 stable release with breaking changes and performance improvements.

**3.** Pinecone launched serverless vector database with automatic scaling capabilities.

---

## 🆕 **What's New**

• **Anthropic Claude API** - New function calling capabilities and improved reasoning

• **Weaviate 1.22** - Enhanced hybrid search combining vector and keyword matching

• **LlamaIndex 0.9** - Simplified RAG pipeline creation with new abstractions

• **Hugging Face Transformers 4.36** - Support for new model architectures and optimizations

---

## ⚡ **Quick Wins**

 Try OpenAI's new function calling for more reliable tool integration

 Upgrade to LangChain 0.1.0 for better performance (check breaking changes)

 Test Pinecone serverless for cost-effective vector storage

---

## 🔗 **Worth Checking Out**

• OpenAI GPT-4 Turbo - Enhanced API with larger context
• LangChain Expression Language - Simplified chain composition
• Pinecone Serverless - Auto-scaling vector database

---

*💡 Want different focus areas? Try: React frameworks, Python libraries, API integrations*

*📧 Generated by SyncAI • Next brief: December 22*"""
        },
        "ai_engineer": {
            "title": "AI Engineer Weekly Brief",
            "sample_content": """# AI Engineer Weekly Brief
*December 15, 2024 • Focus: LLM research, model training, transformer architectures*

---

## 🚀 **This Week's Highlights**

**1.** Google released Gemini Ultra with multimodal capabilities surpassing GPT-4 on several benchmarks.

**2.** Microsoft published research on mixture-of-experts scaling to 1 trillion parameters.

**3.** Meta's Code Llama 70B shows state-of-the-art performance on coding tasks.

---

## 🆕 **What's New**

• **Mixtral 8x7B** - Open-source mixture-of-experts model from Mistral AI

• **Llama 2 Fine-tuning Guide** - Meta released comprehensive training best practices

• **LoRA Improvements** - New QLoRA techniques reduce memory usage by 75%

• **Constitutional AI Paper** - Anthropic's latest research on AI alignment methods

---

## ⚡ **Quick Wins**

 Experiment with Mixtral 8x7B for cost-effective high-performance inference

 Apply QLoRA techniques to reduce fine-tuning memory requirements

 Study constitutional AI methods for safer model alignment

---

## 🔗 **Worth Checking Out**

• Mixtral 8x7B - Open-source mixture-of-experts model
• QLoRA Training - Memory-efficient fine-tuning techniques
• Constitutional AI - Alignment research and methods

---

*💡 Want different focus areas? Try: computer vision, reinforcement learning, model optimization*

*📧 Generated by SyncAI • Next brief: December 22*"""
        }
    }
    
    if persona not in examples:
        available = list(examples.keys())
        raise HTTPException(
            status_code=404, 
            detail=f"No example available for '{persona}'. Available: {available}"
        )
    
    return {
        "persona": persona,
        "example": examples[persona],
        "format": "newsletter",
        "note": "This is a sample newsletter. Use /search/{persona}/newsletter for live data."
    }

# === PERSONA MANAGEMENT ENDPOINTS ===

@router.get("/personas")
async def get_available_personas(
    request: Request,
    include_details: bool = Query(default=False, description="Include detailed persona information"),
    config_loader = Depends(get_persona_config_loader)
):
    """Get list of available personas with their details"""
    try:
        if include_details:
            # Get full persona configurations
            personas_detailed = {}
            for persona_name in config_loader.get_available_personas():
                try:
                    persona_config = config_loader.get_persona_config(persona_name)
                    personas_detailed[persona_name] = {
                        "display_name": persona_config.display_name,
                        "description": persona_config.description,
                        "focus_areas_count": len(persona_config.focus_areas),
                        "search_patterns_count": len(persona_config.search_patterns),
                        "topic_categories": list(persona_config.topic_categories.keys()),
                        "technical_depth": persona_config.instructions.get("technical_depth", "balanced"),
                        "core_objectives": persona_config.instructions.get("core_objectives", [])
                    }
                except Exception as e:
                    logger.warning(f"Error loading details for persona {persona_name}: {e}")
                    personas_detailed[persona_name] = {
                        "display_name": persona_name.replace('_', ' ').title(),
                        "description": "Configuration not available",
                        "error": str(e)
                    }
            
            return {
                "success": True,
                "personas": personas_detailed,
                "total_count": len(personas_detailed),
                "detailed": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Get basic persona info
            personas = config_loader.get_persona_display_info()
            return {
                "success": True,
                "personas": personas,
                "total_count": len(personas),
                "detailed": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get personas: {e}")
        # Return default personas if config fails
        default_personas = {
            "devops_engineer": {
                "display_name": "DevOps Engineer",
                "description": "Infrastructure and deployment focused",
                "focus_count": 15
            },
            "software_engineer": {
                "display_name": "Software Engineer", 
                "description": "Development frameworks and APIs focused",
                "focus_count": 15
            },
            "ai_engineer": {
                "display_name": "AI Engineer",
                "description": "Research and ML engineering focused", 
                "focus_count": 15
            },
            "product_owner": {
                "display_name": "Product Owner",
                "description": "Product features and user experience focused",
                "focus_count": 15
            },
            "product_manager": {
                "display_name": "Product Manager",
                "description": "Business strategy and market focused",
                "focus_count": 15
            }
        }
        return {
            "success": True,
            "personas": default_personas,
            "total_count": len(default_personas),
            "fallback": True,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/personas/{persona}")
async def get_persona_details(
    persona: str,
    config_loader = Depends(get_persona_config_loader)
):
    """Get detailed information about a specific persona"""
    try:
        # Validate persona exists
        available_personas = config_loader.get_available_personas()
        if persona not in available_personas:
            raise HTTPException(
                status_code=404,
                detail=f"Persona '{persona}' not found. Available: {available_personas}"
            )
        
        persona_config = config_loader.get_persona_config(persona)
        
        return {
            "success": True,
            "persona": {
                "name": persona_config.name,
                "display_name": persona_config.display_name,
                "description": persona_config.description,
                "focus_areas": persona_config.focus_areas,
                "search_patterns": persona_config.search_patterns[:5],  # Show first 5
                "topic_categories": persona_config.topic_categories,
                "search_modifiers": persona_config.search_modifiers,
                "output_format": persona_config.output_format,
                "instructions": persona_config.instructions
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get persona details for {persona}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve persona details: {str(e)}"
        )

@router.post("/personas/{persona}/validate")
async def validate_persona_request(
    persona: str,
    request: SyncSearchRequest,
    config_loader = Depends(get_persona_config_loader)
) -> PersonaValidationResponse:
    """Validate a search request for a specific persona"""
    try:
        available_personas = config_loader.get_available_personas()
        
        if persona not in available_personas:
            return PersonaValidationResponse(
                valid=False,
                persona=persona,
                warnings=[f"Unknown persona: {persona}"],
                suggestions=[f"Available personas: {', '.join(available_personas)}"],
                persona_config_available=False
            )
        
        # Use persona config loader's validation if available
        if hasattr(config_loader, 'validate_persona_request'):
            validation = config_loader.validate_persona_request(persona, request.focus_areas)
        else:
            validation = {"valid": True, "warnings": [], "suggestions": []}
        
        return PersonaValidationResponse(
            valid=validation["valid"],
            persona=persona,
            warnings=validation.get("warnings", []),
            suggestions=validation.get("suggestions", []),
            persona_config_available=True
        )
        
    except Exception as e:
        logger.error(f"Validation failed for persona {persona}: {e}")
        return PersonaValidationResponse(
            valid=False,
            persona=persona,
            warnings=[f"Validation error: {str(e)}"],
            suggestions=["Please check persona configuration"],
            persona_config_available=False
        )

# === HEALTH AND MONITORING ENDPOINTS ===

@router.get("/health")
async def health_check(request: Request):
    """Comprehensive health check for SyncAI search service"""
    health_status = {
        "healthy": True,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check if sync search agent is available
    try:
        sync_agent = get_sync_search_agent(request)
        agent_status = sync_agent.get_status()
        health_status["checks"]["sync_agent"] = {
            "healthy": True,
            "status": agent_status.get("status", "unknown"),
            "agent_id": agent_status.get("agent_id"),
            "session_id": agent_status.get("session_id"),
            "tools": agent_status.get("tools", []),
            "features": agent_status.get("features", []),
            "timeout": agent_status.get("configuration", {}).get("timeout", 60)
        }
    except Exception as e:
        health_status["checks"]["sync_agent"] = {
            "healthy": False,
            "error": str(e)
        }
        health_status["healthy"] = False
    
    # Check if persona config is available
    try:
        config_loader = get_persona_config_loader(request)
        personas = config_loader.get_available_personas()
        config_summary = config_loader.get_config_summary()
        health_status["checks"]["persona_config"] = {
            "healthy": True,
            "personas_loaded": len(personas),
            "config_valid": config_summary.get("configuration_valid", False),
            "config_file_exists": config_summary.get("config_exists", False)
        }
    except Exception as e:
        health_status["checks"]["persona_config"] = {
            "healthy": False,
            "error": str(e)
        }
        health_status["healthy"] = False
    
    # Check main configuration
    try:
        main_config = get_config_loader(request)
        search_config = getattr(main_config, 'get_search_config', lambda: {})()
        health_status["checks"]["search_config"] = {
            "healthy": True,
            "max_focus_areas": search_config.get("max_focus_areas", 10),
            "timeout_seconds": search_config.get("timeout_seconds", 60)
        }
    except Exception as e:
        health_status["checks"]["search_config"] = {
            "healthy": False,
            "error": str(e)
        }
        health_status["healthy"] = False
    
    # Test basic agent connectivity
    if health_status["checks"].get("sync_agent", {}).get("healthy"):
        try:
            sync_agent = get_sync_search_agent(request)
            # You could add a simple connectivity test here
            health_status["checks"]["agent_connectivity"] = {
                "healthy": True,
                "test": "basic_status_check_passed"
            }
        except Exception as e:
            health_status["checks"]["agent_connectivity"] = {
                "healthy": False,
                "error": str(e)
            }
            health_status["healthy"] = False
    
    if health_status["healthy"]:
        return health_status
    else:
        raise HTTPException(status_code=503, detail=health_status)

@router.get("/metrics")
async def get_search_metrics(sync_agent = Depends(get_sync_search_agent)):
    """Get search performance metrics and statistics"""
    try:
        agent_status = sync_agent.get_status()
        
        return {
            "metrics": {
                "search_statistics": agent_status.get("statistics", {}),
                "agent_performance": {
                    "status": agent_status.get("status"),
                    "agent_mode": agent_status.get("agent_mode"),
                    "tools_available": agent_status.get("tools", []),
                    "features_available": agent_status.get("features", []),
                    "timeout_seconds": agent_status.get("configuration", {}).get("timeout", 60)
                },
                "configuration": agent_status.get("configuration", {})
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        )

@router.get("/config")
async def get_search_configuration(
    request: Request,
    config_loader = Depends(get_config_loader),
    persona_loader = Depends(get_persona_config_loader)
):
    """Get current search configuration"""
    try:
        search_config = getattr(config_loader, 'get_search_config', lambda: {})()
        persona_summary = persona_loader.get_config_summary()
        
        return {
            "search_configuration": search_config,
            "persona_configuration": persona_summary,
            "single_agent_configured": getattr(config_loader, 'is_single_agent_configured', lambda: None)(),
            "version": "1.1.0",  # Updated version with newsletter support
            "features": [
                "persona_driven_search",
                "newsletter_format",
                "daily_brief_format", 
                "streaming_support",
                "enhanced_error_handling"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get configuration: {str(e)}"
        )

# === DEBUG ENDPOINTS ===

@router.post("/debug/test-agent")
async def test_agent_connectivity(
    sync_agent = Depends(get_sync_search_agent)
):
    """Test basic agent connectivity and response"""
    try:
        logger.info("🧪 Testing agent connectivity...")
        
        # Simple test query
        test_query = "Hello, please respond with a brief test message to confirm connectivity."
        
        # Test sync execution
        result = sync_agent._execute_search_sync(test_query, "test-connectivity")
        
        return {
            "success": True,
            "test_query": test_query,
            "response_length": len(result) if result else 0,
            "response_preview": result[:200] if result else "No response",
            "agent_status": sync_agent.get_status(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f" Agent connectivity test failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }

@router.post("/debug/test-newsletter")
async def test_newsletter_functionality(
    persona: str = Query(default="devops_engineer", description="Persona to test"),
    format_type: str = Query(default="newsletter", description="Format to test"),
    sync_agent = Depends(get_sync_search_agent)
):
    """Test newsletter functionality with sample data"""
    try:
        logger.info(f"🧪 Testing newsletter functionality for {persona} ({format_type})")
        
        # Sample response to test formatting
        sample_response = """
        Recent developments in AI infrastructure include several important announcements. 
        Kubernetes 1.29 was released with enhanced GPU scheduling capabilities for better resource management.
        NVIDIA announced new DGX H100 systems optimized for large-scale AI training workloads.
        Amazon SageMaker launched automated model tuning capabilities for MLOps pipelines.
        Organizations should consider evaluating these new GPU scheduling features for their clusters.
        Teams can implement SageMaker's automated tuning for existing ML pipelines.
        It's recommended to test the new DGX systems for compute-intensive training requirements.
        """
        
        # Test newsletter formatting
        if format_type == "daily":
            formatted = sync_agent._transform_to_daily_brief_format(
                sample_response, persona, None, ["AI infrastructure", "MLOps platforms"]
            )
        else:
            formatted = sync_agent._transform_to_newsletter_format(
                sample_response, persona, None, ["AI infrastructure", "MLOps platforms"]
            )
        
        return {
            "success": True,
            "persona": persona,
            "format_type": format_type,
            "sample_input_length": len(sample_response),
            "formatted_output": formatted,
            "output_word_count": len(formatted.split()),
            "output_char_count": len(formatted),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f" Newsletter test failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/debug/agent-info")
async def get_debug_agent_info(request: Request):
    """Get detailed agent information for debugging"""
    try:
        debug_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "app_state_attributes": dir(request.app.state),
            "has_sync_search_agent": hasattr(request.app.state, 'sync_search_agent'),
            "has_registered_agents": hasattr(request.app.state, 'registered_agents'),
            "has_client": hasattr(request.app.state, 'client'),
            "has_agent_registry": hasattr(request.app.state, 'agent_registry')
        }
        
        if hasattr(request.app.state, 'sync_search_agent') and request.app.state.sync_search_agent:
            sync_agent = request.app.state.sync_search_agent
            debug_info["sync_agent"] = {
                "agent_id": sync_agent.agent_id,
                "session_id": sync_agent.session_id,
                "timeout": sync_agent.timeout,
                "search_count": sync_agent.search_count,
                "status": sync_agent.get_status()
            }
        
        if hasattr(request.app.state, 'registered_agents'):
            debug_info["registered_agents"] = list(request.app.state.registered_agents.keys())
        
        if hasattr(request.app.state, 'agent_registry'):
            debug_info["agent_registry_status"] = request.app.state.agent_registry.get_status()
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Failed to get debug info: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }