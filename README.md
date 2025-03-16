# Crypto Options Chain Aggregator

A minimal tool that retrieves and summarizes real-time options data for Bitcoin and Ethereum from the Deribit API. The tool provides insights on open interest, implied volatility, and generates daily summaries highlighting the largest changes in calls and puts.

## Features

- Fetch real-time options data from Deribit API
- Track open interest and implied volatility
- Generate daily summaries of options data
- Identify significant changes in calls/puts

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Deribit API credentials (optional):
   ```
   DERIBIT_API_KEY=your_api_key
   DERIBIT_API_SECRET=your_api_secret
   ```

## Usage

Run the main script to fetch and analyze options data:

```
python3 src/main.py
```

## Options

- `--currency`: Specify the cryptocurrency (BTC or ETH, default: BTC)
- `--days`: Number of days to analyze (default: 1)
- `--output`: Output format (console, csv, json, default: console)

## Example Output

The tool will display a summary of options data, including:
- Current open interest for calls and puts
- Implied volatility across different strike prices
- Largest daily changes in open interest
- Volume analysis for different expiration dates 