#!/bin/bash
# Enhanced Newsletter Format Curl Tests
# Ultra-concise, actionable newsletters with new features

BASE_URL="http://localhost:8000/api/sync-search"

echo "🚀 Enhanced SyncAI Newsletter Tests - Version 1.1.0"
echo "=================================================="

# =============================================================================
# 1. SERVICE STATUS AND CAPABILITIES
# =============================================================================

echo "📊 1. Checking Enhanced Service Status..."
curl -s -X GET "$BASE_URL/status" | jq '{
  service: .service,
  version: .version,
  capabilities: .capabilities,
  agent_connectivity: .agent_connectivity
}'

echo
echo "📋 2. Available Newsletter Formats..."
curl -s -X GET "$BASE_URL/newsletter/formats" | jq .

echo
echo "👥 3. Available Personas..."
curl -s -X GET "$BASE_URL/personas" | jq '{
  success: .success,
  total_count: .total_count,
  persona_names: (.personas | keys)
}'

# =============================================================================
# 2. ENHANCED NEWSLETTER FORMAT TESTS
# =============================================================================

echo
echo "📰 4. Enhanced Newsletter Format Tests"
echo "======================================"

# DevOps Engineer Newsletter (Enhanced)
echo "🔧 DevOps Engineer Newsletter..."
curl -s -X POST "$BASE_URL/search/devops_engineer/newsletter" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["MLOps platforms", "AI infrastructure", "GPU management"],
    "time_range": "7d"
  }' | jq '{
    success: .success,
    format: .format,
    word_count: .word_count,
    char_count: .char_count,
    elapsed_time: .elapsed_time,
    newsletter: .newsletter
  }'

echo
echo "💻 Software Engineer Newsletter..."
curl -s -X POST "$BASE_URL/search/software_engineer/newsletter" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["AI frameworks", "LLM APIs", "vector databases"],
    "time_range": "7d"
  }' | jq '{
    success: .success,
    format: .format,
    word_count: .word_count,
    newsletter: .newsletter
  }'

echo
echo "🤖 AI Engineer Newsletter..."
curl -s -X POST "$BASE_URL/search/ai_engineer/newsletter" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["LLM research", "model training", "transformer architectures"],
    "time_range": "7d"
  }' | jq '{
    success: .success,
    format: .format,
    word_count: .word_count,
    newsletter: .newsletter
  }'

# =============================================================================
# 3. DAILY BRIEF FORMAT TESTS (NEW FEATURE)
# =============================================================================

echo
echo "📅 5. Daily Brief Format Tests (Ultra-Short)"
echo "============================================"

# DevOps Daily Brief
echo "🔧 DevOps Engineer Daily Brief..."
curl -s -X POST "$BASE_URL/search/devops_engineer/newsletter?format_type=daily" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["MLOps platforms", "AI infrastructure"],
    "time_range": "1d"
  }' | jq '{
    success: .success,
    format: .format,
    word_count: .word_count,
    newsletter: .newsletter
  }'

echo
echo "💻 Software Engineer Daily Brief..."
curl -s -X POST "$BASE_URL/search/software_engineer/newsletter?format_type=daily" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["AI frameworks", "LLM APIs"],
    "time_range": "1d"
  }' | jq '{
    success: .success,
    format: .format,
    word_count: .word_count,
    newsletter: .newsletter
  }'

echo
echo "🤖 AI Engineer Daily Brief..."
curl -s -X POST "$BASE_URL/search/ai_engineer/newsletter?format_type=daily" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["LLM research", "model training"],
    "time_range": "1d"
  }' | jq '{
    success: .success,
    format: .format,
    word_count: .word_count,
    newsletter: .newsletter
  }'

# =============================================================================
# 4. NEWSLETTER PREVIEWS AND EXAMPLES
# =============================================================================

echo
echo "👀 6. Newsletter Previews and Examples"
echo "======================================"

# Preview newsletter format
echo "📰 Newsletter Preview for DevOps Engineer..."
curl -s -X GET "$BASE_URL/newsletter/preview/devops_engineer?format_type=newsletter" | jq '{
  persona: .persona,
  format: .format,
  word_count: .word_count,
  preview: .preview
}'

echo
echo "📅 Daily Preview for AI Engineer..."
curl -s -X GET "$BASE_URL/newsletter/preview/ai_engineer?format_type=daily" | jq '{
  persona: .persona,
  format: .format,
  word_count: .word_count,
  preview: .preview
}'

# Example newsletter (backward compatibility)
echo
echo "📋 Example Newsletter for Software Engineer..."
curl -s -X GET "$BASE_URL/newsletter/example/software_engineer" | jq '{
  persona: .persona,
  format: .format,
  note: .note
}'

# =============================================================================
# 5. ENHANCED COMPARISON TESTS
# =============================================================================

echo
echo "⚖️ 7. Format Comparison Tests"
echo "============================"

# Compare newsletter vs daily format
echo "📊 Comparing Newsletter vs Daily Brief for DevOps Engineer..."
echo "Newsletter Format:"
curl -s -X POST "$BASE_URL/search/devops_engineer/newsletter?format_type=newsletter" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["MLOps platforms"],
    "time_range": "7d"
  }' | jq -r '.newsletter' | wc -w | awk '{print "Words: " $1}'

