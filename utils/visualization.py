import plotly.express as px
import plotly.graph_objects as go
import polars as pl
import os
from config import CHARTS_DIR

def plot_iv_smile(df: pl.DataFrame, ticker: str):
    """
    Plot IV vs Strike for different expiries.
    """
    # Sample a few expiries to avoid clutter
    expiries = df["expiry"].unique().to_list()
    selected_expiries = expiries[:5] # First 5
    
    subset = df.filter(pl.col("expiry").is_in(selected_expiries))
    
    fig = px.line(subset.to_pandas(), x="strike", y="implied_volatility", color="expiry",
                  title=f"{ticker} Implied Volatility Smile",
                  labels={"strike": "Strike Price", "implied_volatility": "IV"})
    
    output_path = os.path.join(CHARTS_DIR, f"{ticker}_iv_smile.html")
    fig.write_html(output_path)
    return output_path

def plot_delta_heatmap(df: pl.DataFrame, ticker: str):
    """
    Heatmap of Delta across Strike and Expiry.
    """
    # Pivot for heatmap
    # We need numeric strikes and categorical expiries
    
    # Using pandas for pivot because polars pivot is strict
    pdf = df.to_pandas()
    
    fig = px.density_heatmap(pdf, x="strike", y="expiry", z="delta",
                             title=f"{ticker} Delta Heatmap",
                             color_continuous_scale="Viridis")
    
    output_path = os.path.join(CHARTS_DIR, f"{ticker}_delta_heatmap.html")
    fig.write_html(output_path)
    return output_path

def plot_volume_oi(df: pl.DataFrame, ticker: str):
    """
    Bar chart of Volume and Open Interest.
    """
    # Aggregate by strike
    agg = df.group_by("strike").agg([
        pl.col("volume").sum(),
        pl.col("open_interest").sum()
    ]).sort("strike")
    
    pdf = agg.to_pandas()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=pdf["strike"], y=pdf["volume"], name="Volume"))
    fig.add_trace(go.Bar(x=pdf["strike"], y=pdf["open_interest"], name="Open Interest"))
    
    fig.update_layout(title=f"{ticker} Volume vs Open Interest by Strike", barmode='group')
    
    output_path = os.path.join(CHARTS_DIR, f"{ticker}_vol_oi.html")
    fig.write_html(output_path)
    return output_path
