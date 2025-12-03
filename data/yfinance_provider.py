import yfinance as yf
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
from .provider_base import DataProvider
from config import RISK_FREE_RATE
from models.black_scholes import calculate_greeks
from utils.logger import logger

class YFinanceProvider(DataProvider):
    """
    YFinance implementation of DataProvider.
    Fetches data from Yahoo Finance and calculates Greeks locally.
    """
    
    def __init__(self):
        pass

    async def get_stock_price(self, symbol: str) -> float:
        """
        Fetch current spot price for the underlying symbol using yfinance.
        """
        try:
            # Run blocking yfinance call in a separate thread
            ticker = yf.Ticker(symbol)
            
            # fast_info is often faster for current price
            price = await asyncio.to_thread(lambda: ticker.fast_info.last_price)
            
            # Fallback if fast_info fails or is None (rare)
            if price is None:
                hist = await asyncio.to_thread(lambda: ticker.history(period="1d"))
                if not hist.empty:
                    price = hist["Close"].iloc[-1]
                else:
                    logger.error(f"Could not fetch price for {symbol} from yfinance.")
                    return 0.0
                    
            return float(price)
        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol}: {e}")
            return 0.0

    async def get_option_chain(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Fetch the full option chain for a given symbol and calculate Greeks.
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current price for Greek calculations
            spot_price = await self.get_stock_price(symbol)
            if spot_price == 0:
                return []
                
            # Get available expirations
            expirations = await asyncio.to_thread(lambda: ticker.options)
            
            if not expirations:
                logger.warning(f"No options found for {symbol}")
                return []
                
            all_options = []
            
            # We will fetch all expirations. 
            # Warning: This can be slow for tickers with many expirations (like SPY).
            # For a real scanner, we might want to limit to the next 4-6 weeks.
            # For now, let's fetch all but be mindful it might take time.
            
            # Use asyncio.gather to fetch expirations in parallel threads?
            # yfinance might have internal rate limiting or locking, but let's try batching.
            
            # Creating tasks for each expiration
            tasks = [self._fetch_chain_for_date(ticker, date, spot_price) for date in expirations]
            results = await asyncio.gather(*tasks)
            
            for res in results:
                all_options.extend(res)
                
            return all_options
            
        except Exception as e:
            logger.error(f"Error fetching option chain for {symbol}: {e}")
            return []

    async def _fetch_chain_for_date(self, ticker, date: str, spot_price: float) -> List[Dict[str, Any]]:
        """
        Helper to fetch and process a single expiration date.
        """
        try:
            # Run blocking call
            chain = await asyncio.to_thread(lambda: ticker.option_chain(date))
            
            calls = chain.calls
            puts = chain.puts
            
            results = []
            
            # Process Calls
            if not calls.empty:
                results.extend(self._process_dataframe(calls, date, "call", spot_price, ticker.ticker))
                
            # Process Puts
            if not puts.empty:
                results.extend(self._process_dataframe(puts, date, "put", spot_price, ticker.ticker))
                
            return results
            
        except Exception as e:
            logger.error(f"Error fetching options for {ticker.ticker} on {date}: {e}")
            return []

    def _process_dataframe(self, df: pd.DataFrame, expiry: str, option_type: str, S: float, symbol: str) -> List[Dict[str, Any]]:
        """
        Process yfinance DataFrame to standard format and calculate Greeks.
        """
        results = []
        
        # Calculate Time to Expiry (T)
        try:
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
            today = datetime.now().date()
            T = (expiry_date - today).days / 365.0
            
            # Avoid T=0 issues
            if T < 1/365.0:
                T = 1/365.0 # Minimum 1 day
        except Exception:
            T = 0.1 # Fallback
            
        r = RISK_FREE_RATE
        
        for _, row in df.iterrows():
            K = float(row["strike"])
            sigma = float(row["impliedVolatility"])
            
            # Calculate Greeks
            # Note: yfinance IV is sometimes 0 or crazy if illiquid.
            greeks = {
                'delta': None, 'gamma': None, 'theta': None, 'vega': None, 'rho': None
            }
            
            if sigma > 0 and T > 0:
                greeks = calculate_greeks(S, K, T, r, sigma, option_type)
            
            item = {
                "symbol": row["contractSymbol"],
                "underlying": symbol,
                "strike": K,
                "expiry": expiry,
                "type": option_type,
                "bid": row["bid"], # yfinance labels
                "bid_price": row["bid"],
                "ask_price": row["ask"],
                "last_price": row["lastPrice"],
                "volume": int(row["volume"]) if not pd.isna(row["volume"]) else 0,
                "open_interest": int(row["openInterest"]) if not pd.isna(row["openInterest"]) else 0,
                "implied_volatility": sigma,
                "delta": greeks['delta'],
                "gamma": greeks['gamma'],
                "theta": greeks['theta'],
                "vega": greeks['vega']
            }
            results.append(item)
            
        return results
