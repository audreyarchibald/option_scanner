import polars as pl
import numpy as np
from models.black_scholes import bs_price
from config import RISK_FREE_RATE
from datetime import datetime, timedelta

def scan_mispricing(df: pl.DataFrame) -> pl.DataFrame:
    """
    Returns only the rows flagged as mispriced.
    Assumes 'mispricing_signal' column exists (added by calculate_theoretical_price).
    """
    if "mispricing_signal" not in df.columns:
        return pl.DataFrame(schema=df.schema)
        
    return df.filter(pl.col("mispricing_signal").is_not_null())
    
def calculate_theoretical_price(df: pl.DataFrame, underlying_price: float) -> pl.DataFrame:
    """
    Augments DF with theoretical_price and mispricing_signal.
    Returns the FULL DataFrame with new columns.
    """
    # Add underlying price
    df = df.with_columns(pl.lit(underlying_price).alias("S"))
    
    # Calculate T (years)
    df = df.with_columns(
        pl.col("expiry").str.strptime(pl.Date, "%Y-%m-%d").alias("expiry_date")
    )
    
    today = datetime.now().date()
    
    df = df.with_columns(
        ((pl.col("expiry_date") - pl.lit(today)).dt.total_days() / 365.0).alias("T")
    )
    
    # Filter out expired or T<=0 for calculation safety (masking)
    # We won't remove rows, just handle calc
    
    # Extract numpy arrays for BS calculation
    S = df["S"].to_numpy()
    K = df["strike"].to_numpy()
    T_vals = df["T"].to_numpy()
    sigma = df["implied_volatility"].fill_null(0).to_numpy()
    r = RISK_FREE_RATE
    
    # Types
    types = df["type"].to_numpy() # 'call' or 'put'
    
    prices = np.zeros(len(df))
    
    # Calculate mask for valid options (T > 0)
    valid_mask = (T_vals > 0.001)
    
    # Calls
    call_mask = (types == 'call') & valid_mask
    if np.any(call_mask):
        prices[call_mask] = bs_price(S[call_mask], K[call_mask], T_vals[call_mask], r, sigma[call_mask], 'call')
        
    # Puts
    put_mask = (types == 'put') & valid_mask
    if np.any(put_mask):
        prices[put_mask] = bs_price(S[put_mask], K[put_mask], T_vals[put_mask], r, sigma[put_mask], 'put')
        
    # Add back to DF
    df = df.with_columns(pl.Series(name="theoretical_price", values=prices))
    
    # Compare
    df = df.with_columns(
        ((pl.col("bid_price") + pl.col("ask_price")) / 2).alias("mid_price")
    )
    
    df = df.with_columns(
        pl.when((pl.col("mid_price") < pl.col("theoretical_price") * 0.9) & (pl.col("mid_price") > 0))
        .then(pl.lit("UNDERPRICED"))
        .when((pl.col("mid_price") > pl.col("theoretical_price") * 1.1) & (pl.col("mid_price") > 0))
        .then(pl.lit("OVERPRICED"))
        .otherwise(pl.lit(None))
        .alias("mispricing_signal")
    )
    
    return df
