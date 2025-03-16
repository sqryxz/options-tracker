#!/usr/bin/env python3

import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path
import glob
import argparse
import re
import base64
from io import BytesIO

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate consolidated daily summary for BTC and ETH")
    
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="output",
        help="Directory containing output files and where to save consolidated summary"
    )
    
    parser.add_argument(
        "--date", 
        type=str, 
        default=None,
        help="Date to consolidate (format: YYYYMMDD, default: latest available)"
    )
    
    parser.add_argument(
        "--markdown", 
        action="store_true",
        help="Generate a markdown report"
    )
    
    return parser.parse_args()

def find_latest_files(output_dir, currency, date=None):
    """Find the latest summary files for a given currency."""
    if date:
        pattern = f"{currency}_summary_stats_{date}_*.csv"
    else:
        pattern = f"{currency}_summary_stats_*.csv"
    
    files = glob.glob(os.path.join(output_dir, pattern))
    if not files:
        return None
    
    # Sort by modification time (newest first)
    latest_file = max(files, key=os.path.getmtime)
    
    # Extract the timestamp part from the filename
    filename = os.path.basename(latest_file)
    match = re.search(r'(\d{8}_\d{6})', filename)
    if match:
        timestamp = match.group(1)
        date_part = timestamp.split('_')[0]
        time_part = timestamp.split('_')[1]
        
        # Find other related files with the same timestamp
        high_volume_file = os.path.join(output_dir, f"{currency}_high_volume_strikes_{date_part}_{time_part}.csv")
        put_call_file = os.path.join(output_dir, f"{currency}_put_call_by_expiry_{date_part}_{time_part}.csv")
        
        return {
            'summary': latest_file,
            'high_volume': high_volume_file if os.path.exists(high_volume_file) else None,
            'put_call': put_call_file if os.path.exists(put_call_file) else None,
            'timestamp': timestamp
        }
    else:
        # If we can't extract the timestamp, just return the summary file
        return {
            'summary': latest_file,
            'high_volume': None,
            'put_call': None,
            'timestamp': None
        }

def load_data(file_paths):
    """Load data from CSV files."""
    data = {}
    
    if file_paths['summary'] and os.path.exists(file_paths['summary']):
        data['summary'] = pd.read_csv(file_paths['summary'])
    
    if file_paths['high_volume'] and os.path.exists(file_paths['high_volume']):
        data['high_volume'] = pd.read_csv(file_paths['high_volume'])
    
    if file_paths['put_call'] and os.path.exists(file_paths['put_call']):
        data['put_call'] = pd.read_csv(file_paths['put_call'])
    
    return data

def generate_consolidated_summary(btc_data, eth_data, output_dir):
    """Generate a consolidated summary for BTC and ETH."""
    # Create timestamp for the output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extract summary data
    btc_summary = btc_data.get('summary')
    eth_summary = eth_data.get('summary')
    
    if btc_summary is None or eth_summary is None:
        print("Error: Missing summary data for BTC or ETH")
        return
    
    # Create a consolidated DataFrame
    consolidated = pd.DataFrame({
        'Metric': [
            'Current Price',
            'Total Open Interest',
            'Calls Open Interest',
            'Puts Open Interest',
            'Put/Call Ratio',
            'Total Volume',
            'Calls Volume',
            'Puts Volume',
            'Volume Put/Call Ratio'
        ],
        'BTC': [
            f"${btc_summary['current_price'].iloc[0]:,.2f}",
            f"{btc_summary['total_open_interest'].iloc[0]:,.0f}",
            f"{btc_summary['calls_open_interest'].iloc[0]:,.0f}",
            f"{btc_summary['puts_open_interest'].iloc[0]:,.0f}",
            f"{btc_summary['put_call_ratio'].iloc[0]:.2f}",
            f"{btc_summary['total_volume'].iloc[0]:,.0f}",
            f"{btc_summary['calls_volume'].iloc[0]:,.0f}",
            f"{btc_summary['puts_volume'].iloc[0]:,.0f}",
            f"{btc_summary['volume_put_call_ratio'].iloc[0]:.2f}"
        ],
        'ETH': [
            f"${eth_summary['current_price'].iloc[0]:,.2f}",
            f"{eth_summary['total_open_interest'].iloc[0]:,.0f}",
            f"{eth_summary['calls_open_interest'].iloc[0]:,.0f}",
            f"{eth_summary['puts_open_interest'].iloc[0]:,.0f}",
            f"{eth_summary['put_call_ratio'].iloc[0]:.2f}",
            f"{eth_summary['total_volume'].iloc[0]:,.0f}",
            f"{eth_summary['calls_volume'].iloc[0]:,.0f}",
            f"{eth_summary['puts_volume'].iloc[0]:,.0f}",
            f"{eth_summary['volume_put_call_ratio'].iloc[0]:.2f}"
        ]
    })
    
    # Save consolidated summary to CSV
    output_file = os.path.join(output_dir, f"consolidated_summary_{timestamp}.csv")
    consolidated.to_csv(output_file, index=False)
    print(f"Saved consolidated summary to {output_file}")
    
    # Create a consolidated high volume strikes table
    combined_high_volume = None
    if 'high_volume' in btc_data and 'high_volume' in eth_data:
        btc_high_volume = btc_data['high_volume'].copy()
        eth_high_volume = eth_data['high_volume'].copy()
        
        # Add currency column
        btc_high_volume['currency'] = 'BTC'
        eth_high_volume['currency'] = 'ETH'
        
        # Combine data
        combined_high_volume = pd.concat([btc_high_volume, eth_high_volume])
        
        # Save to CSV
        high_volume_file = os.path.join(output_dir, f"consolidated_high_volume_{timestamp}.csv")
        combined_high_volume.to_csv(high_volume_file, index=False)
        print(f"Saved consolidated high volume strikes to {high_volume_file}")
    
    # Create a consolidated put/call ratio by expiry table
    combined_put_call = None
    if 'put_call' in btc_data and 'put_call' in eth_data:
        btc_put_call = btc_data['put_call'].copy()
        eth_put_call = eth_data['put_call'].copy()
        
        # Add currency column
        btc_put_call['currency'] = 'BTC'
        eth_put_call['currency'] = 'ETH'
        
        # Combine data
        combined_put_call = pd.concat([btc_put_call, eth_put_call])
        
        # Save to CSV
        put_call_file = os.path.join(output_dir, f"consolidated_put_call_by_expiry_{timestamp}.csv")
        combined_put_call.to_csv(put_call_file, index=False)
        print(f"Saved consolidated put/call ratio by expiry to {put_call_file}")
    
    return {
        'consolidated': consolidated,
        'high_volume': combined_high_volume,
        'put_call': combined_put_call,
        'timestamp': timestamp
    }

