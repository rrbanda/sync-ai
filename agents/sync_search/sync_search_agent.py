import time
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from llama_stack_client import LlamaStackClient
from llama_stack_client.types import UserMessage

logger = logging.getLogger("SyncSearchAgent")

class SyncSearchAgent:
    """
    WORKING SyncAI Search Agent with Newsletter/Daily Brief Support
    """

    def __init__(self, client: LlamaStackClient, agent_id: str, session_id: str, config_loader, timeout: int = 60):
        self.client = client
        self.agent_id = agent_id
        self.session_id = session_id
        self.config_loader = config_loader
        self.timeout = timeout

        self.search_count = 0
        self.total_search_time = 0.0
        self.last_search_time = None

        logger.info(f"🔍 SyncSearchAgent initialized (WORKING VERSION)")
        logger.info(f"🔧 Agent ID: {agent_id}")
        logger.info(f"📱 Session ID: {session_id}")
        logger.info(f"⚡ Mode: Single agent with Web Search + RAG tools")
        logger.info(f"⏱️ Timeout: {timeout} seconds")

    async def search_ai_info(self, persona: str, focus_areas: Optional[List[str]] = None, time_range: str = "30d", correlation_id: Optional[str] = None) -> Dict[str, Any]:
        correlation_id = correlation_id or str(uuid.uuid4())
        start_time = time.time()
        try:
            persona_config = None
            try:
                persona_config = self.config_loader.get_persona_config(persona)
                if not focus_areas:
                    focus_areas = persona_config.focus_areas[:3]
                logger.info(f" Loaded persona config for {persona}")
            except Exception as e:
                logger.warning(f"⚠️ Could not load persona config: {e}")
                focus_areas = focus_areas or ["AI developments", "technology trends"]

            search_query = self._build_working_search_query(persona, persona_config, focus_areas, time_range)
            logger.info(f"🔍 Executing search for {persona}")
            logger.info(f"📝 Query: {search_query}")

            search_results = self._execute_search_sync(search_query, correlation_id)
            formatted_response = self._format_response(search_results, persona, persona_config, focus_areas)
            elapsed_time = time.time() - start_time
            self._update_search_stats(elapsed_time)
            logger.info(f" Search completed for {persona} in {elapsed_time:.2f}s")
            logger.info(f"📊 Response length: {len(formatted_response)} characters")

            return {
                "persona": persona,
                "focus_areas": focus_areas,
                "formatted_response": formatted_response,
                "correlation_id": correlation_id,
                "elapsed_time": elapsed_time,
                "search_strategy": "working_simple_query",
                "sources_summary": {
                    "agent_mode": "single_agent_dual_tools",
                    "tools_used": ["builtin::websearch", "builtin::rag"],
                    "response_available": bool(search_results and search_results.strip())
                },
                "processing_metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_id": self.agent_id,
                    "session_id": self.session_id,
                    "tool_coordination": "automatic",
                    "query_type": "simple_trigger",
                    "response_length": len(search_results) if search_results else 0
                }
            }
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f" Search failed for {persona}: {e}", exc_info=True)
            return {
                "persona": persona,
                "focus_areas": focus_areas or [],
                "formatted_response": f"Search temporarily unavailable for {persona}. Please try again later.\n\nError: {str(e)}",
                "correlation_id": correlation_id,
                "elapsed_time": elapsed_time,
                "error": str(e),
                "search_strategy": "working_simple_query"
            }

    async def search_ai_info_newsletter(
        self,
        persona: str,
        focus_areas: Optional[List[str]] = None,
        time_range: str = "30d",
        format_type: str = "newsletter",
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate newsletter or daily brief for a persona.
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        start_time = time.time()
        logger.info(f"📰 Newsletter ({format_type}) generation for {persona} started.")
        try:
            # Step 1: Get the info (reuse your own logic)
            base_result = await self.search_ai_info(persona, focus_areas, time_range, correlation_id)
            newsletter_content = ""

            # Step 2: Transform to newsletter/daily format
            if format_type == "daily":
                newsletter_content = self._transform_to_daily_brief_format(
                    base_result.get("formatted_response", ""), persona, None, focus_areas
                )
            else:
                newsletter_content = self._transform_to_newsletter_format(
                    base_result.get("formatted_response", ""), persona, None, focus_areas
                )

            elapsed_time = time.time() - start_time
            word_count = len(newsletter_content.split())
            char_count = len(newsletter_content)

            logger.info(f"📰 Newsletter ({format_type}) generated for {persona} in {elapsed_time:.2f}s")
            return {
                "success": True,
                "persona": persona,
                "correlation_id": correlation_id,
                "newsletter": newsletter_content,
                "format": format_type,
                "word_count": word_count,
                "char_count": char_count,
                "focus_areas": base_result.get("focus_areas", []),
                "search_strategy": base_result.get("search_strategy", "newsletter_optimized"),
                "sources_summary": base_result.get("sources_summary", {}),
                "processing_metadata": base_result.get("processing_metadata", {}),
                "elapsed_time": elapsed_time,
            }
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f" Newsletter generation failed for {persona}: {e}", exc_info=True)
            return {
                "success": False,
                "persona": persona,
                "correlation_id": correlation_id,
                "newsletter": f"Newsletter service temporarily unavailable for {persona}. Error: {str(e)}",
                "format": format_type,
                "word_count": 0,
                "char_count": 0,
                "focus_areas": focus_areas or [],
                "search_strategy": "newsletter_optimized",
                "sources_summary": {},
                "processing_metadata": {},
                "elapsed_time": elapsed_time,
            }

    async def search_ai_info_stream(self, persona: str, focus_areas: Optional[List[str]] = None, time_range: str = "30d", correlation_id: Optional[str] = None):
        correlation_id = correlation_id or str(uuid.uuid4())
        start_time = time.time()
        try:
            yield {
                "type": "search_started",
                "persona": persona,
                "correlation_id": correlation_id,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Load persona configuration
            persona_config = None
            try:
                persona_config = self.config_loader.get_persona_config(persona)
                if not focus_areas:
                    focus_areas = persona_config.focus_areas[:3]
                yield {
                    "type": "persona_loaded",
                    "persona": persona,
                    "focus_areas": focus_areas,
                    "display_name": persona_config.display_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                focus_areas = focus_areas or ["AI developments", "technology trends"]
                yield {
                    "type": "warning",
                    "message": f"Using default configuration: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                }

            # Build search query
            search_query = self._build_working_search_query(persona, persona_config, focus_areas, time_range)
            yield {
                "type": "query_built",
                "message": f"Search query prepared: {search_query[:100]}...",
                "timestamp": datetime.utcnow().isoformat()
            }

            yield {
                "type": "search_executing",
                "message": "Executing search with automatic tool invocation",
                "timestamp": datetime.utcnow().isoformat()
            }

            # Execute streaming search
            search_results = ""
            try:
                user_message = UserMessage(content=search_query, role="user")
                logger.info(f"🚀 Starting LlamaStack request with simple query...")

                generator = self.client.agents.turn.create(
                    agent_id=self.agent_id,
                    session_id=self.session_id,
                    messages=[user_message],
                    stream=True
                )

                chunk_count = 0
                content_chunks = 0

                for chunk in generator:
                    chunk_count += 1
                    content = self._extract_content_from_chunk(chunk, chunk_count)
                    if content:
                        search_results += content
                        content_chunks += 1

                        # Yield progress updates every 50 chunks
                        if chunk_count % 50 == 0:
                            yield {
                                "type": "search_progress",
                                "message": f"Processing response... ({len(search_results)} chars received)",
                                "chunks_processed": chunk_count,
                                "content_chunks": content_chunks,
                                "timestamp": datetime.utcnow().isoformat()
                            }

                logger.info(f" Streaming completed. Total chunks: {chunk_count}, Content chunks: {content_chunks}, Response length: {len(search_results)}")

            except Exception as e:
                logger.error(f" Search execution failed: {e}", exc_info=True)
                search_results = f"Search execution failed: {str(e)}"

            yield {
                "type": "search_completed",
                "message": f"Search execution completed ({len(search_results)} chars)",
                "timestamp": datetime.utcnow().isoformat()
            }

            # Format response
            formatted_response = self._format_response(search_results, persona, persona_config, focus_areas)
            elapsed_time = time.time() - start_time
            self._update_search_stats(elapsed_time)

            yield {
                "type": "result",
                "persona": persona,
                "focus_areas": focus_areas,
                "formatted_response": formatted_response,
                "correlation_id": correlation_id,
                "elapsed_time": elapsed_time,
                "search_strategy": "working_simple_query",
                "sources_summary": {
                    "agent_mode": "single_agent_dual_tools",
                    "tools_used": ["builtin::websearch", "builtin::rag"],
                    "response_available": bool(search_results and search_results.strip())
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f" Streaming search failed for {persona}: {e}", exc_info=True)
            yield {
                "type": "error",
                "persona": persona,
                "error": str(e),
                "correlation_id": correlation_id,
                "elapsed_time": elapsed_time,
                "timestamp": datetime.utcnow().isoformat()
            }

    def _build_working_search_query(self, persona, persona_config, focus_areas, time_range):
        """
        Build SIMPLE search query following WORKING LlamaStack patterns
        """
        persona_display = persona_config.display_name if persona_config else persona.replace('_', ' ').title()
        focus_text = ', '.join(focus_areas)
        query = f"Search for the latest information about {focus_text}. Focus on developments relevant to a {persona_display}."
        return query

    def _execute_search_sync(self, search_query: str, correlation_id: str) -> str:
        """
        Execute search with proper error handling - SIMPLIFIED VERSION
        """
        try:
            logger.info(f"🔍 Executing search for correlation: {correlation_id}")
            user_message = UserMessage(content=search_query, role="user")

            generator = self.client.agents.turn.create(
                agent_id=self.agent_id,
                session_id=self.session_id,
                messages=[user_message],
                stream=True
            )
            full_response = ""
            chunk_count = 0
            content_chunks = 0
            start_time = time.time()

            for chunk in generator:
                chunk_count += 1
                current_time = time.time()
                if current_time - start_time > self.timeout:
                    logger.warning(f"⏰ Search timeout after {self.timeout} seconds")
                    break
                content = self._extract_content_from_chunk(chunk, chunk_count)
                if content:
                    full_response += content
                    content_chunks += 1
                if chunk_count % 100 == 0:
                    elapsed = current_time - start_time
                    logger.info(f"📊 Progress: {chunk_count} chunks ({content_chunks} with content), {len(full_response)} chars, {elapsed:.1f}s")

            elapsed_time = time.time() - start_time
            logger.info(f" Search completed in {elapsed_time:.2f}s")
            logger.info(f"📊 Total chunks: {chunk_count}, Content chunks: {content_chunks}, Response length: {len(full_response)}")
            if not full_response.strip():
                logger.warning(f"⚠️ Empty response received after {chunk_count} chunks")
                return f"No content extracted from {chunk_count} chunks. The agent may not be responding to the search query properly."
            return full_response.strip()

        except Exception as e:
            logger.error(f" Search execution failed: {e}", exc_info=True)
            return f"Search execution failed: {str(e)}"

    def _extract_content_from_chunk(self, chunk, chunk_number: int) -> str:
        """
        WORKING content extraction method for LlamaStack response chunks
        """
        try:
            if hasattr(chunk, "event") and chunk.event:
                if hasattr(chunk.event, "payload") and chunk.event.payload:
                    if hasattr(chunk.event.payload, "delta") and chunk.event.payload.delta:
                        if hasattr(chunk.event.payload.delta, "text"):
                            content = chunk.event.payload.delta.text
                            if isinstance(content, str):
                                return content
                    if hasattr(chunk.event.payload, "content"):
                        content = chunk.event.payload.content
                        if isinstance(content, str) and content.strip():
                            return content
            if hasattr(chunk, "delta") and chunk.delta:
                if hasattr(chunk.delta, "content"):
                    content = chunk.delta.content
                    if isinstance(content, str) and content.strip():
                        return content
                elif hasattr(chunk.delta, "text"):
                    content = chunk.delta.text
                    if isinstance(content, str) and content.strip():
                        return content
            if hasattr(chunk, "content"):
                content = chunk.content
                if isinstance(content, str) and content.strip():
                    return content
            if isinstance(chunk, str) and chunk.strip():
                return chunk
            if hasattr(chunk, 'choices') and chunk.choices:
                for choice in chunk.choices:
                    if hasattr(choice, 'delta') and hasattr(choice.delta, 'content'):
                        content = choice.delta.content
                        if isinstance(content, str) and content.strip():
                            return content
            return ""
        except Exception as e:
            if chunk_number <= 5:
                logger.debug(f"🔍 Error extracting content from chunk {chunk_number}: {e}")
            return ""

    def _format_response(self, search_results, persona, persona_config, focus_areas):
        """
        Format the response using persona configuration - SIMPLIFIED VERSION
        """
        if not search_results or not search_results.strip():
            display_name = persona_config.display_name if persona_config else persona.replace('_', ' ').title()
            return f"""# Search Results Unavailable

Unfortunately, no search results are currently available for {display_name}.

**Possible causes:**
- Web search tool may not be properly configured
- Knowledge base may be empty
- Network connectivity issues
- Agent may not be invoking tools automatically

**Requested focus areas:** {', '.join(focus_areas)}

**Troubleshooting tip:** Try simpler queries like "What's the latest in AI?" or "Search for recent ML developments"

Please check the system configuration and try again."""

        # Format the response with proper headers
        formatted = self._add_headers_and_structure(search_results, persona, persona_config, focus_areas)
        return formatted

    def _add_headers_and_structure(self, response: str, persona: str, persona_config, focus_areas: List[str]) -> str:
        """
        Add proper headers and structure to the response
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        display_name = persona_config.display_name if persona_config else persona.replace('_', ' ').title()

        if not response.startswith("#"):
            header = f"# 🔄 SyncAI Intelligence Report: {display_name}\n\n"
            header += f"**Focus Areas:** {', '.join(focus_areas)}\n"
            header += f"**Generated:** {timestamp}\n"
            if persona_config and hasattr(persona_config, 'description'):
                header += f"**Report Type:** {persona_config.description}\n"
            header += "\n---\n\n"
            response = header + response

        footer = f"\n\n---\n\n*This report was generated by SyncAI using automated tool invocation.*\n"
        footer += f"*Optimized for: {display_name}*\n"
        footer += f"*Report generated at {timestamp}*\n"
        if persona_config:
            core_objectives = persona_config.instructions.get("core_objectives", [])
            if core_objectives:
                footer += f"*Focus: {', '.join(core_objectives[:3])}*\n"

        return response + footer

    def _transform_to_newsletter_format(self, response: str, persona: str, persona_config, focus_areas):
        """
        Simple newsletter transformation: Markdown headers + numbered items.
        """
        today = datetime.utcnow().strftime("%B %d, %Y")
        display_name = persona.replace("_", " ").title()
        header = f"# {display_name} Weekly Brief\n*{today}*"
        key_updates = "\n\n## Key Updates\n\n"
        lines = [line.strip() for line in response.split("\n") if line.strip()]
        for i, line in enumerate(lines):
            key_updates += f"**{i+1}.** {line}\n"
        action_items = "\n\n## Action Items\n\n• Review these updates\n• Plan follow-ups\n• See documentation for details"
        footer = f"\n---\n*Generated by SyncAI — Next brief: {today}*"
        return f"{header}{key_updates}{action_items}{footer}"

    def _transform_to_daily_brief_format(self, response: str, persona: str, persona_config, focus_areas):
        """
        Ultra-short format: Top 3 bullets.
        """
        today = datetime.utcnow().strftime("%b %d")
        display_name = persona.replace("_", " ").title()
        bullets = []
        for line in response.split("\n"):
            if line.strip():
                bullets.append(f"**{len(bullets)+1}.** {line.strip()}")
            if len(bullets) >= 3:
                break
        bullets_text = "\n".join(bullets)
        action = "\n\n**Action:** Review top developments."
        footer = f"\n\n*Focus: {', '.join(focus_areas) if focus_areas else ''}*"
        return f"# {display_name} Daily\n*{today}*\n\n{bullets_text}{action}{footer}"

    def _update_search_stats(self, elapsed_time: float):
        self.search_count += 1
        self.total_search_time += elapsed_time
        self.last_search_time = datetime.utcnow()

    def get_status(self) -> Dict[str, Any]:
        avg_search_time = (self.total_search_time / self.search_count) if self.search_count > 0 else 0
        return {
            "status": "ready_working",
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "agent_mode": "single_agent_dual_tools_working",
            "tools": ["builtin::websearch", "builtin::rag"],
            "query_strategy": "simple_trigger_words",
            "statistics": {
                "total_searches": self.search_count,
                "total_search_time": round(self.total_search_time, 2),
                "average_search_time": round(avg_search_time, 2),
                "last_search": self.last_search_time.isoformat() if self.last_search_time else None
            },
            "configuration": {
                "timeout": self.timeout,
                "config_loader_available": bool(self.config_loader),
                "personas_available": len(self.config_loader.get_available_personas()) if self.config_loader else 0
            },
            "improvements": {
                "query_method": "simplified_following_working_patterns",
                "trigger_words": ["Search for", "latest", "information about"],
                "expected_behavior": "automatic_tool_invocation",
                "based_on": "successful_llamastack_notebook_patterns"
            }
        }

    # Utility: test simple search (optional)
    def test_simple_search(self, query: str) -> str:
        try:
            user_message = UserMessage(content=query, role="user")
            generator = self.client.agents.turn.create(
                agent_id=self.agent_id,
                session_id=self.session_id,
                messages=[user_message],
                stream=True
            )
            full_response = ""
            for chunk in generator:
                content = self._extract_content_from_chunk(chunk, 0)
                if content:
                    full_response += content
            return full_response.strip() if full_response.strip() else "No response received"
        except Exception as e:
            return f"Test failed: {str(e)}"

    def get_working_test_queries(self) -> List[str]:
        return [
            "Search for the latest AI developments",
            "What's new in machine learning?",
            "Find recent updates in MLOps platforms",
            "Search for latest Kubernetes features",
            "What are the recent developments in AI infrastructure?",
            "Find information about new AI frameworks",
            "Search for latest trends in DevOps automation",
            "What's the latest in containerization technology?"
        ]
