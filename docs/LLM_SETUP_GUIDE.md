# LLM-Powered Recommendations Setup Guide

Your dashboard now uses **OpenAI's GPT models** to generate intelligent, context-aware recommendations based on real-time grid data!

## 🚀 Quick Start

### 1. Get an OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### 2. Set the Environment Variable

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY="sk-your-key-here"
```

**Windows Command Prompt:**
```cmd
set OPENAI_API_KEY=sk-your-key-here
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY=sk-your-key-here
```

### 3. Restart the Backend Server

```powershell
cd C:\Users\leric\Downloads\LADWP
python api_server.py
```

## 🎯 How It Works

### LLM Analysis Pipeline

1. **Data Collection** - The system gathers:
   - ML predictions with anomaly detection
   - Real-time and forecast price data
   - Current demand levels
   - Historical context
   - Grid operating parameters (2,000-6,200 MW range)

2. **Context Preparation** - Creates a comprehensive prompt with:
   - Current grid situation
   - Statistical summaries (avg, min, max)
   - Detailed anomaly information
   - LADWP-specific constraints
   - Historical patterns

3. **LLM Analysis** - GPT analyzes the data considering:
   - Price arbitrage opportunities
   - Demand response triggers
   - Grid stability concerns
   - Energy storage optimization
   - Load shifting strategies
   - Equipment maintenance needs

4. **Structured Output** - Returns recommendations with:
   - Priority levels (HIGH/MEDIUM/LOW)
   - Specific actions with timeframes
   - Financial impact calculations
   - Reliability risk assessments
   - Confidence scores

### Example LLM Prompt Context

```
You are an expert grid operations analyst for LADWP.
Analyze the following grid data and provide actionable recommendations.

## CURRENT SITUATION
- Current Time: 2025-10-15 03:00 PM
- Current Demand: 5,200 MW
- LADWP Typical Range: 2,000 - 6,200 MW (peak)

## DEMAND FORECAST (Next 24 Hours)
- Average Predicted Demand: 4,800 MW
- Peak Predicted Demand: 6,100 MW
- Minimum Predicted Demand: 2,300 MW

## PRICE FORECAST
- Average Price: $85/MWh
- Peak Price: $180/MWh (at 5:00 PM)
- Minimum Price: $45/MWh (at 2:00 AM)