echo "Daily Format:"
curl -s -X POST "$BASE_URL/search/devops_engineer/newsletter?format_type=daily" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["MLOps platforms"],
    "time_range": "1d"
  }' | jq -r '.newsletter' | wc -w | awk '{print "Words: " $1}'

# Compare regular search vs newsletter
echo
echo "📈 Regular Search vs Newsletter Format..."
echo "Regular Search Response Length:"
curl -s -X POST "$BASE_URL/search/devops_engineer" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["MLOps platforms"],
    "time_range": "7d"
  }' | jq -r '.formatted_response' | wc -w | awk '{print "Words: " $1}'

echo "Newsletter Format Length:"
curl -s -X POST "$BASE_URL/search/devops_engineer/newsletter" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["MLOps platforms"],
    "time_range": "7d"
  }' | jq -r '.newsletter' | wc -w | awk '{print "Words: " $1}'

# =============================================================================
# 6. SAVE NEWSLETTERS TO FILES (ENHANCED)
# =============================================================================

echo
echo "💾 8. Saving Newsletters to Files"
echo "================================="

DATE=$(date +%Y%m%d)
TIMESTAMP=$(date +%H%M%S)

# Save weekly newsletters
echo "📰 Saving weekly newsletters..."
curl -s -X POST "$BASE_URL/search/devops_engineer/newsletter" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["MLOps platforms", "AI infrastructure", "GPU management"],
    "time_range": "7d"
  }' | jq -r '.newsletter' > "devops_newsletter_${DATE}_${TIMESTAMP}.md"

curl -s -X POST "$BASE_URL/search/software_engineer/newsletter" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["AI frameworks", "LLM APIs", "vector databases"],
    "time_range": "7d"
  }' | jq -r '.newsletter' > "software_newsletter_${DATE}_${TIMESTAMP}.md"

curl -s -X POST "$BASE_URL/search/ai_engineer/newsletter" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["LLM research", "model training", "transformer architectures"],
    "time_range": "7d"
  }' | jq -r '.newsletter' > "ai_newsletter_${DATE}_${TIMESTAMP}.md"

# Save daily briefs
echo "📅 Saving daily briefs..."
curl -s -X POST "$BASE_URL/search/devops_engineer/newsletter?format_type=daily" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["MLOps platforms", "AI infrastructure"],
    "time_range": "1d"
  }' | jq -r '.newsletter' > "devops_daily_${DATE}_${TIMESTAMP}.md"

curl -s -X POST "$BASE_URL/search/ai_engineer/newsletter?format_type=daily" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["LLM research", "model training"],
    "time_range": "1d"
  }' | jq -r '.newsletter' > "ai_daily_${DATE}_${TIMESTAMP}.md"

echo "📁 Files saved with timestamp: ${DATE}_${TIMESTAMP}"

# =============================================================================
# 7. PERFORMANCE AND METRICS TESTS
# =============================================================================

echo
echo "📊 9. Performance and Metrics"
echo "============================="

# Get detailed metrics
echo "📈 Enhanced Service Metrics..."
curl -s -X GET "$BASE_URL/metrics" | jq '{
  search_statistics: .metrics.search_statistics,
  features_available: .metrics.agent_performance.features_available,
  agent_mode: .metrics.agent_performance.agent_mode
}'

# Health check with newsletter features
echo
echo "🏥 Enhanced Health Check..."
curl -s -X GET "$BASE_URL/health" | jq '{
  healthy: .healthy,
  sync_agent_healthy: .checks.sync_agent.healthy,
  features: .checks.sync_agent.features,
  persona_config_healthy: .checks.persona_config.healthy
}'

# =============================================================================
# 8. ERROR HANDLING AND VALIDATION TESTS
# =============================================================================

echo
echo "🔍 10. Error Handling and Validation"
echo "==================================="

# Test invalid persona
echo " Testing invalid persona..."
curl -s -X POST "$BASE_URL/search/invalid_persona/newsletter" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["test"],
    "time_range": "7d"
  }' | jq '{
    success: .success,
    error: .detail
}'

# Test invalid format
echo
echo " Testing invalid format..."
curl -s -X POST "$BASE_URL/search/devops_engineer/newsletter?format_type=invalid" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["MLOps"],
    "time_range": "7d"
  }' | jq '{
    success: .success,
    format: .format,
    newsletter_preview: (.newsletter[:100])
}'

# Test persona validation
echo
echo " Testing persona validation..."
curl -s -X POST "$BASE_URL/personas/devops_engineer/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["MLOps platforms", "AI infrastructure"],
    "time_range": "7d"
  }' | jq '{
    valid: .valid,
    persona: .persona,
    warnings: .warnings,
    suggestions: .suggestions
}'

# =============================================================================
# 9. DEBUG AND TESTING ENDPOINTS
# =============================================================================

echo
echo "🧪 11. Debug and Testing"
echo "======================="

