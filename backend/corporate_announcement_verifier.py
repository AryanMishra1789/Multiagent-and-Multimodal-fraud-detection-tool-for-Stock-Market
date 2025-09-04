"""
Corporate Announcement Verification Module

This module is designed to detect and analyze misleading or false corporate announcements
from listed companies by comparing them with historical data, market reactions,
and regulatory requirements.
"""

import requests
import re
import json
import functools
import time
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for announcement analysis
ANNOUNCEMENT_KEYWORDS = [
    'financial results', 'quarterly results', 'annual results', 'profit', 'loss',
    'dividend', 'bonus', 'merger', 'acquisition', 'takeover', 'stake', 'investment',
    'expansion', 'new product', 'launch', 'contract', 'order', 'partnership',
    'joint venture', 'agreement', 'restructuring', 'layoff', 'workforce reduction',
    'debt', 'fundraising', 'rights issue', 'buy back', 'settlement', 'legal',
    'litigation', 'patent', 'regulatory approval', 'fda', 'clinical trial',
    'breakthrough', 'milestone', 'guidance', 'forecast', 'outlook'
]

# Keywords that might indicate exaggeration or potential misleading information
SUSPICIOUS_KEYWORDS = [
    'record breaking', 'unprecedented', 'revolutionary', 'game[ -]?changing',
    'breakthrough', 'extraordinary', 'massive', 'tremendous', 'spectacular',
    'guaranteed', 'assured', 'certain', 'landmark', 'blockbuster', 'industry[ -]?leading',
    'first[- ]ever', 'highest[- ]ever', 'best[- ]ever', 'transformational', 
    'disruptive'
]

# Keywords that might indicate speculative announcements
SPECULATIVE_KEYWORDS = [
    'exploring', 'considering', 'evaluating', 'potential', 'possible', 'may',
    'might', 'could', 'looking into', 'preliminary', 'non-binding', 'letter of intent',
    'memorandum of understanding', 'proposed', 'anticipated', 'expected'
]

# Corporate announcement sources
BSE_ANNOUNCEMENT_URL = "https://www.bseindia.com/corporates/ann.html"
NSE_ANNOUNCEMENT_URL = "https://www.nseindia.com/companies-listing/corporate-announcements"

