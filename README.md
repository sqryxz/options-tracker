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

## GitHub Actions Automation

This repository includes a GitHub Actions workflow that automatically runs the options tracker daily and commits the results to the repository.

### Setting up GitHub Actions

1. Fork or clone this repository to your GitHub account
2. Go to your repository settings
3. Navigate to "Secrets and variables" > "Actions"
4. Add the following secrets:
   - `DERIBIT_API_KEY`: Your Deribit API key
   - `DERIBIT_API_SECRET`: Your Deribit API secret
5. The workflow will run automatically every day at 00:00 UTC
6. You can also manually trigger the workflow from the "Actions" tab

The workflow will:
1. Run the options tracker for both BTC and ETH
2. Generate CSV files and plots
3. Commit and push the results to the repository

## Example Output

The tool will display a summary of options data, including:
- Current open interest for calls and puts
- Implied volatility across different strike prices
- Largest daily changes in open interest
- Volume analysis for different expiration dates 