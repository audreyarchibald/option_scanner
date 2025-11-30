import polars as pl
from config import MIN_VOLUME

def scan_uoa(df: pl.DataFrame) -> pl.DataFrame:
    """
    Scan for Unusual Options Activity.
    """
    # Volume > Open Interest
    # And meaningful volume
    
    uoa = df.filter(
        (pl.col("volume") > pl.col("open_interest")) & 
        (pl.col("volume") > MIN_VOLUME)
    ).with_columns(
        pl.lit("UOA_HIGH_VOL").alias("signal")
    )
    
    return uoa
