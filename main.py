import asyncio
import argparse
import polars as pl
import os
from datetime import datetime

from config import DATA_PROVIDER, REPORTS_DIR, CHARTS_DIR
from utils.logger import logger
from data.polygon_provider import PolygonProvider
from scanners.iv_scanner import scan_iv
from scanners.uoa_scanner import scan_uoa
from scanners.delta_scanner import scan_delta
from scanners.mispricing_scanner import scan_mispricing, calculate_theoretical_price
from scanners.spread_scanner import scan_spreads
from utils.visualization import plot_iv_smile, plot_delta_heatmap, plot_volume_oi

async def process_ticker(ticker: str, provider):
    logger.info(f"Fetching data for {ticker}...")
    
    # Fetch Stock Price
    price = await provider.get_stock_price(ticker)
    if price == 0:
        logger.error(f"Could not fetch price for {ticker}. Skipping.")
        return
        
    logger.info(f"{ticker} Spot Price: {price}")
    
    # Fetch Option Chain
    chain = await provider.get_option_chain(ticker)
    if not chain:
        logger.warning(f"No options data for {ticker}.")
        return

    # Convert to Polars DataFrame
    df = pl.DataFrame(chain)
    
    # Ensure numeric columns
    numeric_cols = ["strike", "bid_price", "ask_price", "last_price", "volume", "open_interest", "implied_volatility", "delta", "gamma", "theta", "vega"]
    for col in numeric_cols:
        df = df.with_columns(pl.col(col).cast(pl.Float64).fill_null(0.0))
        
    logger.info(f"Processing {len(df)} contracts for {ticker}...")

    # --- 1. Calculate Theoretical Prices & Mispricing ---
    df = calculate_theoretical_price(df, price)
    
    # --- 2. Run Scanners ---
    
    # IV Scanner
    iv_signals = scan_iv(df)
    
    # UOA Scanner
    uoa_signals = scan_uoa(df)
    
    # Spread Scanner
    spread_signals = scan_spreads(df)
    
    # Delta Buckets
    df = scan_delta(df) # Adds bucket column
    
    # Mispricing Scanner (already computed signals in calculate_theoretical_price, but let's filter)
    mispricing_signals = scan_mispricing(df)
    
    # Combine Signals
    # We want a master report of "Interesting" options
    
    # Let's collect all rows that have ANY signal
    # iv_signals has "signal" column
    # uoa_signals has "signal" column
    # spread_signals has "spread_signal"
    # mispricing_signals has "mispricing_signal"
    
    # It's easier to join them back or just add columns to the main DF and filter
    
    # Let's augment the main DF with signals
    
    # Join IV signals
    # We need a unique key. Symbol + Expiry + Strike + Type
    # Or just run the logic again on the main DF to add columns instead of filtering.
    # The scanner functions currently filter.
    # Let's adjust approach: The scanners return a subset. We can concat the subsets for a "Signals Report".
    
    all_signals = []
    
    if not iv_signals.is_empty():
        all_signals.append(iv_signals.select(["symbol", "strike", "expiry", "type", "signal"]))
        
    if not uoa_signals.is_empty():
        all_signals.append(uoa_signals.select(["symbol", "strike", "expiry", "type", "signal"]))
        
    if not spread_signals.is_empty():
         all_signals.append(spread_signals.rename({"spread_signal": "signal"}).select(["symbol", "strike", "expiry", "type", "signal"]))
         
    if not mispricing_signals.is_empty():
        all_signals.append(mispricing_signals.rename({"mispricing_signal": "signal"}).select(["symbol", "strike", "expiry", "type", "signal"]))
        
    if all_signals:
        report_df = pl.concat(all_signals)
        
        # Save Report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(REPORTS_DIR, f"{ticker}_signals_{timestamp}.csv")
        report_df.write_csv(report_path)
        logger.info(f"Saved signals report to {report_path}")
        
        # Print Top Opportunities
        print(f"\n--- TOP SIGNALS FOR {ticker} ---")
        print(report_df.head(10))
        
    else:
        logger.info(f"No significant signals found for {ticker}.")
        
    # Save Full Chain with Greeks (Optional, maybe too big)
    # df.write_csv(os.path.join(REPORTS_DIR, f"{ticker}_full_chain.csv"))

    # --- 3. Visualizations ---
    logger.info("Generating charts...")
    plot_iv_smile(df, ticker)
    plot_delta_heatmap(df, ticker)
    plot_volume_oi(df, ticker)
    logger.info("Charts generated.")

async def main():
    parser = argparse.ArgumentParser(description="Option Scanner")
    parser.add_argument("tickers", nargs="+", help="List of tickers to scan (e.g. SPY QQQ AAPL)")
    args = parser.parse_args()
    
    # Create output directories if not exist
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(CHARTS_DIR, exist_ok=True)
    
    # Initialize Provider
    if DATA_PROVIDER.lower() == "polygon":
        provider = PolygonProvider()
    else:
        logger.error(f"Unknown provider: {DATA_PROVIDER}")
        return

    # Process tickers
    tasks = [process_ticker(ticker, provider) for ticker in args.tickers]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
