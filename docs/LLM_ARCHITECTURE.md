# LLM Recommendation System Architecture

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                             │
│                     http://localhost:5173                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Smart Recommendations Component                            │ │
│  │  - Displays recommendation cards                            │ │
│  │  - Shows priority badges                                    │ │
│  │  - Lists actions with timeframes                            │ │
│  │  - Shows financial impact                                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              ↑                                      │
│                              │ JSON Response                        │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                      GET /api/recommendations
                      ?use_llm=true
                               │
┌──────────────────────────────┼──────────────────────────────────────┐
│                        BACKEND (FastAPI)                            │
│                     http://localhost:8000                           │
│                              ↓                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  API Endpoint: /api/recommendations                          │ │
│  │  - Loads ML predictions                                      │ │
│  │  - Extracts anomalies                                        │ │
│  │  - Gets price forecast                                       │ │
│  │  - Calculates current demand                                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              ↓                                      │
│                         Decision Point                              │
│                    ┌─────────┴─────────┐                           │
│                    │   use_llm=true?   │                           │
│                    │   API key set?    │                           │
│                    └─────────┬─────────┘                           │
│                              │                                      │
│              ┌───────────────┼───────────────┐                     │
│              │ YES                            │ NO                  │
│              ↓                                ↓                     │
│  ┌─────────────────────────┐    ┌───────────────────────────────┐ │
│  │ LLM Recommendation      │    │ Fallback Recommendations      │ │
│  │ Engine                  │    │ (Rule-Based)                  │ │
│  │                         │    │                               │ │
│  │ - Prepare context       │    │ - Template-based generation   │ │
│  │ - Call OpenAI API       │    │ - Simple priority logic       │ │
│  │ - Parse response        │    │ - Basic financial calc        │ │
│  │ - Structure output      │    │ - Fixed action list           │ │
│  └────────┬────────────────┘    └───────────┬───────────────────┘ │
│           │                                  │                     │
│           │  ┌──────────────────────────────┘                     │
│           │  │                                                     │
│           ↓  ↓                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Response Formatter                                          │ │
│  │  - Count priorities                                          │ │
│  │  - Add metadata                                              │ │
│  │  - Return JSON                                               │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              ↓                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                               ↓ JSON Response
                        {
                          "success": true,
                          "data": {
                            "llm_powered": true/false,
                            "total_anomalies": 1,
                            "high_priority": 1,
                            "recommendations": [...]
                          }
                        }
