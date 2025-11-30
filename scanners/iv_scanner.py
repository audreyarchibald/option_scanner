import polars as pl
from config import IV_LOW_THRESHOLD, IV_HIGH_THRESHOLD

def scan_iv(df: pl.DataFrame) -> pl.DataFrame:
    """
    Scan for high and low IV opportunities.
    df: Polars DataFrame containing option chain data.
    """
    # Filter for liquid options first
    df = df.filter(pl.col("volume") > 0)
    
    # Low IV -> Buy Candidates
    low_iv = df.filter(pl.col("implied_volatility") < IV_LOW_THRESHOLD).with_columns(
        pl.lit("BUY_VOL").alias("signal")
    )
    
    # High IV -> Sell Candidates
    high_iv = df.filter(pl.col("implied_volatility") > IV_HIGH_THRESHOLD).with_columns(
        pl.lit("SELL_VOL").alias("signal")
    )
    
    return pl.concat([low_iv, high_iv])