## ANOMALIES DETECTED
- Total Anomalies: 2
- Anomaly 1: 8,500 MW at 7:00 PM (95% confidence)
...
```

## 💰 Cost Optimization

### Model Options

**Recommended: gpt-4o-mini** (Current Default)
- **Cost**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **Speed**: Fast (~1-2 seconds)
- **Quality**: Excellent for grid operations
- **Estimated Cost**: ~$0.001-0.002 per recommendation generation

**Advanced: gpt-4o**
- **Cost**: ~$2.50 per 1M input tokens, ~$10 per 1M output tokens  
- **Speed**: Moderate (~2-4 seconds)
- **Quality**: Maximum reasoning capability
- **Use case**: Complex scenarios, critical decisions

### Typical Usage Costs

- **Per API call**: $0.001-0.002 (gpt-4o-mini)
- **Per day** (hourly refresh): ~$0.05
- **Per month**: ~$1.50
- **With 5-minute refresh**: ~$0.30/day, ~$9/month

### To Change Models

Edit `api_server.py` line ~337:
```python
llm_engine = LLMRecommendationEngine(model="gpt-4o")  # Change to gpt-4o
```

Or in `llm_recommendation_engine.py` line 22:
```python
def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
```

## 🔧 Configuration Options

### Enable/Disable LLM Per Request

The API endpoint supports a `use_llm` parameter:

```
GET /api/recommendations?use_llm=true   # Use LLM (default)
GET /api/recommendations?use_llm=false  # Use rule-based fallback
```

### Fallback Behavior

If LLM is unavailable (no API key, API error, timeout), the system automatically falls back to rule-based recommendations. You'll see:
```json
{
  "llm_powered": false,
  "recommendations": [...]
}
```

## 🎛️ Advanced Configuration

### Adjust LLM Temperature

In `llm_recommendation_engine.py` line ~217:
```python
"temperature": 0.3,  # Lower = more consistent, Higher = more creative
```

- **0.0-0.3**: Consistent, factual (recommended for operations)
- **0.4-0.7**: Balanced creativity and consistency
- **0.8-1.0**: More creative, varied responses

### Adjust Token Limits

In `llm_recommendation_engine.py` line ~218:
```python
"max_tokens": 2000,  # Maximum response length
```

- **1000**: Short, concise recommendations
- **2000**: Standard (current default)
- **4000**: Detailed analysis with more context

### Add Historical Context

In `api_server.py`, pass additional context:
```python
llm_engine.generate_recommendations(
    predictions=predictions_list,
    price_forecast=price_forecast,
    current_demand=current_demand,
    anomalies=anomalies,
    historical_context={
        "avg_monthly_demand": 4500,
        "typical_peak_hour": "5:00 PM",
        "recent_outages": []
    }
)
```

## 📊 Monitoring LLM Performance

### Check if LLM is Active

Look at the API response:
```json
{
  "success": true,
  "data": {
    "llm_powered": true,  // ✅ LLM is working
    "recommendations": [...]
  }
}
```

### View LLM Errors

Backend logs will show:
```
LLM generation failed: [error details]
```

Common issues:
- ❌ No API key set
- ❌ Invalid API key
- ❌ Rate limit exceeded
- ❌ Network timeout

## 🔐 Security Best Practices

1. **Never commit API keys** to git
2. **Use environment variables** only
3. **Rotate keys regularly** (every 90 days)
4. **Set usage limits** in OpenAI dashboard
5. **Monitor costs** via OpenAI usage dashboard

### Add to .gitignore
```
.env
*.key
.env.local
```

### Create .env file (optional)
```bash
# .env
OPENAI_API_KEY=sk-your-key-here
```

Then load it in your shell:
```powershell
# PowerShell
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
```

## 🧪 Testing LLM Recommendations

### Test with Extreme Anomaly

The current code includes a test anomaly (8,500 MW). The LLM will analyze it and provide:
- Verification steps
- Grid stability assessment  
- Emergency coordination
- Financial impact ($115,000/hour)

### Sample LLM Response

```json
{
  "priority": "HIGH",
  "title": "🚨 CRITICAL: Extreme Demand Spike - Emergency Response Required",
  "why": "Demand of 8,500 MW represents a 37% increase above LADWP's normal peak capacity...",
  "actions": [
    {
      "icon": "🔔",
      "action": "Activate Demand Response",
      "details": "Deploy all available DR programs, target 500 MW reduction",
      "timeframe": "Immediately"
    },
    {
      "icon": "⚡",
      "action": "Emergency Generation",
      "details": "Bring online backup peaker plants, coordinate with CAISO",
      "timeframe": "Within 10 minutes"
    }
  ],
  "impact": {
    "financial": "Potential $115,000/hour in excess costs, plus ~$50,000 emergency DR activation",
    "reliability_risk": "CRITICAL - Risk of rolling blackouts if sustained"
  }
}
```

## 🎓 Next Steps

1. ✅ Set OPENAI_API_KEY environment variable
2. ✅ Restart backend server
3. ✅ Refresh dashboard in browser
4. ✅ Review LLM-generated recommendations
5. ✅ Monitor OpenAI usage dashboard
6. ✅ Adjust model/temperature as needed
7. ✅ Remove test anomaly injection (api_server.py lines 285-293)

## 📚 Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI Pricing](https://openai.com/pricing)
- [Usage Dashboard](https://platform.openai.com/usage)
- [API Keys Management](https://platform.openai.com/api-keys)

## 🆘 Troubleshooting

### "No API key" error
```bash
# Verify key is set
echo $env:OPENAI_API_KEY  # PowerShell
```

### "Rate limit exceeded"
- Wait a few minutes
- Reduce refresh frequency
- Upgrade OpenAI plan

### "Invalid API key"
- Regenerate key in OpenAI dashboard
- Check for extra spaces/quotes
- Ensure key starts with `sk-`

### LLM not generating recommendations
- Check backend logs for errors
- Verify internet connection
- Try fallback mode: `?use_llm=false`

---

**Happy optimizing! 🎉**