# Test agent connectivity
echo "🔌 Testing agent connectivity..."
curl -s -X POST "$BASE_URL/debug/test-agent" | jq '{
  success: .success,
  response_length: .response_length,
  agent_status: .agent_status.status
}'

# Test newsletter functionality
echo
echo "📰 Testing newsletter functionality..."
curl -s -X POST "$BASE_URL/debug/test-newsletter?persona=devops_engineer&format_type=newsletter" | jq '{
  success: .success,
  persona: .persona,
  format_type: .format_type,
  output_word_count: .output_word_count,
  sample_output: (.formatted_output[:200])
}'

# Test daily brief functionality
echo
echo "📅 Testing daily brief functionality..."
curl -s -X POST "$BASE_URL/debug/test-newsletter?persona=ai_engineer&format_type=daily" | jq '{
  success: .success,
  persona: .persona,
  format_type: .format_type,
  output_word_count: .output_word_count,
  sample_output: (.formatted_output[:150])
}'

# =============================================================================
# 10. AUTOMATION SCRIPTS FOR DAILY/WEEKLY USE
# =============================================================================

echo
echo "🤖 12. Automation Examples"
echo "========================="

# Function to generate daily digest for all personas
generate_daily_digest() {
    local date_suffix=$(date +%Y%m%d)
    
    echo "📅 Generating daily digest for all personas..."
    
    for persona in "devops_engineer" "software_engineer" "ai_engineer"; do
        echo "Processing ${persona}..."
        curl -s -X POST "$BASE_URL/search/${persona}/newsletter?format_type=daily" \
          -H "Content-Type: application/json" \
          -d '{
            "focus_areas": ["latest developments", "new tools"],
            "time_range": "1d"
          }' | jq -r '.newsletter' > "${persona}_daily_${date_suffix}.md"
    done
    
    echo "📁 Daily digest files created with suffix: ${date_suffix}"
}

# Function to generate weekly newsletter compilation
generate_weekly_compilation() {
    local date_suffix=$(date +%Y%m%d)
    
    echo "📰 Generating weekly newsletter compilation..."
    
    # Create a combined newsletter file
    {
        echo "# SyncAI Weekly Technology Brief"
        echo "*Generated: $(date)*"
        echo ""
        echo "---"
        echo ""
        
        for persona in "devops_engineer" "software_engineer" "ai_engineer"; do
            echo "Processing ${persona} newsletter..."
            curl -s -X POST "$BASE_URL/search/${persona}/newsletter" \
              -H "Content-Type: application/json" \
              -d '{
                "focus_areas": ["latest developments", "new frameworks", "infrastructure updates"],
                "time_range": "7d"
              }' | jq -r '.newsletter'
            echo ""
            echo "---"
            echo ""
        done
    } > "syncai_weekly_compilation_${date_suffix}.md"
    
    echo "📁 Weekly compilation created: syncai_weekly_compilation_${date_suffix}.md"
}

# Example usage (commented out to avoid execution during test)
# generate_daily_digest
# generate_weekly_compilation

# =============================================================================
# 13. QUICK DAILY/WEEKLY GENERATION COMMANDS
# =============================================================================

echo
echo "⚡ 13. Quick Generation Commands"
echo "==============================="

# Quick daily AI digest
echo "🤖 Quick AI Daily Digest..."
curl -s -X POST "$BASE_URL/search/ai_engineer/newsletter?format_type=daily" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["AI developments", "new models", "research papers"],
    "time_range": "1d"
  }' | jq -r '.newsletter'

echo
echo "🔧 Quick DevOps Weekly Roundup..."
curl -s -X POST "$BASE_URL/search/devops_engineer/newsletter" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_areas": ["container orchestration", "AI infrastructure", "monitoring tools"],
    "time_range": "7d"
  }' | jq -r '.newsletter'

# =============================================================================
# 14. CONFIGURATION AND STATUS SUMMARY
# =============================================================================

echo
echo "⚙️ 14. Configuration Summary"
echo "==========================="

# Get enhanced configuration
curl -s -X GET "$BASE_URL/config" | jq '{
  version: .version,
  features: .features,
  persona_config_valid: .persona_configuration.configuration_valid,
  personas_available: .persona_configuration.personas_loaded
}'

echo
echo "🎯 Newsletter Format Characteristics..."
curl -s -X GET "$BASE_URL/newsletter/formats" | jq '{
  newsletter: .formats.newsletter,
  daily: .formats.daily
}'

echo
echo " Enhanced SyncAI Newsletter Tests Complete!"
echo "============================================="
echo "📊 Summary:"
echo "- Enhanced newsletter format with ultra-concise sections"
echo "- Daily brief format for quick daily updates" 
echo "- Improved error handling and validation"
echo "- Performance metrics and debugging endpoints"
echo "- Automation-ready API endpoints"
echo ""
echo "📁 Generated files:"
echo "- Newsletter files: *_newsletter_${DATE}_${TIMESTAMP}.md"
echo "- Daily brief files: *_daily_${DATE}_${TIMESTAMP}.md"
echo ""
echo "🚀 Ready for production use with enhanced features!"