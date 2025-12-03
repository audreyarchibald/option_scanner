import asyncio
import pandas as pd
from data.yfinance_provider import YFinanceProvider

async def test_yfinance():
    print("Initializing YFinanceProvider...")
    provider = YFinanceProvider()
    
    ticker = "AAPL"
    print(f"Fetching stock price for {ticker}...")
    price = await provider.get_stock_price(ticker)
    print(f"Stock Price: {price}")
    
    print(f"Fetching option chain for {ticker} (this might take a moment)...")
    chain = await provider.get_option_chain(ticker)
    
    if not chain:
        print("No options data found!")
        return
        
    print(f"Fetched {len(chain)} contracts.")
    
    # Convert to DataFrame for nice display
    df = pd.DataFrame(chain)
    
    print("\n--- Sample Calls ---")
    print(df[df['type'] == 'call'][['symbol', 'strike', 'expiry', 'bid', 'ask_price', 'implied_volatility', 'delta', 'gamma']].head())
    
    print("\n--- Sample Puts ---")
    print(df[df['type'] == 'put'][['symbol', 'strike', 'expiry', 'bid', 'ask_price', 'implied_volatility', 'delta', 'gamma']].head())
    
    # Verify Greeks are calculated
    null_greeks = df['delta'].isnull().sum()
    if null_greeks < len(df):
        print(f"\nSuccess! Greeks calculated for {len(df) - null_greeks} contracts.")
    else:
        print("\nWarning: Greeks were not calculated properly (all null).")

if __name__ == "__main__":
    asyncio.run(test_yfinance())
