import re
import time
import math
import json
from collections import defaultdict, deque
from datetime import datetime, timedelta
import requests
from llm_utils import gemini_llm  # Changed from relative to absolute import

# Constants for sentiment analysis
SENTIMENT_WINDOW_HOURS = 24
SENTIMENT_PATTERN_SIZE = 5  # Number of sentiment samples to detect patterns
MAX_COORD_MESSAGES = 50     # Max number of coordinated message samples to store

# Data structures
sentiment_history = defaultdict(lambda: deque(maxlen=SENTIMENT_WINDOW_HOURS*6))  # key -> deque of (timestamp, sentiment, message)
coordinated_messages = {}   # pattern_hash -> list of similar messages

def extract_key_phrases(text):
    """Extract key phrases from text for coordination detection"""
    # Simple extraction of noun phrases and financial terms
    # In production, use NLP techniques like noun phrase chunking
    phrases = []
    
    # Extract financial terms and phrases
    financial_terms = re.findall(r'\b(?:stock|share|price|market|ipo|invest|return|profit|grow|buy|sell)\w*\b', 
                                text.lower())
    
    # Extract potential stock symbols (uppercase words)
    symbols = re.findall(r'\b[A-Z]{2,6}\b', text)
    
    # Extract percentage figures
    percentages = re.findall(r'\d+(?:\.\d+)?%', text)
    
    # Extract price figures
    prices = re.findall(r'(?:₹|Rs\.?|INR)\s*\d+(?:,\d+)*(?:\.\d+)?', text)
    
    phrases = list(set(financial_terms + symbols + percentages + prices))
    return phrases

def get_sentiment_score(text):
    """Get sentiment score using the LLM"""
    prompt = (
        "Analyze the financial sentiment in this text. Return ONLY a JSON with these keys:\n"
        "- score: a number from -1.0 (extremely negative) to 1.0 (extremely positive)\n"
        "- is_promotional: boolean (true if it's promoting investment, false otherwise)\n"
        "- key_entities: list of mentioned companies/stocks/financial entities\n"
        "- key_claims: list of the main financial claims made\n\n"
        f"Text: {text}\n\n"
        "JSON response (nothing else):"
    )
    
    try:
        response = gemini_llm(prompt)
        # Clean response to extract just the JSON
        if response.strip().startswith('```'):
            response = response.strip().lstrip('```').rstrip('`').strip()
            if response.startswith('json'):
                response = response[4:].strip()
        result = json.loads(response)
        return result
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        return {
            "score": 0,
            "is_promotional": False,
            "key_entities": [],
            "key_claims": []
        }

def record_sentiment(message, entity=None):
    """
    Record sentiment for a message, optionally associated with a specific entity.
    Returns the sentiment analysis result.
    """
    sentiment_result = get_sentiment_score(message)
    score = sentiment_result.get("score", 0)
    
    now = time.time()
    # If entity is provided, record sentiment for that entity
    if entity:
        sentiment_history[entity].append((now, score, message))
    
    # Check for coordinated messaging
    key_phrases = extract_key_phrases(message)
    if key_phrases and sentiment_result.get("is_promotional", False):
        # Create a fingerprint from key phrases, claims, and sentiment direction
        fingerprint = "_".join(sorted(key_phrases)) + "_" + ("pos" if score > 0 else "neg")
        fingerprint_hash = hash(fingerprint) % 10000  # Simple hash
        
        if fingerprint_hash not in coordinated_messages:
            coordinated_messages[fingerprint_hash] = []
            
        if len(coordinated_messages[fingerprint_hash]) < MAX_COORD_MESSAGES:
            coordinated_messages[fingerprint_hash].append({
                "timestamp": now,
                "message": message,
                "score": score,
                "key_phrases": key_phrases,
                "key_claims": sentiment_result.get("key_claims", [])
            })
    
    return sentiment_result

