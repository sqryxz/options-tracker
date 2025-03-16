#!/usr/bin/env python3

import os
import sys
import subprocess
from datetime import datetime
import argparse

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run daily options data collection and consolidated summary")
    
    parser.add_argument(
        "--no-pdf", 
        action="store_true",
        help="Skip PDF report generation"
    )
    
    return parser.parse_args()

def main():
    """Run the daily options data collection and consolidated summary."""
    args = parse_arguments()
    
    print("="*80)
    print(f"DAILY CRYPTO OPTIONS SUMMARY - {datetime.now().strftime('%Y-%m-%d')}")
    print("="*80)
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Run the main script for BTC
    print("\nStep 1: Collecting BTC options data...")
    btc_cmd = ["python3", "src/main.py", "--currency", "BTC", "--output", "csv", "--plot"]
    btc_result = subprocess.run(btc_cmd, capture_output=True, text=True)
    
    if btc_result.returncode != 0:
        print("Error collecting BTC data:")
        print(btc_result.stderr)
        return 1
    
    print(btc_result.stdout)
    
    # Step 2: Run the main script for ETH
    print("\nStep 2: Collecting ETH options data...")
    eth_cmd = ["python3", "src/main.py", "--currency", "ETH", "--output", "csv", "--plot"]
    eth_result = subprocess.run(eth_cmd, capture_output=True, text=True)
    
    if eth_result.returncode != 0:
        print("Error collecting ETH data:")
        print(eth_result.stderr)
        return 1
    
    print(eth_result.stdout)
    
    # Step 3: Generate consolidated summary
    print("\nStep 3: Generating consolidated summary...")
    summary_cmd = ["python3", "src/consolidated_summary.py", "--markdown"]
    
    # Add PDF option if not disabled
    if not args.no_pdf:
        summary_cmd.append("--pdf")
    
    summary_result = subprocess.run(summary_cmd, capture_output=True, text=True)
    
    if summary_result.returncode != 0:
        print("Error generating consolidated summary:")
        print(summary_result.stderr)
        return 1
    
    print(summary_result.stdout)
    
    print("\n" + "="*80)
    print("Daily summary completed successfully!")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 