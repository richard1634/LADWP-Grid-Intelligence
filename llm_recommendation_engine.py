"""
LLM-Based Recommendation Engine for LADWP Grid Intelligence
Uses OpenAI GPT to generate intelligent, context-aware recommendations
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests


class LLMRecommendationEngine:
    """
    LLM-powered recommendation engine that analyzes grid data
    and generates intelligent operational recommendations.
    """
    
    # Cache for LLM responses to avoid redundant API calls
    _response_cache = {}
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the LLM recommendation engine.
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env variable)
            model: Model to use (gpt-3.5-turbo is fastest/cheapest, gpt-4o-mini for better quality)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
    
    def generate_recommendations(
        self,
        predictions: List[Dict],
        price_forecast: List[Dict],
        current_demand: float,
        anomalies: List[Dict],
        historical_context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations using LLM analysis.
        
        Args:
            predictions: ML predictions with demand forecasts
            price_forecast: Price predictions for upcoming periods
            current_demand: Current demand in MW
            anomalies: Detected anomalies from ML model
            historical_context: Optional historical data for context
            
        Returns:
            List of recommendation dictionaries
        """
        # Create cache key based on anomalies
        cache_key = self._create_cache_key(anomalies, current_demand)
        
        # Check cache first
        if cache_key in self._response_cache:
            print(f"[LLM] Using cached response for {len(anomalies)} anomalies")
            return self._response_cache[cache_key]
        
        # Prepare context for LLM
        context = self._prepare_context(
            predictions, price_forecast, current_demand, anomalies, historical_context
        )
        
        # Generate recommendations via LLM
        llm_response = self._call_llm(context)
        
        # Parse and structure the response
        recommendations = self._parse_llm_response(llm_response, anomalies)
        
        # Cache the response
        self._response_cache[cache_key] = recommendations
        print(f"[LLM] Cached response for future requests")
        
        return recommendations
    
    def _create_cache_key(self, anomalies: List[Dict], current_demand: float) -> str:
        """Create a cache key from anomaly data."""
        import hashlib
        
        # Create key from anomaly timestamps and demand values
        key_data = []
        for anomaly in anomalies:
            key_data.append(f"{anomaly.get('timestamp')}_{anomaly.get('demand_mw')}_{anomaly.get('confidence')}")
        key_data.append(f"demand_{current_demand}")
        
        key_string = "|".join(key_data)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _prepare_context(
        self,
        predictions: List[Dict],
        price_forecast: List[Dict],
        current_demand: float,
        anomalies: List[Dict],
        historical_context: Optional[Dict]
    ) -> str:
        """Prepare comprehensive context for LLM analysis."""
        
        # Calculate statistics
        if predictions:
            avg_demand = sum(p.get('demand_mw', 0) for p in predictions) / len(predictions)
            max_demand = max(p.get('demand_mw', 0) for p in predictions)
            min_demand = min(p.get('demand_mw', 0) for p in predictions)
        else:
            avg_demand = max_demand = min_demand = current_demand
        
        if price_forecast:
            avg_price = sum(p.get('price_per_mwh', 0) for p in price_forecast) / len(price_forecast)
            max_price = max(p.get('price_per_mwh', 0) for p in price_forecast)
            min_price = min(p.get('price_per_mwh', 0) for p in price_forecast)
        else:
            avg_price = max_price = min_price = 50.0
        
        # Build context string
        context = f"""You are an expert grid operations analyst for LADWP (Los Angeles Department of Water and Power).
Analyze the following grid data and provide actionable recommendations for grid operators.

## CURRENT SITUATION
- **Current Time**: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
- **Current Demand**: {current_demand:,.0f} MW
- **LADWP Typical Range**: 2,000 - 6,200 MW (peak)
- **Service Area**: 465 sq mi, 1.5M+ customers, Los Angeles

## DEMAND FORECAST (Next 24 Hours)
- **Average Predicted Demand**: {avg_demand:,.0f} MW
- **Peak Predicted Demand**: {max_demand:,.0f} MW
- **Minimum Predicted Demand**: {min_demand:,.0f} MW
- **Total Predictions**: {len(predictions)} data points

## PRICE FORECAST (Next 24 Hours)
- **Average Price**: ${avg_price:.2f}/MWh
- **Peak Price**: ${max_price:.2f}/MWh
- **Minimum Price**: ${min_price:.2f}/MWh
- **Total Price Points**: {len(price_forecast)} data points
- **Historical Average**: ~$50/MWh

## ANOMALIES DETECTED
- **Total Anomalies**: {len(anomalies)}
"""
        
        # Add detailed anomaly information
        if anomalies:
            context += "\n### Anomaly Details:\n"
            for i, anomaly in enumerate(anomalies[:5], 1):  # Limit to top 5
                demand = anomaly.get('demand_mw', 0)
                predicted = anomaly.get('predicted_demand', demand)
                confidence = anomaly.get('confidence', 0)
                severity = anomaly.get('severity', 'unknown')
                deviation = ((demand - predicted) / predicted * 100) if predicted else 0
                
                context += f"""
**Anomaly {i}:**
- Time: {anomaly.get('timestamp', 'Unknown')}
- Actual Demand: {demand:,.0f} MW
- Predicted Demand: {predicted:,.0f} MW
- Deviation: {deviation:+.1f}%
- Confidence: {confidence:.1f}%
- Severity: {severity.upper()}
"""
        else:
            context += "\n**No significant anomalies detected** - Grid operating within normal parameters.\n"
        
        # Add historical context if available
        if historical_context:
            context += f"\n## HISTORICAL CONTEXT\n{json.dumps(historical_context, indent=2)}\n"
        
        # Add specific analysis requests
        context += """

## YOUR TASK
Analyze this data and provide 1-5 specific, actionable recommendations for LADWP grid operators.

For each recommendation, provide:
1. **Priority** (HIGH, MEDIUM, LOW)
2. **Title** (short, descriptive, with relevant emoji)
3. **Why** (clear explanation of the issue/opportunity)
4. **Actions** (3-5 specific steps with timeframes)
5. **Financial Impact** (estimated cost savings or costs)
6. **Reliability Impact** (how this affects grid stability)
7. **Confidence** (your confidence in this recommendation, 0-100%)

Focus on:
- Price arbitrage opportunities (buy low, sell high)
- Demand response activation during peak prices
- Grid stability concerns during anomalies
- Energy storage optimization (charge during low prices, discharge during high)
- Load shifting opportunities
- Preventive maintenance if patterns suggest equipment issues
- Emergency response for critical anomalies

**IMPORTANT**: 
- Be specific with MW amounts, timeframes, and dollar figures
- Consider LADWP's actual operating constraints (2,000-6,200 MW range)
- Prioritize recommendations by potential impact
- If no anomalies exist, focus on optimization opportunities

Return your response as a JSON array of recommendation objects with this EXACT structure:
```json
[
  {
    "priority": "HIGH",
    "title": "Activate Demand Response - Price Spike Incoming",
    "why": "Price forecast shows spike to $180/MWh at 3:00 PM, 60% above baseline",
    "actions": [
      {
        "icon": "🔔",
        "action": "Alert demand response participants",
        "details": "Send automated alerts to 500+ enrolled customers",
        "timeframe": "Within 15 minutes"
      }
    ],
    "impact": {
      "financial": "Estimated savings of $45,000 by reducing 250 MW during peak",
      "financial_type": "savings",
      "reliability_risk": "LOW - Voluntary reduction maintains stability",
      "magnitude_mw": 250,
      "duration_estimate": "2-4 hours during peak pricing"
    },
    "confidence": 85,
    "time_sensitive": true
  }
]
```

Return ONLY valid JSON, no markdown formatting, no explanation text outside the JSON.
"""
        
        return context
    
    def _call_llm(self, context: str) -> str:
        """Call OpenAI API to get recommendations."""
        import time
        start_time = time.time()
        
        try:
            print(f"[LLM] Calling OpenAI API with model {self.model}...")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert grid operations analyst specializing in real-time power system optimization, energy economics, and grid reliability. You provide actionable, data-driven recommendations."
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                "temperature": 0.3,  # Lower temperature for more consistent, factual responses
                "max_tokens": 1500,  # Reduced for faster response
                "response_format": {"type": "json_object"}  # Force JSON response
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=15  # Reduced to 15s - gpt-3.5-turbo is much faster
            )
            
            elapsed = time.time() - start_time
            print(f"[LLM] API call completed in {elapsed:.2f}s")
            
            response.raise_for_status()
            result = response.json()
            
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.Timeout as e:
            elapsed = time.time() - start_time
            print(f"[LLM] TIMEOUT after {elapsed:.2f}s: {e}")
            return self._get_fallback_recommendations()
        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            print(f"[LLM] API Error after {elapsed:.2f}s: {e}")
            return self._get_fallback_recommendations()
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"[LLM] Unexpected error after {elapsed:.2f}s: {e}")
            return self._get_fallback_recommendations()
    
    def _parse_llm_response(self, llm_response: str, anomalies: List[Dict]) -> List[Dict]:
        """Parse LLM response and structure recommendations."""
        try:
            # Parse JSON response
            data = json.loads(llm_response)
            
            # Handle different response structures
            if isinstance(data, dict):
                recommendations = data.get('recommendations', [data])
            else:
                recommendations = data
            
            # Enrich recommendations with anomaly data
            enriched_recommendations = []
            for i, rec in enumerate(recommendations):
                # Link to corresponding anomaly if available
                anomaly = anomalies[i] if i < len(anomalies) else None
                
                enriched_rec = {
                    "timestamp": datetime.now().isoformat(),
                    "anomaly": self._format_anomaly(anomaly) if anomaly else None,
                    "analysis": {
                        "source": "llm",
                        "model": self.model,
                        "generated_at": datetime.now().isoformat()
                    },
                    "recommendation": rec
                }
                
                enriched_recommendations.append(enriched_rec)
            
            return enriched_recommendations
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Response was: {llm_response[:500]}")
            return self._get_fallback_recommendations_structured()
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return self._get_fallback_recommendations_structured()
    
    def _format_anomaly(self, anomaly: Dict) -> Dict:
        """Format anomaly data for recommendation output."""
        if not anomaly:
            return None
        
        try:
            ts = anomaly.get('timestamp', '')
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            time_str = dt.strftime('%I:%M %p')
            date_str = dt.strftime('%b %d, %Y')
        except:
            time_str = "Unknown"
            date_str = "Unknown"
        
        return {
            "timestamp": anomaly.get('timestamp'),
            "demand_mw": anomaly.get('demand_mw', 0),
            "severity": anomaly.get('severity', 'unknown'),
            "confidence": anomaly.get('confidence', 0),
            "time_str": time_str,
            "date_str": date_str
        }
    
    def _get_fallback_recommendations(self) -> str:
        """Return fallback recommendations if LLM call fails."""
        return json.dumps([{
            "priority": "MEDIUM",
            "title": "🔄 System Operating Normally - Monitor Trends",
            "why": "Unable to generate AI recommendations at this time. Grid appears to be operating within normal parameters based on available data.",
            "actions": [
                {
                    "icon": "📊",
                    "action": "Monitor Key Metrics",
                    "details": "Continue monitoring demand forecasts and price trends",
                    "timeframe": "Ongoing"
                },
                {
                    "icon": "⚠️",
                    "action": "Review Alert Thresholds",
                    "details": "Ensure automated alerts are properly configured",
                    "timeframe": "Within 1 hour"
                },
                {
                    "icon": "🔧",
                    "action": "System Health Check",
                    "details": "Verify all monitoring systems are operational",
                    "timeframe": "Within 30 minutes"
                }
            ],
            "impact": {
                "financial": "Standard operational costs",
                "financial_type": "neutral",
                "reliability_risk": "LOW - Normal operations",
                "magnitude_mw": 0,
                "duration_estimate": "N/A"
            },
            "confidence": 70,
            "time_sensitive": False
        }])
    
    def _get_fallback_recommendations_structured(self) -> List[Dict]:
        """Return structured fallback recommendations."""
        fallback_json = self._get_fallback_recommendations()
        fallback_list = json.loads(fallback_json)
        
        return [{
            "timestamp": datetime.now().isoformat(),
            "anomaly": None,
            "analysis": {
                "source": "fallback",
                "model": "rule-based",
                "generated_at": datetime.now().isoformat()
            },
            "recommendation": rec
        } for rec in fallback_list]


# Convenience function for easy integration
def generate_llm_recommendations(
    predictions: List[Dict],
    price_forecast: List[Dict],
    current_demand: float,
    anomalies: List[Dict],
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini"
) -> List[Dict]:
    """
    Generate LLM-based recommendations (convenience function).
    
    Args:
        predictions: ML predictions list
        price_forecast: Price forecast list
        current_demand: Current demand in MW
        anomalies: List of detected anomalies
        api_key: OpenAI API key (optional, can use env variable)
        model: Model to use (default: gpt-4o-mini for cost-effectiveness)
    
    Returns:
        List of recommendation dictionaries
    """
    engine = LLMRecommendationEngine(api_key=api_key, model=model)
    return engine.generate_recommendations(
        predictions, price_forecast, current_demand, anomalies
    )
