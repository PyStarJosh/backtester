# Arcback

Arcback is a backtesting framework (in active development) for evaluating trading indicators and algorithms against historical financial market data. The end goal is to deliver detailed performance reports across stocks, forex, cryptocurrencies, and commodities.

> **Status:** Early-stage. The data ingestion and persistence layer is functional. The backtesting engine, strategy interface, portfolio, risk, and analysis modules are scaffolded but not yet implemented.

---

## Features

### Implemented

- **Multi-source market data ingestion** via the [`Loader`](src/backend/data/loader.py) class
  - **Twelve Data API** — stocks, forex pairs, and cryptocurrencies (time series, EOD and intraday)
  - **Alpha Vantage API** — commodities (WTI, Brent, copper, wheat, aluminum, corn, cotton, sugar, coffee, natural gas)
  - Supported intraday + daily/weekly/monthly intervals (`1min` → `1month`)
  - Lookup of supported symbols per asset type
  - Robust HTTP error handling (connection errors, timeouts, HTTP errors, JSON decode errors, API-level error responses)
- **SQLite persistence layer** via the [`Processor`](src/backend/data/processor.py) class
  - Auto-initialized schema with three tables: `time_series_data`, `commodity_prices`, `last_updated`
  - Composite primary keys to prevent duplicate rows (`INSERT OR IGNORE`)
  - Context manager support for safe connection handling
  - Formatted output as lists of dicts ready for downstream processing
- **Interval-aware caching** via the [`DataManager`](src/backend/data/data_manager.py) coordinator
  - Tracks the date range already cached per `(symbol, interval)` pair in the `last_updated` table
  - Computes the missing date range and only fetches what isn't already in the local DB, minimizing redundant API calls
- **Environment-based API key management** via [`Constants`](src/backend/constants.py) using `python-dotenv`
- **Configured root logger** in [`main.py`](main.py) so submodules inherit a consistent logging format

### Planned / Scaffolded

The following packages exist as empty modules under [`src/backend/`](src/backend/) and are next on the roadmap:

| Module | Purpose |
|---|---|
| [`engine/`](src/backend/engine/) | Core backtest event loop — bar-by-bar simulation over historical data |
| [`strategy/`](src/backend/strategy/) | Strategy/indicator interface that emits signals from market data |
| [`portfolio/`](src/backend/portfolio/) | Position tracking, order execution, cash and equity accounting |
| [`risk/`](src/backend/risk/) | Position sizing, stop-loss / take-profit, exposure limits |
| [`analysis/`](src/backend/analysis/) | Performance metrics (Sharpe, drawdown, win rate, etc.) and report generation |

---

## Project Structure

```
Arcback/
├── main.py                         # Entry point + logging config
├── requirements.txt
├── .env.example                    # Template for required API keys
├── reference_data/                 # Sample API response payloads (gitignored)
└── src/
    └── backend/
        ├── constants.py            # API key loader (uses python-dotenv)
        ├── data/
        │   ├── loader.py           # Twelve Data + Alpha Vantage HTTP client
        │   ├── processor.py        # SQLite schema, inserts, queries
        │   └── data_manager.py     # Coordinates loader + processor with caching
        ├── engine/                 # (planned)
        ├── strategy/               # (planned)
        ├── portfolio/              # (planned)
        ├── risk/                   # (planned)
        └── analysis/               # (planned)
```

---

## Installation

### Prerequisites

- Python 3.12+
- API keys for:
  - [Twelve Data](https://twelvedata.com/) — stocks, forex, crypto
  - [Alpha Vantage](https://www.alphavantage.co/) — commodities

### Setup

```bash
# Clone the repo
git clone https://github.com/<your-username>/Arcback.git
cd Arcback

# Create and activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# then edit .env and fill in your keys
```

### `.env` format

```env
ALPHAVANTAGE_API_KEY=your_API_key_here
TWELVE_DATA_API_KEY=your_API_key_here
```

---

## Usage

> A CLI / runner is not yet wired up — the data layer is currently exercised programmatically.

### Fetching and caching time series data

```python
from src.backend.data.data_manager import DataManager

with DataManager() as dm:
    # Stocks, forex, or crypto via Twelve Data
    aapl = dm.get_formatted_time_series_data(
        symbol="AAPL",
        interval="1day",
        start_date="2024-01-01",
        end_date="2024-12-31",
    )
    for row in aapl[:5]:
        print(row)
```

The first call hits the API and populates the SQLite DB. Subsequent calls covering the same range are served entirely from the local cache; calls extending the range only fetch the missing window.

### Fetching commodities data

```python
from src.backend.data.data_manager import DataManager

with DataManager() as dm:
    wti = dm.get_formatted_commodities_data(commodity_type="WTI", interval="daily")
    print(wti[:5])
```

### Output shape

**Time series row:**
```python
{
    "symbol": "AAPL",
    "interval": "1day",
    "datetime": "2024-12-31",
    "open": 252.10,
    "high": 253.28,
    "low": 249.43,
    "close": 250.42,
    "volume": 39480718,
}
```

**Commodity row:**
```python
{
    "interval": "daily",
    "commodity_type": "WTI",
    "date": "2024-12-31",
    "price": 71.72,
}
```

---

## Supported Assets & Intervals

### Twelve Data (stocks / forex / crypto)
Intervals: `1min`, `5min`, `15min`, `30min`, `45min`, `1h`, `2h`, `4h`, `8h`, `1day`, `1week`, `1month`

### Alpha Vantage (commodities)

| Commodity | Supported Intervals |
|---|---|
| WTI, Brent, Natural Gas | `daily`, `weekly`, `monthly` |
| Copper, Wheat, Aluminum, Corn, Cotton, Sugar, Coffee | `monthly`, `quarterly`, `annual` |

---

## Data Storage

A SQLite database (`financial_data.db`) is created next to [`processor.py`](src/backend/data/processor.py) on first run.

| Table | Columns | Primary Key |
|---|---|---|
| `time_series_data` | symbol, interval, datetime, open, high, low, close, volume | (symbol, datetime, interval) |
| `commodity_prices` | interval, commodity_type, date, price | (commodity_type, interval, date) |
| `last_updated` | symbol, interval, start_date, last_date | (symbol, interval) |

The DB file is gitignored.

---

## Tech Stack

- **Language:** Python 3.12+
- **HTTP:** `requests`
- **Storage:** `sqlite3` (stdlib)
- **Config:** `python-dotenv`
- **Numerics / data (declared, not yet wired up):** `numpy`, `pandas`
- **Plotting (planned for analysis module):** `matplotlib`
- **Tooling:** `black` for formatting

---

## Roadmap

- [x] Twelve Data integration (stocks / forex / crypto)
- [x] Alpha Vantage integration (commodities)
- [x] SQLite persistence with composite primary keys
- [x] Interval-aware caching to skip redundant API calls
- [ ] Strategy / indicator interface
- [ ] Event-driven backtest engine
- [ ] Portfolio and order management
- [ ] Risk management (sizing, stops, exposure)
- [ ] Performance analysis and report generation
- [ ] CLI / configuration-driven runs
- [ ] Unit + integration tests

---

## License

[MIT](LICENSE) © 2026 Joshua J.