def detect_sentiment_patterns(entity):
    """
    Detect patterns in sentiment for a specific entity.
    Returns pattern type and confidence if found.
    """
    data = list(sentiment_history[entity])
    if len(data) < SENTIMENT_PATTERN_SIZE:
        return None
    
    # Sort by timestamp
    data.sort(key=lambda x: x[0])
    
    timestamps = [t for t, _, _ in data]
    sentiments = [s for _, s, _ in data]
    
    # Pattern 1: Consistent positive sentiment
    if all(s > 0.5 for s in sentiments[-SENTIMENT_PATTERN_SIZE:]):
        return {
            "pattern": "consistently_positive",
            "confidence": 0.8,
            "description": "Consistently positive sentiment may indicate promotional campaign"
        }
    
    # Pattern 2: Sudden shift from negative to positive
    first_half = sentiments[:len(sentiments)//2]
    second_half = sentiments[len(sentiments)//2:]
    
    if len(first_half) > 2 and len(second_half) > 2:
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if first_avg < -0.2 and second_avg > 0.5:
            return {
                "pattern": "sentiment_shift",
                "confidence": 0.7,
                "description": "Sharp shift from negative to positive sentiment"
            }
    
    # Pattern 3: Oscillating sentiment (potential manipulation)
    if len(sentiments) >= 6:
        diffs = [abs(sentiments[i+1] - sentiments[i]) for i in range(len(sentiments)-1)]
        avg_diff = sum(diffs) / len(diffs)
        
        if avg_diff > 0.5:
            return {
                "pattern": "oscillating",
                "confidence": 0.6,
                "description": "Highly variable sentiment may indicate manipulation"
            }
    
    return None

def detect_coordinated_campaigns():
    """
    Detect potential coordinated messaging campaigns.
    Returns a list of detected campaigns.
    """
    campaigns = []
    
    # Look for clusters of similar messages in a short time period
    for fingerprint, messages in coordinated_messages.items():
        if len(messages) < 3:  # Need at least 3 similar messages to consider coordination
            continue
            
        # Sort by timestamp
        messages.sort(key=lambda x: x["timestamp"])
        
        # Check if messages are clustered in time
        timestamps = [m["timestamp"] for m in messages]
        time_span = max(timestamps) - min(timestamps)
        avg_interval = time_span / (len(timestamps) - 1) if len(timestamps) > 1 else float('inf')
        
        # If average interval is less than 2 hours, consider it suspicious
        if avg_interval < 7200 and len(messages) >= 3:
            # Calculate how similar the messages are
            key_phrases_sets = [set(m["key_phrases"]) for m in messages]
            union_size = len(set().union(*key_phrases_sets))
            intersection_size = len(set.intersection(*key_phrases_sets)) if key_phrases_sets else 0
            
            similarity = intersection_size / union_size if union_size > 0 else 0
            
            if similarity > 0.3:  # At least 30% similar phrases
                campaigns.append({
                    "id": fingerprint,
                    "message_count": len(messages),
                    "time_span_hours": time_span / 3600,
                    "avg_interval_minutes": avg_interval / 60,
                    "similarity": similarity,
                    "common_phrases": list(set.intersection(*key_phrases_sets)) if key_phrases_sets else [],
                    "sample_messages": [m["message"] for m in messages[:3]],  # Sample of messages
                    "confidence": min(0.9, (similarity * 0.5) + (0.5 * (1 - (avg_interval / 7200)))),
                    "first_seen": datetime.fromtimestamp(min(timestamps)).isoformat(),
                    "latest_seen": datetime.fromtimestamp(max(timestamps)).isoformat(),
                })
    
    # Sort by confidence
    campaigns.sort(key=lambda x: x["confidence"], reverse=True)
    return campaigns

if __name__ == "__main__":
    # Test with sample messages
    messages = [
        "GLENMARK stock is going to explode! Buy now before it's too late! Price target ₹1200",
        "Just heard from inside source that GLENMARK will rise 40% this week! BUY NOW!",
        "GLENMARK shares are set to double. Inside information from reliable source. Price target ₹1200",
        "The market is uncertain today due to global factors. HDFC Bank down 2%.",
        "GLENMARK is the best investment now! Will hit ₹1200 by next week!"
    ]
    
    # Record sentiments
    for msg in messages:
        sentiment = record_sentiment(msg, "GLENMARK")
        print(f"Message: {msg}\nSentiment: {sentiment}\n")
    
    # Detect patterns
    pattern = detect_sentiment_patterns("GLENMARK")
    print(f"Pattern: {pattern}")
    
    # Detect campaigns
    campaigns = detect_coordinated_campaigns()
    print(f"Campaigns: {campaigns}")