```

## LLM Engine Internal Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│          LLMRecommendationEngine.generate_recommendations()         │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: Prepare Context (_prepare_context)                        │
│                                                                     │
│  Input Data:                                                        │
│  ├── Predictions: [{demand_mw, predicted_demand, confidence}]      │
│  ├── Price Forecast: [{timestamp, price_per_mwh}]                  │
│  ├── Current Demand: 5,200 MW                                      │
│  ├── Anomalies: [{demand: 8,500, severity: critical}]              │
│  └── Historical Context: {avg_demand, peak_hour}                   │
│                                                                     │
│  Calculate Statistics:                                              │
│  ├── Average Demand: 4,800 MW                                      │
│  ├── Peak Demand: 6,100 MW                                         │
│  ├── Average Price: $85/MWh                                        │
│  ├── Peak Price: $180/MWh at 5pm                                   │
│  └── Min Price: $45/MWh at 2am                                     │
│                                                                     │
│  Build Prompt:                                                      │
│  "You are an expert grid operations analyst for LADWP..."          │
│  + Current situation                                                │
│  + Demand forecast details                                          │
│  + Price forecast details                                           │
│  + Anomaly descriptions                                             │
│  + Task instructions                                                │
│  + JSON output format                                               │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2: Call LLM (_call_llm)                                      │
│                                                                     │
│  POST https://api.openai.com/v1/chat/completions                   │
│  {                                                                  │
│    "model": "gpt-4o-mini",                                          │
│    "messages": [                                                    │
│      {"role": "system", "content": "You are expert analyst..."},   │
│      {"role": "user", "content": "<prepared_context>"}             │
│    ],                                                               │
│    "temperature": 0.3,  // Consistent, factual                     │
│    "max_tokens": 2000,                                              │
│    "response_format": {"type": "json_object"}                      │
│  }                                                                  │
│                                                                     │
│  Error Handling:                                                    │
│  ├── Timeout → Return fallback                                     │
│  ├── Rate limit → Return fallback                                  │
│  ├── Invalid key → Return fallback                                 │
│  └── Network error → Return fallback                               │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3: Parse Response (_parse_llm_response)                      │
│                                                                     │
│  LLM Returns JSON:                                                  │
│  {                                                                  │
│    "recommendations": [                                             │
│      {                                                              │
│        "priority": "HIGH",                                          │
│        "title": "Activate Demand Response...",                     │
│        "why": "Price spike to $180/MWh...",                        │
│        "actions": [                                                 │
│          {"icon": "🔔", "action": "Alert participants", ...}       │
│        ],                                                           │
│        "impact": {                                                  │
│          "financial": "$45,000 savings",                           │
│          "reliability_risk": "LOW"                                 │
│        },                                                           │
│        "confidence": 85                                             │
│      }                                                              │
│    ]                                                                │
│  }                                                                  │
│                                                                     │
│  Enrich with Metadata:                                              │
│  ├── Add timestamps                                                 │
│  ├── Link to anomaly data                                           │
│  ├── Add generation source                                          │
│  └── Format anomaly timestamps                                      │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4: Return Structured Recommendations                         │
│                                                                     │
│  [                                                                  │
│    {                                                                │
│      "timestamp": "2025-10-15T15:30:00",                           │
│      "anomaly": {                                                   │
│        "demand_mw": 8500,                                           │
│        "confidence": 95.5,                                          │
│        "time_str": "03:30 PM"                                       │
│      },                                                             │
│      "analysis": {                                                  │
│        "source": "llm",                                             │
│        "model": "gpt-4o-mini"                                       │
│      },                                                             │
│      "recommendation": {                                            │
│        "priority": "HIGH",                                          │
│        "title": "...",                                              │
│        "actions": [...],                                            │
│        "impact": {...}                                              │
│      }                                                              │
│    }                                                                │
│  ]                                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Comparison: Fallback vs LLM

```
┌──────────────────────────┬──────────────────────────────────────────┐
│   FALLBACK (Rule-Based)  │         LLM (AI-Powered)                 │
├──────────────────────────┼──────────────────────────────────────────┤
│ Input:                   │ Input:                                   │
│  - Anomaly data only     │  - Anomaly data                          │
│                          │  - Price forecasts                       │
│                          │  - Demand patterns                       │
│                          │  - Historical context                    │
│                          │  - Grid constraints                      │
├──────────────────────────┼──────────────────────────────────────────┤
│ Processing:              │ Processing:                              │
│  - Template matching     │  - Multi-factor analysis                 │
│  - Simple if/else        │  - Pattern recognition                   │
│  - Fixed thresholds      │  - Context understanding                 │
│                          │  - Temporal reasoning                    │
├──────────────────────────┼──────────────────────────────────────────┤
│ Output:                  │ Output:                                  │
│  - Generic actions       │  - Specific recommendations              │
│  - Fixed 2-3 steps       │  - Variable actions (2-6)                │
│  - Basic calculations    │  - Detailed calculations                 │
│  - One scenario          │  - Multiple strategies                   │
├──────────────────────────┼──────────────────────────────────────────┤
│ Example:                 │ Example:                                 │
│  "Verify Data Accuracy"  │  "Discharge 40 MWh battery at 5pm peak,  │
│  "Assess Grid Stability" │   recharge overnight at $35/MWh,         │
│  "Emergency Coord"       │   net savings $45K, maintain 20% reserve"│
├──────────────────────────┼──────────────────────────────────────────┤
│ Cost: FREE               │ Cost: ~$0.001 per call                   │
│ Speed: <1ms              │ Speed: 1-2 seconds                       │
│ Reliability: 100%        │ Reliability: 99.9% (with fallback)       │
└──────────────────────────┴──────────────────────────────────────────┘
```

## File Structure

```
LADWP/
├── api_server.py                      # Main API server
│   ├── /api/recommendations           # Main endpoint
│   │   ├── Load predictions           # From ML models
│   │   ├── Get price data             # From CAISO
│   │   ├── Extract anomalies          # Filter predictions
│   │   ├── Call LLM engine            # If API key set
│   │   └── Call fallback              # If no API key
│   └── _generate_fallback_recommendations()
│
├── llm_recommendation_engine.py       # LLM Engine (NEW)
│   ├── LLMRecommendationEngine
│   │   ├── __init__()                 # Initialize with API key
│   │   ├── generate_recommendations() # Main entry point
│   │   ├── _prepare_context()         # Build LLM prompt
│   │   ├── _call_llm()                # OpenAI API call
│   │   ├── _parse_llm_response()      # Parse JSON
│   │   ├── _format_anomaly()          # Format timestamps
│   │   └── _get_fallback_*()          # Emergency fallback
│   └── generate_llm_recommendations() # Convenience function
│
├── LLM_SETUP_GUIDE.md                 # Setup instructions (NEW)
├── LLM_IMPLEMENTATION_COMPLETE.md     # Summary (NEW)
├── setup_api_key.example.ps1          # Quick setup script (NEW)
│
└── frontend/src/components/
    └── RecommendationCards.tsx        # Displays recommendations
        ├── Priority badge
        ├── Title with emoji
        ├── Why explanation
        ├── Action list with icons
        ├── Financial impact
        └── Reliability risk
