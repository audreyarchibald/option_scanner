import aiohttp
import logging
from typing import List, Dict, Any
from .provider_base import DataProvider
from config import POLYGON_API_KEY
from utils.logger import logger

class PolygonProvider(DataProvider):
    """
    Polygon.io implementation of DataProvider.
    """
    BASE_URL = "https://api.polygon.io"
    
    def __init__(self, api_key: str = POLYGON_API_KEY):
        self.api_key = api_key
        self._cache = {}
        if not self.api_key:
            logger.warning("Polygon API Key not found! Please set POLYGON_API_KEY in .env or config.py")

    async def get_stock_price(self, symbol: str) -> float:
        """
        Fetch last trade price for underlying.
        """
        # Check cache (simple expiry could be added, but for now just hit API if not recently fetched)
        # Since this is a scanner, we probably want fresh data. 
        # But let's implement a short-lived cache or just simple dedup if called multiple times.
        
        url = f"{self.BASE_URL}/v2/last/trade/{symbol}"
        params = {"apiKey": self.api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Error fetching stock price for {symbol}: {response.status}")
                    return 0.0
                
                data = await response.json()
                return data.get("results", {}).get("p", 0.0)

    async def get_option_chain(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Fetch all options for a symbol using Snapshot API.
        """
        # Polygon Options Snapshot: v3/snapshot/options/{underlyingAsset}
        # This endpoint returns the entire chain with prices.
        # Note: Pagination might be required if using contracts endpoint, but snapshot usually returns all or a large set.
        # However, the snapshot endpoint can be heavy.
        
        url = f"{self.BASE_URL}/v3/snapshot/options/{symbol}"
        params = {
            "apiKey": self.api_key,
            "limit": 250  # Adjust as needed, snapshot might not support limit in same way as list
        }
        
        # Note: Snapshot API might require pagination if result is huge, but documentation says "Get the most up-to-date market data for all options contracts".
        # It handles pagination via next_url if there are too many contracts.
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            while url:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Error fetching options for {symbol}: {response.status}")
                        text = await response.text()
                        logger.error(text)
                        break
                        
                    data = await response.json()
                    results.extend(data.get("results", []))
                    
                    # Handle pagination
                    url = data.get("next_url")
                    # Clear params for next_url as it usually contains everything
                    if url:
                        params = {"apiKey": self.api_key}
                    
        return self._normalize_data(results)

    def _normalize_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize Polygon data to standard format.
        """
        normalized = []
        for item in raw_data:
            details = item.get("details", {})
            day = item.get("day", {})
            greeks = item.get("greeks", {})
            
            # Parse ticker to get details if needed, but details dict usually has it
            contract_type = details.get("contract_type")
            strike = details.get("strike_price")
            expiry = details.get("expiration_date")
            
            normalized.append({
                "symbol": details.get("ticker"),
                "underlying": item.get("underlying_asset", {}).get("ticker"),
                "strike": strike,
                "expiry": expiry,
                "type": contract_type,
                "bid": item.get("greeks", {}).get("bid") if "bid" in item else 0.0, # Snapshot structure varies slightly, usually at root or day
                # Checking actual snapshot structure: usually has 'last_quote' with bid/ask
                "bid_price": item.get("last_quote", {}).get("bid", 0.0),
                "ask_price": item.get("last_quote", {}).get("ask", 0.0),
                "last_price": day.get("close") or day.get("l", 0.0),
                "volume": day.get("volume") or day.get("v", 0),
                "open_interest": item.get("open_interest", 0),
                "implied_volatility": item.get("implied_volatility"),
                "delta": greeks.get("delta"),
                "gamma": greeks.get("gamma"),
                "theta": greeks.get("theta"),
                "vega": greeks.get("vega")
            })
        return normalized
