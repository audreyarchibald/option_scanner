import polars as pl

def scan_delta(df: pl.DataFrame) -> pl.DataFrame:
    """
    Categorize options by delta buckets.
    """
    # Absolute delta for categorization (handling puts)
    df = df.with_columns(pl.col("delta").abs().alias("abs_delta"))
    
    # Define buckets
    # We return the whole dataframe with an extra column for filtering later
    # or we can just return specific interesting ones.
    
    # Let's just mark them.
    
    def get_bucket(delta):
        if delta >= 0.70: return "DEEP_ITM"
        elif delta >= 0.45: return "DIRECTIONAL"
        elif delta >= 0.25: return "SENSIBLE"
        elif delta >= 0.10: return "LOTTO"
        else: return "OTM_JUNK"

    # Polars optimization using expressions
    return df.with_columns(
        pl.when(pl.col("abs_delta") >= 0.70).then(pl.lit("DEEP_ITM"))
        .when(pl.col("abs_delta") >= 0.45).then(pl.lit("DIRECTIONAL"))
        .when(pl.col("abs_delta") >= 0.25).then(pl.lit("SENSIBLE"))
        .when(pl.col("abs_delta") >= 0.10).then(pl.lit("LOTTO"))
        .otherwise(pl.lit("OTM_JUNK"))
        .alias("delta_bucket")
    )
