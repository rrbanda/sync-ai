#!/usr/bin/env python3
"""
Test script for the working SyncSearchAgent
Fixed for sync-ai project structure
"""

import sys
import os
import asyncio
import logging

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from llama_stack_client import LlamaStackClient
from agents.sync_search.sync_search_agent import SyncSearchAgent
from agents.sync_search.persona_config_loader import PersonaConfigLoader
from config.config import ConfigLoader

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestSyncSearch")

async def test_sync_search_agent():
    """Test the working SyncSearchAgent"""
    
    print("🧪 Testing SyncSearchAgent with Working Patterns")
    print("=" * 60)
    
    # Load configuration
    try:
        config_loader = ConfigLoader("config.yaml")
        llamastack_url = config_loader.get_llamastack_base_url()
        tavily_api_key = config_loader.get_tavily_api_key()
        
        print(f" Configuration loaded")
        print(f"📡 LlamaStack URL: {llamastack_url}")
        print(f"🔑 Tavily API Key: {' Found' if tavily_api_key else ' Missing'}")
        
        if not tavily_api_key:
            print(" Tavily API key not found. Please check your config.yaml")
            return
            
    except Exception as e:
        print(f" Failed to load configuration: {e}")
        return
    
    # Initialize client
    try:
        client = LlamaStackClient(
            base_url=llamastack_url,
            provider_data={"tavily_search_api_key": tavily_api_key}
        )
        print(" LlamaStack client initialized")
    except Exception as e:
        print(f" Failed to initialize client: {e}")
        return
    
    # Load persona config
    try:
        persona_config_loader = PersonaConfigLoader("persona_config.yaml")
        personas = persona_config_loader.get_available_personas()
        print(f" Persona config loaded ({len(personas)} personas)")
    except Exception as e:
        print(f"⚠️ Persona config failed, using defaults: {e}")
        persona_config_loader = None
    
    # Get agent details from your running system
    # You'll need to get these from your agent registry
    # For now, let's try to get them from the config
    try:
        agents_config = config_loader.get_agents_config()
        sync_agent = next((agent for agent in agents_config if agent.get("name") == "sync_search"), None)
        
        if not sync_agent:
            print(" sync_search agent not found in configuration")
            return
            
        print(f" Found sync_search agent configuration")
        
        # You'll need to replace these with actual IDs from your running system
        # Check your startup logs for the actual agent_id and session_id
        agent_id = "8f4736ab-bb90-409d-a9a5-f18be555b752"  # Replace with actual
        session_id = "e0284c5e-b657-4718-bab3-767b2213b5e4"  # Replace with actual
        
        print(f"📝 Using Agent ID: {agent_id}")
        print(f"📝 Using Session ID: {session_id}")
        print("⚠️ Make sure these IDs match your running system!")
        
    except Exception as e:
        print(f" Failed to get agent configuration: {e}")
        return
    
    # Initialize the working agent
    try:
        agent = SyncSearchAgent(
            client=client,
            agent_id=agent_id,
            session_id=session_id,
            config_loader=persona_config_loader,
            timeout=60
        )
        print(" SyncSearchAgent initialized")
    except Exception as e:
        print(f" Failed to initialize agent: {e}")
        return
    
    # Test 1: Simple search test
    print("\n🔍 Test 1: Simple search query")
    print("-" * 40)
    
    test_query = "Search for the latest AI developments"
    try:
        print(f"Query: {test_query}")
        result = agent.test_simple_search(test_query)
        print(f"Result length: {len(result)} characters")
        
        if "Search execution failed" in result:
            print(f" Search failed: {result}")
        elif len(result) > 100:
            print(" Received substantial response")
            print(f"Preview: {result[:200]}...")
        else:
            print(f"⚠️ Short response: {result}")
    except Exception as e:
        print(f" Test 1 failed: {e}")
    
    # Test 2: Persona-based search
    print("\n🎭 Test 2: Persona-based search")
    print("-" * 40)
    
    try:
        result = await agent.search_ai_info(
            persona="devops_engineer",
            focus_areas=["MLOps platforms", "AI infrastructure"],
            time_range="30d"
        )
        print(f"Persona: {result['persona']}")
        print(f"Focus areas: {result['focus_areas']}")
        print(f"Response length: {len(result['formatted_response'])} characters")
        print(f"Elapsed time: {result['elapsed_time']:.2f}s")
        
        if result.get('error'):
            print(f" Error: {result['error']}")
        elif result.get('sources_summary', {}).get('response_available'):
            print(" Search completed successfully")
            print(f"Preview: {result['formatted_response'][:200]}...")
        else:
            print("⚠️ No response available")
            
    except Exception as e:
        print(f" Test 2 failed: {e}")
    
    # Test 3: Get working test queries
    print("\n📝 Test 3: Recommended test queries")
    print("-" * 40)
    
    test_queries = agent.get_working_test_queries()
    print("Try these queries for best results:")
    for i, query in enumerate(test_queries[:5], 1):
        print(f"{i}. {query}")
    
    # Test 4: Agent status
    print("\n📊 Test 4: Agent status")
    print("-" * 40)
    
    status = agent.get_status()
    print(f"Status: {status['status']}")
    print(f"Agent mode: {status['agent_mode']}")
    print(f"Tools: {status['tools']}")
    print(f"Query strategy: {status['query_strategy']}")
    print(f"Total searches: {status['statistics']['total_searches']}")
    
    print("\n🎉 Testing completed!")
    print("=" * 60)
    
    return agent

