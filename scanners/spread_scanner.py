import polars as pl

def scan_spreads(df: pl.DataFrame) -> pl.DataFrame:
    """
    Scan for tight spreads and high liquidity.
    """
    # Calculate Spread
    df = df.with_columns([
        (pl.col("ask_price") - pl.col("bid_price")).alias("spread"),
        ((pl.col("ask_price") - pl.col("bid_price")) / pl.col("ask_price")).alias("spread_pct")
    ])
    
    # Calculate Liquidity Score
    # Simple score: Volume * OI / Spread (just a heuristic)
    # Or just normalize spread.
    
    # Avoid div by zero
    df = df.with_columns(
        (pl.col("volume") * pl.col("open_interest") / (pl.col("spread") + 0.01)).alias("liquidity_score")
    )
    
    # Filter for High Quality Spreads
    # Spread < 0.10 or Spread % < 5%
    quality = df.filter(
        (pl.col("spread") < 0.10) | (pl.col("spread_pct") < 0.05)
    ).with_columns(
        pl.lit("HIGH_QUALITY").alias("spread_signal")
    )
    
    return quality
