from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class DataProvider(ABC):
    """
    Abstract base class for data providers.
    """
    
    @abstractmethod
    async def get_option_chain(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Fetch the full option chain for a given symbol.
        Should return a list of dictionaries with standard keys:
        - symbol
        - strike
        - expiry
        - type (call/put)
        - bid
        - ask
        - last
        - volume
        - open_interest
        - implied_volatility (if available from source)
        """
        pass
    
    @abstractmethod
    async def get_stock_price(self, symbol: str) -> float:
        """
        Fetch current spot price for the underlying symbol.
        """
        pass
