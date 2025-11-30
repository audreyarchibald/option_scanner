# Option Scanner

A production-ready Python tool for scanning US equity options (NASDAQ + S&P500) for opportunities, Greeks calculation, and visualization.

## Features

- **Real-time Data**: Fetches option chains using Polygon.io (extensible to other providers).
- **Greeks Calculation**: Implements Black-Scholes for Delta, Gamma, Theta, Vega, Rho.
- **Scanners**:
    - **IV Scanner**: Detects Low/High IV opportunities.
    - **UOA Scanner**: Flags Unusual Options Activity (Vol > OI).
    - **Delta Buckets**: Categorizes options by risk profile (Lotto, Sensible, Directional, Deep ITM).
    - **Mispricing**: Compares Theoretical Price (Black-Scholes) vs Market Price.
    - **Spread Quality**: Identifies liquid options with tight spreads.
- **Visualizations**: Generates interactive HTML charts for IV Smile, Delta Heatmap, and Volume/OI.
- **Performance**: Built with `aiohttp` for async requests and `polars` for fast data processing.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/option_scanner.git
   cd option_scanner
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API Key**:
   - Create a `.env` file in the root directory:
     ```bash
     touch .env
     ```
   - Add your Polygon.io API key:
     ```env
     POLYGON_API_KEY=your_polygon_api_key_here
     DATA_PROVIDER=polygon
     ```

## Usage

Run the scanner with a list of tickers:

```bash
python main.py SPY QQQ AAPL TSLA
```

### Output

- **Reports**: CSV files with flagged signals in `outputs/reports/`.
- **Charts**: Interactive HTML charts in `outputs/charts/`.
    - `[TICKER]_iv_smile.html`
    - `[TICKER]_delta_heatmap.html`
    - `[TICKER]_vol_oi.html`

## Configuration

Edit `config.py` to adjust:
- `RISK_FREE_RATE`
- `MIN_VOLUME`, `MIN_OI` thresholds
- `IV_LOW_THRESHOLD`, `IV_HIGH_THRESHOLD`

## Project Structure

```
option_scanner/
├── main.py                 # Entry point
├── config.py               # Configuration
├── requirements.txt        # Dependencies
├── data/                   # Data Providers
│   ├── provider_base.py
│   └── polygon_provider.py
├── models/                 # Math & Pricing Models
│   └── black_scholes.py
├── scanners/               # Scanning Logic
│   ├── iv_scanner.py
│   ├── uoa_scanner.py
│   ├── delta_scanner.py
│   ├── mispricing_scanner.py
│   └── spread_scanner.py
├── utils/                  # Utilities
│   ├── logger.py
│   ├── math_utils.py
│   └── visualization.py
└── outputs/                # Generated Results
```

## Performance Notes

- Uses `aiohttp` for concurrent API requests.
- Uses `polars` for efficient vectorized data manipulation (faster than pandas).
- Uses `numpy` for heavy mathematical calculations (Black-Scholes).

## Extension

To add a new data provider (e.g., Tradier), implement the `DataProvider` class in `data/provider_base.py` and update `main.py` to use it.