def create_comparison_plots(btc_data, eth_data, output_dir):
    """Create comparison plots for BTC and ETH."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_files = {}
    
    # Plot put/call ratios
    if 'put_call' in btc_data and 'put_call' in eth_data:
        plt.figure(figsize=(12, 8))
        
        # Filter to common expiration dates if needed
        btc_put_call = btc_data['put_call'].copy()
        eth_put_call = eth_data['put_call'].copy()
        
        # Plot
        plt.figure(figsize=(14, 8))
        
        # Convert expiration_date to datetime for better x-axis formatting
        btc_put_call['expiration_date'] = pd.to_datetime(btc_put_call['expiration_date'])
        eth_put_call['expiration_date'] = pd.to_datetime(eth_put_call['expiration_date'])
        
        # Sort by date
        btc_put_call = btc_put_call.sort_values('expiration_date')
        eth_put_call = eth_put_call.sort_values('expiration_date')
        
        # Plot
        plt.plot(btc_put_call['expiration_date'], btc_put_call['put_call_ratio'], 'o-', label='BTC')
        plt.plot(eth_put_call['expiration_date'], eth_put_call['put_call_ratio'], 's-', label='ETH')
        
        plt.title('Put/Call Ratio by Expiration Date: BTC vs ETH')
        plt.xlabel('Expiration Date')
        plt.ylabel('Put/Call Ratio')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save plot
        put_call_plot = os.path.join(output_dir, f"btc_eth_put_call_comparison_{timestamp}.png")
        plt.savefig(put_call_plot)
        plt.close()
        print(f"Saved put/call ratio comparison plot to {put_call_plot}")
        plot_files['put_call'] = put_call_plot
    
    # Create a bar chart comparing key metrics
    if 'summary' in btc_data and 'summary' in eth_data:
        btc_summary = btc_data['summary']
        eth_summary = eth_data['summary']
        
        metrics = ['put_call_ratio', 'volume_put_call_ratio']
        labels = ['Open Interest Put/Call Ratio', 'Volume Put/Call Ratio']
        
        plt.figure(figsize=(10, 6))
        
        x = range(len(metrics))
        width = 0.35
        
        plt.bar([i - width/2 for i in x], 
                [btc_summary[metric].iloc[0] for metric in metrics], 
                width, 
                label='BTC')
        
        plt.bar([i + width/2 for i in x], 
                [eth_summary[metric].iloc[0] for metric in metrics], 
                width, 
                label='ETH')
        
        plt.xlabel('Metric')
        plt.ylabel('Ratio')
        plt.title('BTC vs ETH: Key Ratios Comparison')
        plt.xticks(x, labels)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save plot
        ratios_plot = os.path.join(output_dir, f"btc_eth_ratios_comparison_{timestamp}.png")
        plt.savefig(ratios_plot)
        plt.close()
        print(f"Saved ratios comparison plot to {ratios_plot}")
        plot_files['ratios'] = ratios_plot
    
    return plot_files

def print_consolidated_summary(consolidated):
    """Print the consolidated summary to the console."""
    print("\n" + "="*80)
    print(f"CONSOLIDATED CRYPTO OPTIONS SUMMARY - {datetime.now().strftime('%Y-%m-%d')}")
    print("="*80 + "\n")
    
    # Print the table
    print(consolidated.to_string(index=False))
    
    print("\n" + "="*80)

def generate_markdown_report(summary_data, plot_files, output_dir):
    """Generate a comprehensive markdown report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_date = datetime.now().strftime("%Y-%m-%d")
    
    consolidated = summary_data['consolidated']
    high_volume = summary_data.get('high_volume')
    put_call = summary_data.get('put_call')
    
    # Start building the markdown content
    md_content = f"""# Consolidated Crypto Options Summary - {report_date}

## Overview

This report provides a consolidated view of options data for Bitcoin (BTC) and Ethereum (ETH).

## Summary Statistics

| Metric | BTC | ETH |
|--------|-----|-----|
"""
    
    # Add each row from the consolidated DataFrame
    for _, row in consolidated.iterrows():
        md_content += f"| {row['Metric']} | {row['BTC']} | {row['ETH']} |\n"
    
    # Add plots
    md_content += "\n## Comparison Charts\n\n"
    
    if 'ratios' in plot_files:
        md_content += f"### BTC vs ETH: Key Ratios Comparison\n\n"
        md_content += f"![BTC vs ETH Ratios]({os.path.basename(plot_files['ratios'])})\n\n"
    
    if 'put_call' in plot_files:
        md_content += f"### Put/Call Ratio by Expiration Date\n\n"
        md_content += f"![Put/Call Ratio by Expiration]({os.path.basename(plot_files['put_call'])})\n\n"
    
    # Add high volume strikes if available
    if high_volume is not None:
        md_content += "\n## High Volume Strikes\n\n"
        md_content += "### BTC High Volume Strikes\n\n"
        
        btc_high_volume = high_volume[high_volume['currency'] == 'BTC'].sort_values('volume', ascending=False).head(5)
        md_content += "| Strike | Volume | Distance from Current Price |\n"
        md_content += "|--------|--------|----------------------------|\n"
        
        for _, row in btc_high_volume.iterrows():
            md_content += f"| ${row['strike']:,.0f} | {row['volume']:,.0f} | {row['distance_pct']:.2f}% |\n"
        
        md_content += "\n### ETH High Volume Strikes\n\n"
        
        eth_high_volume = high_volume[high_volume['currency'] == 'ETH'].sort_values('volume', ascending=False).head(5)
        md_content += "| Strike | Volume | Distance from Current Price |\n"
        md_content += "|--------|--------|----------------------------|\n"
        
        for _, row in eth_high_volume.iterrows():
            md_content += f"| ${row['strike']:,.0f} | {row['volume']:,.0f} | {row['distance_pct']:.2f}% |\n"
    
    # Add put/call ratio by expiry if available
    if put_call is not None:
        md_content += "\n## Put/Call Ratio by Expiration\n\n"
        
        # Convert to datetime for sorting
        put_call['expiration_date'] = pd.to_datetime(put_call['expiration_date'])
        
        # Group by currency and sort by date
        btc_put_call = put_call[put_call['currency'] == 'BTC'].sort_values('expiration_date')
        eth_put_call = put_call[put_call['currency'] == 'ETH'].sort_values('expiration_date')
        
        md_content += "### BTC Put/Call Ratio by Expiration\n\n"
        md_content += "| Expiration Date | Put/Call Ratio |\n"
        md_content += "|-----------------|----------------|\n"
        
        for _, row in btc_put_call.iterrows():
            md_content += f"| {row['expiration_date'].strftime('%Y-%m-%d')} | {row['put_call_ratio']:.2f} |\n"
        
        md_content += "\n### ETH Put/Call Ratio by Expiration\n\n"
        md_content += "| Expiration Date | Put/Call Ratio |\n"
        md_content += "|-----------------|----------------|\n"
        
        for _, row in eth_put_call.iterrows():
            md_content += f"| {row['expiration_date'].strftime('%Y-%m-%d')} | {row['put_call_ratio']:.2f} |\n"
    
    # Add footer
    md_content += f"\n\n---\n\nReport generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    # Write the markdown file
    md_file = os.path.join(output_dir, f"consolidated_report_{timestamp}.md")
    with open(md_file, "w") as f:
        f.write(md_content)
    
    print(f"Saved markdown report to {md_file}")
    return md_file

def main():
    """Main function to generate consolidated summary."""
    args = parse_arguments()
    output_dir = args.output_dir
    date = args.date
    
    # Find the latest files for BTC and ETH
    btc_files = find_latest_files(output_dir, "BTC", date)
    eth_files = find_latest_files(output_dir, "ETH", date)
    
    if not btc_files or not eth_files:
        print("Error: Could not find summary files for both BTC and ETH")
        return 1
    
    # Load data
    btc_data = load_data(btc_files)
    eth_data = load_data(eth_files)
    
    # Generate consolidated summary
    summary_data = generate_consolidated_summary(btc_data, eth_data, output_dir)
    
    # Create comparison plots
    plot_files = create_comparison_plots(btc_data, eth_data, output_dir)
    
    # Print consolidated summary
    if summary_data and 'consolidated' in summary_data:
        print_consolidated_summary(summary_data['consolidated'])
    
    # Generate markdown report if requested
    if args.markdown and summary_data:
        generate_markdown_report(summary_data, plot_files, output_dir)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 