class CorporateAnnouncementVerifier:
    """
    Verifies corporate announcements by comparing them with actual data,
    market reactions, and detecting potentially misleading information.
    """
    
    def __init__(self):
        self.announcement_cache = {}
        self.company_data_cache = {}
        self.financial_data_cache = {}
    
    def fetch_recent_announcements(self, symbol: str, exchange: str = "both") -> List[Dict]:
        """
        Fetch recent corporate announcements for a given company
        
        Args:
            symbol: Company symbol/ticker
            exchange: 'bse', 'nse', or 'both'
            
        Returns:
            List of announcement dictionaries
        """
        announcements = []
        
        # First try to use direct API endpoints where available
        try:
            if exchange.lower() in ["both", "bse"]:
                bse_announcements = self._fetch_bse_announcements(symbol)
                announcements.extend(bse_announcements)
                
            if exchange.lower() in ["both", "nse"]:
                nse_announcements = self._fetch_nse_announcements(symbol)
                announcements.extend(nse_announcements)
        except Exception as e:
            logger.error(f"Error fetching official announcements: {e}")
            
        # If official sources fail, try alternative sources like MoneyControl
        if not announcements:
            try:
                alt_announcements = self._fetch_alternative_announcements(symbol)
                announcements.extend(alt_announcements)
            except Exception as e:
                logger.error(f"Error fetching alternative announcements: {e}")
        
        # Cache the announcements
        self.announcement_cache[symbol] = announcements
        
        return announcements
    
    def _fetch_bse_announcements(self, symbol: str) -> List[Dict]:
        """
        Fetch announcements from BSE
        """
        # This would normally use BSE's API, but for demo we'll create sample data
        # In a real implementation, you would parse from BSE website or API
        
        # Placeholder implementation
        return []
    
    def _fetch_nse_announcements(self, symbol: str) -> List[Dict]:
        """
        Fetch announcements from NSE
        """
        # This would normally use NSE's API, but for demo we'll create sample data
        # In a real implementation, you would parse from NSE website or API
        
        # Placeholder implementation
        return []
    
    def _fetch_alternative_announcements(self, symbol: str) -> List[Dict]:
        """
        Fetch announcements from alternative sources like MoneyControl
        """
        try:
            # Try to get data from MoneyControl
            symbol_search = symbol.replace('&', '%26')
            search_url = f"https://www.moneycontrol.com/stocks/company_info/stock_news.php?sc_id={symbol_search}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            # This is just a placeholder - in real implementation we would parse the page
            # For the demo, return some sample data
            
            # Get today's date for sample data
            today = datetime.now()
            
            # Sample announcements - in a real implementation these would be parsed from websites
            sample_data = [
                {
                    "date": (today - timedelta(days=2)).strftime("%d-%b-%Y"),
                    "title": f"{symbol} Reports Q1 Results: Revenue up 15%, Net Profit Rises 22%",
                    "description": "The company announced strong quarterly results exceeding market expectations.",
                    "url": f"https://www.example.com/news/{symbol}-q1-results",
                    "source": "MoneyControl",
                    "category": "Financial Results"
                },
                {
                    "date": (today - timedelta(days=5)).strftime("%d-%b-%Y"),
                    "title": f"{symbol} Announces New Product Launch",
                    "description": "The company unveiled a revolutionary new product that could transform the industry.",
                    "url": f"https://www.example.com/news/{symbol}-new-product",
                    "source": "MoneyControl",
                    "category": "Product Launch"
                },
                {
                    "date": (today - timedelta(days=10)).strftime("%d-%b-%Y"),
                    "title": f"{symbol} Exploring Potential Acquisition",
                    "description": "The company is in preliminary talks for a strategic acquisition to expand market share.",
                    "url": f"https://www.example.com/news/{symbol}-acquisition-talks",
                    "source": "MoneyControl",
                    "category": "Merger/Acquisition"
                }
            ]
            
            return sample_data
        except Exception as e:
            logger.error(f"Error fetching alternative announcements: {e}")
            return []
    
    @functools.lru_cache(maxsize=128)
    def get_stock_reaction(self, symbol: str, announcement_date: str) -> Dict:
        """
        Analyze stock price reaction to an announcement
        
        Args:
            symbol: Company symbol/ticker
            announcement_date: Date of announcement in 'DD-MM-YYYY' format
            
        Returns:
            Dictionary with price reaction analysis
        """
        from announcement_utils import get_cached_stock_data, calculate_price_impact
        
        start_time = time.time()
        try:
            # Convert date string to datetime object
            try:
                ann_date = datetime.strptime(announcement_date, "%d-%b-%Y")
            except ValueError:
                try:
                    ann_date = datetime.strptime(announcement_date, "%Y-%m-%d")
                except ValueError:
                    ann_date = datetime.strptime(announcement_date, "%d-%m-%Y")
            
            # Get data for a period before and after announcement (with caching)
            start_date = ann_date - timedelta(days=15)
            end_date = ann_date + timedelta(days=15)
            
            # Try with different symbol formats using parallel requests
            symbols_to_try = [symbol]
            if not any(suffix in symbol for suffix in [".NS", ".BO"]):
                symbols_to_try.extend([f"{symbol}.NS", f"{symbol}.BO"])
            
            # Get stock data with caching
            hist = None
            for sym in symbols_to_try:
                hist = get_cached_stock_data(sym, start_date, end_date)
                if not hist.empty:
                    symbol = sym  # Update symbol to the one that worked
                    break
            
            if hist is None or hist.empty:
                logger.warning(f"Could not fetch stock data for {symbol}")
                return {
                    "error": "Could not fetch stock price data", 
                    "processing_time_ms": int((time.time() - start_time) * 1000)
                }
            
            # Find the nearest trading day to the announcement date
            nearest_date = min(hist.index, key=lambda x: abs(x - pd.Timestamp(ann_date)))
            
            # Get indices for before and after periods
            date_idx = hist.index.get_loc(nearest_date)
            
            # Get data before and after announcement
            if date_idx > 0 and date_idx < len(hist) - 1:
                before_price = hist["Close"].iloc[date_idx - 1]
                announcement_price = hist["Close"].iloc[date_idx]
                after_price = hist["Close"].iloc[date_idx + 1]
                
                # Calculate changes
                day_of_change = ((announcement_price / before_price) - 1) * 100
                next_day_change = ((after_price / announcement_price) - 1) * 100
                total_change = ((after_price / before_price) - 1) * 100
                
                # Calculate abnormal volume
                avg_volume = hist["Volume"].iloc[max(0, date_idx-10):date_idx].mean()
                announcement_volume = hist["Volume"].iloc[date_idx]
                volume_ratio = announcement_volume / avg_volume if avg_volume > 0 else 0
                
                # Calculate volatility
                returns = hist["Close"].pct_change()
                before_volatility = returns.iloc[max(0, date_idx-10):date_idx].std() * (252 ** 0.5) * 100
                after_volatility = returns.iloc[date_idx:min(len(hist), date_idx+10)].std() * (252 ** 0.5) * 100
                
                result = {
                    "symbol": symbol,
                    "announcement_date": nearest_date.strftime("%Y-%m-%d"),
                    "price_before": float(before_price),
                    "price_on_announcement": float(announcement_price),
                    "price_after": float(after_price),
                    "day_of_change_pct": float(day_of_change),
                    "next_day_change_pct": float(next_day_change),
                    "total_change_pct": float(total_change),
                    "volume_ratio": float(volume_ratio),
                    "volume_abnormal": volume_ratio > 2.0,
                    "volatility_before": float(before_volatility),
                    "volatility_after": float(after_volatility),
                    "volatility_increase": after_volatility > before_volatility * 1.5,
                    "significant_reaction": abs(total_change) > 5 or volume_ratio > 3,
                    "processing_time_ms": int((time.time() - start_time) * 1000)
                }
                return result
            else:
                return {
                    "error": "Announcement date too close to data boundaries", 
                    "processing_time_ms": int((time.time() - start_time) * 1000)
                }
                
        except Exception as e:
            logger.error(f"Error analyzing stock reaction: {e}")
            return {
                "error": f"Error analyzing stock reaction: {str(e)}",
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
    
    def analyze_financial_reality(self, symbol: str, announcement: Dict) -> Dict:
        """
        Analyze if an announcement matches financial reality
        
        Args:
            symbol: Company symbol/ticker
            announcement: Announcement dictionary
            
        Returns:
            Dictionary with analysis of financial reality
        """
        try:
            # Extract key claims from announcement
            title = announcement.get("title", "")
            description = announcement.get("description", "")
            
            # Combine title and description for analysis
            full_text = f"{title}. {description}"
            
            # Extract financial claims
            financial_claims = self._extract_financial_claims(full_text)
            
            # Get actual financial data
            financial_data = self._get_financial_data(symbol)
            
            # Compare claims with reality
            mismatches = []
            
            for claim in financial_claims:
                if claim["type"] == "revenue_growth":
                    claimed_growth = claim["value"]
                    actual_growth = financial_data.get("revenue_growth", 0)
                    
                    if actual_growth is not None and abs(claimed_growth - actual_growth) > 5:
                        mismatches.append({
                            "claim_type": "revenue_growth",
                            "claimed": f"{claimed_growth}%",
                            "actual": f"{actual_growth}%",
                            "discrepancy": abs(claimed_growth - actual_growth)
                        })
                
                elif claim["type"] == "profit_growth":
                    claimed_growth = claim["value"]
                    actual_growth = financial_data.get("profit_growth", 0)
                    
                    if actual_growth is not None and abs(claimed_growth - actual_growth) > 10:
                        mismatches.append({
                            "claim_type": "profit_growth",
                            "claimed": f"{claimed_growth}%",
                            "actual": f"{actual_growth}%",
                            "discrepancy": abs(claimed_growth - actual_growth)
                        })
            
            # Look for exaggeration patterns
            exaggerations = self._detect_exaggerations(full_text)
            
            # Check for speculative language
            speculative = self._detect_speculative_language(full_text)
            
            return {
                "claims_analyzed": len(financial_claims),
                "mismatches_found": len(mismatches),
                "mismatches": mismatches,
                "exaggerations": exaggerations,
                "speculative_language": speculative,
                "has_issues": len(mismatches) > 0 or len(exaggerations) > 3 or len(speculative) > 3
            }
                
        except Exception as e:
            logger.error(f"Error analyzing financial reality: {e}")
            return {"error": str(e)}
    
    def _extract_financial_claims(self, text: str) -> List[Dict]:
        """
        Extract financial claims from announcement text
        """
        claims = []
        
        # Look for revenue growth claims
        revenue_patterns = [
            r'revenue up (\d+(?:\.\d+)?)%',
            r'revenue growth of (\d+(?:\.\d+)?)%',
            r'revenue increased by (\d+(?:\.\d+)?)%',
            r'sales up (\d+(?:\.\d+)?)%'
        ]
        
        for pattern in revenue_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                try:
                    value = float(match.group(1))
                    claims.append({
                        "type": "revenue_growth",
                        "value": value,
                        "text": match.group(0)
                    })
                except:
                    pass
        
        # Look for profit growth claims
        profit_patterns = [
            r'profit up (\d+(?:\.\d+)?)%',
            r'profit growth of (\d+(?:\.\d+)?)%',
            r'profit increased by (\d+(?:\.\d+)?)%',
            r'net income up (\d+(?:\.\d+)?)%',
            r'earnings up (\d+(?:\.\d+)?)%'
        ]
        
        for pattern in profit_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                try:
                    value = float(match.group(1))
                    claims.append({
                        "type": "profit_growth",
                        "value": value,
                        "text": match.group(0)
                    })
                except:
                    pass
        
        # More claim types could be added here
        
        return claims
    
    def _get_financial_data(self, symbol: str) -> Dict:
        """
        Get actual financial data for a company
        """
        # In a real implementation, this would fetch actual financial data
        # For the demo, we'll return simulated data
        
        # Check if we have cached data
        if symbol in self.financial_data_cache:
            return self.financial_data_cache[symbol]
        
        # Generate some sample data for demonstration
        import random
        
        data = {
            "revenue_growth": round(random.uniform(5, 20), 1),
            "profit_growth": round(random.uniform(-5, 30), 1),
            "eps_growth": round(random.uniform(-10, 25), 1),
            "last_reported_quarter": "2023-06-30"
        }
        
        # Cache the data
        self.financial_data_cache[symbol] = data
        
        return data
    
    def _detect_exaggerations(self, text: str) -> List[str]:
        """
        Detect exaggerated claims in the announcement
        """
        exaggerations = []
        
        for keyword in SUSPICIOUS_KEYWORDS:
            pattern = r'\b' + keyword + r'\b'
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                # Get some context around the match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                exaggerations.append({
                    "term": match.group(0),
                    "context": context
                })
        
        return exaggerations
    
    def _detect_speculative_language(self, text: str) -> List[str]:
        """
        Detect speculative language in the announcement
        """
        speculative_terms = []
        
        for keyword in SPECULATIVE_KEYWORDS:
            pattern = r'\b' + keyword + r'\b'
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                # Get some context around the match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                speculative_terms.append({
                    "term": match.group(0),
                    "context": context
                })
        
        return speculative_terms
    
    def verify_announcement(self, symbol: str, announcement: Dict) -> Dict:
        """
        Comprehensive verification of a corporate announcement
        
        Args:
            symbol: Company symbol/ticker
            announcement: Announcement dictionary
            
        Returns:
            Verification result with detailed analysis
        """
        # Get stock price reaction
        date_str = announcement.get("date", datetime.now().strftime("%d-%b-%Y"))
        market_reaction = self.get_stock_reaction(symbol, date_str)
        
        # Analyze financial reality
        financial_analysis = self.analyze_financial_reality(symbol, announcement)
        
        # Check for regulatory red flags (simple implementation for demo)
        regulatory_issues = self._check_regulatory_issues(announcement)
        
        # Overall determination
        is_misleading = False
        risk_score = 0
        risk_factors = []
        
        # Check credibility score from announcement data
        credibility_score = announcement.get("credibility_score", 0.5)
        
        # Apply strong penalty for low credibility
        if credibility_score < 0.3:
            risk_score += 60  # Major red flag for very low credibility
            risk_factors.append(f"Very low credibility score ({credibility_score:.2f})")
        elif credibility_score < 0.5:
            risk_score += 40  # Significant penalty for moderately low credibility
            risk_factors.append(f"Low credibility score ({credibility_score:.2f})")
        
        # Financial mismatches increase risk score
        if financial_analysis.get("mismatches_found", 0) > 0:
            risk_score += 30
            risk_factors.append(f"Financial claims don't match reality ({financial_analysis['mismatches_found']} discrepancies)")
        
        # Exaggerations increase risk score
        exaggeration_count = len(financial_analysis.get("exaggerations", []))
        if exaggeration_count > 2:
            risk_score += min(20, exaggeration_count * 5)
            risk_factors.append(f"Announcement contains {exaggeration_count} exaggerated terms")
        
        # Speculative language increases risk score
        speculative_count = len(financial_analysis.get("speculative_language", []))
        if speculative_count > 2:
            risk_score += min(15, speculative_count * 3)
            risk_factors.append(f"Announcement contains {speculative_count} speculative terms")
        
        # Look for specific high-risk patterns
        text = announcement.get("text", "") or announcement.get("description", "")
        if re.search(r"multibagger|penny stock", text, re.IGNORECASE):
            risk_score += 50  # Major red flag
            risk_factors.append("Contains high-risk terms (multibagger/penny stock)")
            
        if re.search(r"([5-9][0-9]|[1-9][0-9]{2,})%\s*returns?\s*(in|within)?\s*\d+\s*(days?|weeks?)", text, re.IGNORECASE):
            risk_score += 70  # Critical red flag
            risk_factors.append("Promises unrealistic returns in short timeframe")
        
        # Suspicious market reaction increases risk score
        if market_reaction.get("significant_reaction", False):
            if abs(market_reaction.get("total_change_pct", 0)) > 10:
                risk_score += 20
                risk_factors.append(f"Unusual price movement ({market_reaction.get('total_change_pct', 0):.1f}%) following announcement")
            
            if market_reaction.get("volume_abnormal", False):
                risk_score += 15
                risk_factors.append(f"Abnormal trading volume ({market_reaction.get('volume_ratio', 0):.1f}x normal) on announcement")
        
        # Regulatory issues increase risk score
        if regulatory_issues.get("has_issues", False):
            risk_score += 25
            risk_factors.append(f"Potential regulatory issues: {regulatory_issues.get('main_issue', 'Compliance concern')}")
        
        # Determine if misleading based on risk score (lower threshold to catch more cases)
        is_misleading = risk_score >= 40  # Lowered from 50 to catch more suspicious messages
        
        # If credibility score is very low, force classification as misleading regardless of risk score
        if announcement.get("credibility_score", 1.0) <= 0.2:
            is_misleading = True
            if "Very low credibility score" not in " ".join(risk_factors):
                risk_factors.append("Critical: Extremely low credibility score")
        
        # If text contains specific high-risk phrases, always mark as misleading
        text = announcement.get("text", "") or announcement.get("description", "")
        high_risk_phrases = [
            r"multibagger penny stock",
            r"([1-9][0-9]{2,})%\s*returns?\s*in",
            r"guaranteed profit",
            r"pump and dump"
        ]
        
        for phrase in high_risk_phrases:
            if re.search(phrase, text, re.IGNORECASE):
                is_misleading = True
                break
                
        return {
            "symbol": symbol,
            "announcement": announcement,
            "verification_timestamp": datetime.now().isoformat(),
            "is_misleading": is_misleading,
            "risk_score": risk_score,
            "risk_level": "high" if risk_score >= 70 else "medium" if risk_score >= 40 else "low",
            "risk_factors": risk_factors,
            "market_reaction": market_reaction,
            "financial_analysis": financial_analysis,
            "regulatory_issues": regulatory_issues,
            "action_recommended": "Investigate further" if is_misleading else "No concerns"
        }
    
    def _check_regulatory_issues(self, announcement: Dict) -> Dict:
        """
        Check for regulatory issues with an announcement
        """
        # In a real implementation, this would check against regulatory requirements
        # For the demo, we'll do some simple checks
        
        title = announcement.get("title", "")
        description = announcement.get("description", "")
        full_text = f"{title}. {description}"
        
        issues = []
        
        # Check for forward-looking statements without disclaimers
        if re.search(r'will\s+(?:be|reach|achieve|grow|increase)', full_text, re.IGNORECASE) and not re.search(r'forward[ -]looking|projection', full_text, re.IGNORECASE):
            issues.append("Forward-looking statements without proper disclaimers")
        
        # Check for absolute claims
        if re.search(r'best|guaranteed|certain|assured', full_text, re.IGNORECASE):
            issues.append("Contains absolute claims or guarantees")
        
        # Check for missing attribution
        if re.search(r'experts|analysts|studies show', full_text, re.IGNORECASE) and not re.search(r'according to|cited|referenced|published', full_text, re.IGNORECASE):
            issues.append("References experts or studies without attribution")
        
        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
            "main_issue": issues[0] if issues else None,
            "total_issues": len(issues)
        }