def test_simple_patterns():
    """Test the basic patterns that should work"""
    
    print("\n🧪 Testing Simple Query Patterns")
    print("=" * 60)
    
    # These are the patterns that work based on the notebook
    working_patterns = [
        "Search for the latest information about AI developments",
        "What's the latest in machine learning?",
        "Find recent updates in MLOps platforms", 
        "Search for latest Kubernetes features",
        "What are the recent developments in AI infrastructure?",
        "Find information about new AI frameworks"
    ]
    
    print(" Working query patterns (use these for testing):")
    for i, pattern in enumerate(working_patterns, 1):
        print(f"{i}. {pattern}")
    
    print("\n Avoid these complex patterns:")
    avoid_patterns = [
        "Complex multi-step instructions",
        "Verbose requirements lists",
        "Asking for specific formatting without search trigger words",
        "Queries without 'search', 'latest', 'find', or 'what's new'"
    ]
    
    for pattern in avoid_patterns:
        print(f"- {pattern}")

def get_actual_agent_info():
    """Helper function to get actual agent IDs from your system"""
    print("\n🔍 Getting Agent Information")
    print("-" * 40)
    print("To get the actual agent_id and session_id for your system:")
    print("1. Check your startup logs for these lines:")
    print("   'Found existing agent: sync_search with ID: [AGENT_ID]'")
    print("   'Created session [SESSION_ID] for agent: sync_search'")
    print("2. Or call the API endpoint: GET /api/agents/status")
    print("3. Update the agent_id and session_id variables in this script")
    print("4. Current values are from your startup logs - they should work!")

async def main():
    """Main test function"""
    try:
        # Show how to get actual agent info
        get_actual_agent_info()
        
        # Run the comprehensive test
        agent = await test_sync_search_agent()
        
        # Show simple patterns
        test_simple_patterns()
        
        print("\n💡 Key Success Factors:")
        print("1. Use simple queries with trigger words: 'search', 'latest', 'find'")
        print("2. Keep instructions concise in config.yaml")
        print("3. Let the agent automatically invoke tools")
        print("4. Tavily API key is already working correctly")
        print("5. Focus on query simplicity over complexity")
        
        print("\n🔧 If tests fail:")
        print("1. Make sure your SyncAI server is running")
        print("2. Check that agent_id and session_id are correct")
        print("3. Verify Tavily API key in config.yaml")
        print("4. Try the simple queries first")
        
    except Exception as e:
        print(f" Main test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting SyncSearchAgent Test")
    print(f"📁 Project root: {project_root}")
    print(f"🐍 Python path: {sys.path[0]}")
    asyncio.run(main())