```

## Environment Variables

```
┌────────────────────────────────────────────────────────────┐
│  OPENAI_API_KEY                                            │
│  ├── Required for LLM mode                                 │
│  ├── Optional (fallback works without it)                  │
│  ├── Format: sk-proj-...                                   │
│  ├── Get from: https://platform.openai.com/api-keys       │
│  └── Set in PowerShell: $env:OPENAI_API_KEY="sk-..."      │
└────────────────────────────────────────────────────────────┘
```

## Decision Tree

```
User opens dashboard
        ↓
Frontend fetches /api/recommendations
        ↓
Backend checks: OPENAI_API_KEY set?
        ↓
    ┌───┴───┐
   YES      NO
    ↓        ↓
 Try LLM   Fallback
    ↓        ↓
Success?    ┌──┘
    ↓ NO
Fallback
    ↓
Return JSON with llm_powered flag
    ↓
Frontend renders recommendations
```

## API Response Format

```json
{
  "success": true,
  "data": {
    "generated_at": "2025-10-15T15:30:00",
    "month": "october",
    "total_anomalies": 1,
    "high_priority": 1,
    "medium_priority": 0,
    "low_priority": 0,
    "llm_powered": true,  // ← Indicates if LLM was used
    "recommendations": [
      {
        "timestamp": "2025-10-15T13:30:00",
        "anomaly": {
          "demand_mw": 8500,
          "confidence": 95.5,
          "severity": "critical",
          "time_str": "01:30 PM",
          "date_str": "Oct 15, 2025"
        },
        "analysis": {
          "source": "llm",  // or "rule-based"
          "model": "gpt-4o-mini",
          "generated_at": "2025-10-15T15:30:00"
        },
        "recommendation": {
          "priority": "HIGH",
          "title": "🚨 CRITICAL: Extreme Demand Anomaly",
          "why": "Demand of 8,500 MW far exceeds...",
          "actions": [
            {
              "icon": "🔍",
              "action": "Verify Data Accuracy",
              "details": "Confirm with SCADA systems...",
              "timeframe": "Immediately"
            }
          ],
          "impact": {
            "financial": "$115,000/hour excess costs",
            "financial_type": "high_cost",
            "reliability_risk": "CRITICAL",
            "magnitude_mw": 2300,
            "duration_estimate": "Unknown"
          },
          "confidence": 95,
          "time_sensitive": true
        }
      }
    ]
  }
}
```

---

**Architecture designed for:**
- ✅ Reliability (automatic fallback)
- ✅ Cost-effectiveness (~$1.50/month)
- ✅ Flexibility (toggle on/off)
- ✅ Scalability (easy to add new features)
- ✅ Maintainability (clean separation of concerns)