# Initialize the verifier
corporate_verifier = CorporateAnnouncementVerifier()

def verify_corporate_announcement(symbol: str, announcement_text: str = None, announcement_date: str = None) -> Dict:
    """
    Main function to verify corporate announcements
    
    Args:
        symbol: Company symbol/ticker
        announcement_text: Optional specific announcement text to verify
        announcement_date: Optional date of announcement to verify
        
    Returns:
        Verification result with detailed analysis
    """
    try:
        # Import optimized utilities for parallel processing
        from announcement_utils import prefetch_data, check_announcement_credibility, fast_stock_check, detect_pump_and_dump_language
        from announcement_utils_optimized import analyze_in_parallel_optimized, ultra_fast_stock_check
        
        # Fast check for obvious scams to short-circuit expensive operations
        fast_mode = True  # Default to fast mode to reduce API dependency
        
        # Import to check for pump and dump language patterns
        from announcement_utils import detect_pump_and_dump_language
        
        # First, check if this is an obvious pump and dump scheme
        pump_dump_check = None
        if announcement_text:
            pump_dump_check = detect_pump_and_dump_language(announcement_text)
            if pump_dump_check.get("is_pump_and_dump", False):
                logger.warning(f"Ultra-fast detection identified pump and dump language")
                # We can skip most analysis for obvious pump and dump schemes
                return {
                    "symbol": symbol,
                    "verification_timestamp": datetime.now().isoformat(),
                    "is_misleading": True,
                    "category": "pump_and_dump_scheme",
                    "risk_score": 95,
                    "risk_level": "high",
                    "verification_type": "ultra_fast",
                    "risk_factors": [
                        f"Contains clear pump and dump language: {pump_dump_check.get('detected_phrases', [])}",
                        "Message matches known scam patterns"
                    ],
                    "warning": "This message contains language commonly used in pump and dump schemes"
                }
        
        # Perform quick stock symbol check without API calls
        quick_stock_check = fast_stock_check(symbol)
        if not quick_stock_check.get("exists", True) and quick_stock_check.get("warning", ""):
            # If it's likely a fake stock symbol, short-circuit with a scam response
            logger.warning(f"Detected likely fake stock symbol: {symbol}")
            
            if announcement_text:
                # Still check the text for scam indicators
                credibility = check_announcement_credibility(announcement_text)
                pump_dump = analyze_in_parallel_optimized(
                    text=announcement_text,
                    symbol=symbol,
                    announcement_date=announcement_date or datetime.now().strftime("%d-%b-%Y"),
                    fast_mode=True,
                    max_timeout=10
                ).get("text_analysis", {}).get("pump_and_dump", {})
                
                return {
                    "symbol": symbol,
                    "verification_timestamp": datetime.now().isoformat(),
                    "is_misleading": True,
                    "risk_score": 90,
                    "risk_level": "high",
                    "risk_factors": [
                        "Potential fake stock symbol commonly used in scams",
                        f"Low credibility score: {credibility:.2f}",
                        "Contains pump and dump language" if pump_dump.get("is_pump_and_dump", False) else ""
                    ],
                    "warning": "Potential fake stock symbol detected"
                }
        
        # If needed, start prefetching data in background for verified symbols
        if quick_stock_check.get("exists", False) and fast_mode == False:
            prefetch_data(symbol)
        
        # If specific announcement text is provided, create an announcement object
        if announcement_text:
            # Use parallel processing for faster analysis
            start_time = datetime.now()
            logger.info(f"Starting parallel verification for {symbol} (fast_mode={fast_mode})")
            
            # Run analyses in parallel with optimized version
            parallel_results = analyze_in_parallel_optimized(
                text=announcement_text,
                symbol=symbol,
                announcement_date=announcement_date or datetime.now().strftime("%d-%b-%Y"),
                fast_mode=fast_mode,
                max_timeout=15
            )
            
            # Create announcement object
            announcement = {
                "date": announcement_date or datetime.now().strftime("%d-%b-%Y"),
                "title": announcement_text[:100],  # First 100 chars as title
                "text": announcement_text,
                "source": "User Input",
                "category": "Unknown"
            }
            
            # Direct credibility check for better accuracy with our new patterns
            credibility_score = check_announcement_credibility(announcement_text)
            
            # Enhance the announcement with parallel results and direct credibility check
            announcement["sentiment"] = parallel_results.get("text_analysis", {}).get("sentiment", {})
            announcement["credibility_score"] = min(
                credibility_score,  # Direct check
                parallel_results.get("text_analysis", {}).get("credibility_score", 0.5)  # Parallel check
            )
            
            # Check for common scam indicators in penny stocks/pump-and-dump
            pump_dump_results = parallel_results.get("text_analysis", {}).get("pump_and_dump", {})
            if pump_dump_results.get("is_pump_and_dump", False) and pump_dump_results.get("confidence", 0) > 0.6:
                # Force very low credibility for high-confidence pump-and-dump detection
                announcement["credibility_score"] = 0.1
                announcement["scam_indicators"] = pump_dump_results.get("indicators", [])
            
            # Log performance improvement
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Parallel verification completed in {elapsed:.2f} seconds")
            
            # Verify the specific announcement with enhanced data
            return corporate_verifier.verify_announcement(symbol, announcement)
        else:
            # Fetch recent announcements
            announcements = corporate_verifier.fetch_recent_announcements(symbol)
            
            if not announcements:
                return {
                    "symbol": symbol,
                    "error": "No recent announcements found",
                    "success": False
                }
            
            # If date is provided, find the matching announcement
            if announcement_date:
                matching = [a for a in announcements if a.get("date") == announcement_date]
                if matching:
                    # Verify the specific announcement
                    return corporate_verifier.verify_announcement(symbol, matching[0])
            
            # Otherwise verify the most recent announcement
            return corporate_verifier.verify_announcement(symbol, announcements[0])
    
    except Exception as e:
        logger.error(f"Error in verify_corporate_announcement: {e}")
        return {
            "symbol": symbol,
            "error": str(e),
            "success": False
        }

# For testing
if __name__ == "__main__":
    # Test with a sample announcement
    sample_announcement = "XYZ Ltd announces revolutionary new product that will transform the industry. Revenue expected to grow by 50% next quarter with profit margins expanding to unprecedented levels. This guaranteed growth makes XYZ the market leader."
    
    result = verify_corporate_announcement("INFY", sample_announcement)
    print(json.dumps(result, indent=2))
