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
import markdown
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import numpy as np
from tabulate import tabulate

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
    
    parser.add_argument(
        "--pdf", 
        action="store_true",
        help="Generate a PDF report"
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
            'Volume Put/Call Ratio',
            'Average IV',
            'Min IV',
            'Max IV'
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
            f"{btc_summary['volume_put_call_ratio'].iloc[0]:.2f}",
            f"{btc_summary['average_iv'].iloc[0]:.2%}" if 'average_iv' in btc_summary.columns and not pd.isna(btc_summary['average_iv'].iloc[0]) else "N/A",
            f"{btc_summary['min_iv'].iloc[0]:.2%}" if 'min_iv' in btc_summary.columns and not pd.isna(btc_summary['min_iv'].iloc[0]) else "N/A",
            f"{btc_summary['max_iv'].iloc[0]:.2%}" if 'max_iv' in btc_summary.columns and not pd.isna(btc_summary['max_iv'].iloc[0]) else "N/A"
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
            f"{eth_summary['volume_put_call_ratio'].iloc[0]:.2f}",
            f"{eth_summary['average_iv'].iloc[0]:.2%}" if 'average_iv' in eth_summary.columns and not pd.isna(eth_summary['average_iv'].iloc[0]) else "N/A",
            f"{eth_summary['min_iv'].iloc[0]:.2%}" if 'min_iv' in eth_summary.columns and not pd.isna(eth_summary['min_iv'].iloc[0]) else "N/A",
            f"{eth_summary['max_iv'].iloc[0]:.2%}" if 'max_iv' in eth_summary.columns and not pd.isna(eth_summary['max_iv'].iloc[0]) else "N/A"
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
    
    # Plot key ratios comparison
    btc_summary = btc_data.get('summary')
    eth_summary = eth_data.get('summary')
    
    if btc_summary is not None and eth_summary is not None:
        # Check if implied volatility data is available
        has_iv_data = ('average_iv' in btc_summary.columns and 'average_iv' in eth_summary.columns and
                      not pd.isna(btc_summary['average_iv'].iloc[0]) and not pd.isna(eth_summary['average_iv'].iloc[0]))
        
        if has_iv_data:
            # Create implied volatility comparison plot
            plt.figure(figsize=(10, 6))
            
            # Extract IV data
            btc_avg_iv = btc_summary['average_iv'].iloc[0]
            btc_min_iv = btc_summary['min_iv'].iloc[0]
            btc_max_iv = btc_summary['max_iv'].iloc[0]
            
            eth_avg_iv = eth_summary['average_iv'].iloc[0]
            eth_min_iv = eth_summary['min_iv'].iloc[0]
            eth_max_iv = eth_summary['max_iv'].iloc[0]
            
            # Create bar chart
            labels = ['Average IV', 'Min IV', 'Max IV']
            btc_values = [btc_avg_iv, btc_min_iv, btc_max_iv]
            eth_values = [eth_avg_iv, eth_min_iv, eth_max_iv]
            
            x = np.arange(len(labels))
            width = 0.35
            
            fig, ax = plt.subplots(figsize=(12, 7))
            rects1 = ax.bar(x - width/2, btc_values, width, label='BTC', color='orange', alpha=0.7)
            rects2 = ax.bar(x + width/2, eth_values, width, label='ETH', color='blue', alpha=0.7)
            
            # Add labels and formatting
            ax.set_ylabel('Implied Volatility')
            ax.set_title('Implied Volatility Comparison: BTC vs ETH')
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.legend()
            
            # Format y-axis as percentage
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1%}'))
            
            # Add value labels on bars
            def autolabel(rects):
                for rect in rects:
                    height = rect.get_height()
                    ax.annotate(f'{height:.1%}',
                                xy=(rect.get_x() + rect.get_width()/2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom')
            
            autolabel(rects1)
            autolabel(rects2)
            
            plt.tight_layout()
            
            # Save the plot
            iv_plot_file = os.path.join(output_dir, f"iv_comparison_{timestamp}.png")
            plt.savefig(iv_plot_file)
            plt.close()
            
            plot_files['iv_comparison'] = iv_plot_file
            print(f"Saved implied volatility comparison plot to {iv_plot_file}")
    
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

def generate_markdown_report(data, plot_files, output_dir):
    """Generate a markdown report with the consolidated analysis."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = os.path.join(output_dir, f'consolidated_report_{timestamp}.md')
    
    with open(report_file, 'w') as f:
        # Title
        f.write(f"# Consolidated Crypto Options Summary - {datetime.now().strftime('%Y-%m-%d')}\n\n")
        
        # Overview
        f.write("## Overview\n\n")
        f.write("This report provides a consolidated view of options data for Bitcoin (BTC) and Ethereum (ETH).\n\n")
        
        # Summary Statistics
        f.write("## Summary Statistics\n\n")
        stats_table = tabulate(data['consolidated'], headers='keys', tablefmt='pipe', floatfmt='.2f')
        f.write(f"{stats_table}\n\n")
        
        # Implied Volatility Analysis
        f.write("## Implied Volatility Analysis\n\n")
        f.write("Implied volatility (IV) represents the market's expectation of future price movement and volatility. ")
        f.write("Higher IV indicates greater expected price movement and typically higher option premiums.\n\n")
        
        # Extract IV metrics from consolidated data
        btc_avg_iv = next((row['BTC'] for _, row in data['consolidated'].iterrows() if row['Metric'] == 'Average IV'), 'N/A')
        eth_avg_iv = next((row['ETH'] for _, row in data['consolidated'].iterrows() if row['Metric'] == 'Average IV'), 'N/A')
        
        f.write(f"- **BTC Average IV**: {btc_avg_iv}\n")
        f.write(f"- **ETH Average IV**: {eth_avg_iv}\n\n")
        
        f.write("The IV spread between different strikes indicates market sentiment about potential price directions. ")
        f.write("A higher IV for out-of-the-money puts compared to calls suggests a bearish skew, while the opposite suggests a bullish skew.\n\n")

        # New Section: Volatility Skew Analytics
        f.write("### Volatility Skew Analytics\n\n")
        
        # BTC Skew Analysis
        f.write("#### Bitcoin (BTC) Skew Analysis\n\n")
        btc_skew = calculate_skew_metrics('BTC', output_dir)
        f.write("**Put/Call Skew Metrics:**\n")
        f.write(f"- 25-Delta Put/Call Skew: {btc_skew['25d_skew']:.2f}%\n")
        f.write(f"- 10-Delta Put/Call Skew: {btc_skew['10d_skew']:.2f}%\n")
        f.write(f"- ATM Volatility: {btc_skew['atm_vol']:.2f}%\n")
        f.write(f"- Term Structure Slope: {btc_skew['term_slope']:.2f}%\n\n")
        
        # ETH Skew Analysis
        f.write("#### Ethereum (ETH) Skew Analysis\n\n")
        eth_skew = calculate_skew_metrics('ETH', output_dir)
        f.write("**Put/Call Skew Metrics:**\n")
        f.write(f"- 25-Delta Put/Call Skew: {eth_skew['25d_skew']:.2f}%\n")
        f.write(f"- 10-Delta Put/Call Skew: {eth_skew['10d_skew']:.2f}%\n")
        f.write(f"- ATM Volatility: {eth_skew['atm_vol']:.2f}%\n")
        f.write(f"- Term Structure Slope: {eth_skew['term_slope']:.2f}%\n\n")
        
        # Volatility Surface Analysis
        f.write("### Volatility Surface Analysis\n\n")
        f.write("The volatility surface provides a comprehensive view of implied volatility across different strikes and expiration dates. ")
        f.write("This visualization helps identify potential trading opportunities and market inefficiencies.\n\n")
        
        # BTC Volatility Surface
        f.write("#### Bitcoin (BTC) Volatility Surface\n\n")
        btc_surface_file = None
        for key, path in plot_files.items():
            if 'BTC_volatility_surface' in path:
                btc_surface_file = os.path.basename(path)
                break
        if btc_surface_file:
            f.write(f"![BTC Volatility Surface]({btc_surface_file})\n\n")
        
        # ETH Volatility Surface
        f.write("#### Ethereum (ETH) Volatility Surface\n\n")
        eth_surface_file = None
        for key, path in plot_files.items():
            if 'ETH_volatility_surface' in path:
                eth_surface_file = os.path.basename(path)
                break
        if eth_surface_file:
            f.write(f"![ETH Volatility Surface]({eth_surface_file})\n\n")
        
        # Implied Volatility Comparison
        f.write("### Implied Volatility Comparison\n\n")
        iv_comparison_file = None
        for key, path in plot_files.items():
            if 'iv_comparison' in path:
                iv_comparison_file = os.path.basename(path)
                break
        if iv_comparison_file:
            f.write(f"![Implied Volatility Comparison]({iv_comparison_file})\n\n")
        
        # Volatility Hotspots Summary
        f.write("### Volatility Skew Hotspots\n\n")
        f.write("#### BTC Volatility Hotspots\n")
        btc_hotspots = analyze_volatility_hotspots('BTC', output_dir)
        f.write(f"- Total hotspots identified: {btc_hotspots['total']}\n")
        f.write(f"- Maximum deviation: {btc_hotspots['max_dev']:.2f}%\n")
        f.write(f"- Average deviation: {btc_hotspots['avg_dev']:.2f}%\n")
        f.write(f"- Call-side hotspots: {btc_hotspots['calls']}\n")
        f.write(f"- Put-side hotspots: {btc_hotspots['puts']}\n")
        f.write(f"- Most active strikes: {', '.join(f'${x:,}' for x in btc_hotspots['active_strikes'])}\n\n")
        
        f.write("#### ETH Volatility Hotspots\n")
        eth_hotspots = analyze_volatility_hotspots('ETH', output_dir)
        f.write(f"- Total hotspots identified: {eth_hotspots['total']}\n")
        f.write(f"- Maximum deviation: {eth_hotspots['max_dev']:.2f}%\n")
        f.write(f"- Average deviation: {eth_hotspots['avg_dev']:.2f}%\n")
        f.write(f"- Call-side hotspots: {eth_hotspots['calls']}\n")
        f.write(f"- Put-side hotspots: {eth_hotspots['puts']}\n")
        f.write(f"- Most active strikes: {', '.join(f'${x:,}' for x in eth_hotspots['active_strikes'])}\n\n")

        # Comparison Charts
        f.write("## Comparison Charts\n\n")
        f.write("### BTC vs ETH: Key Ratios Comparison\n\n")
        ratios_comparison_file = None
        for key, path in plot_files.items():
            if 'ratios_comparison' in path:
                ratios_comparison_file = os.path.basename(path)
                break
        if ratios_comparison_file:
            f.write(f"![BTC vs ETH Ratios]({ratios_comparison_file})\n\n")
        
        f.write("### Put/Call Ratio by Expiration Date\n\n")
        pc_comparison_file = None
        for key, path in plot_files.items():
            if 'put_call_comparison' in path:
                pc_comparison_file = os.path.basename(path)
                break
        if pc_comparison_file:
            f.write(f"![Put/Call Ratio by Expiration]({pc_comparison_file})\n\n")
        
        # High Volume Strikes
        f.write("\n## High Volume Strikes\n\n")
        f.write("### BTC High Volume Strikes\n\n")
        btc_volume_table = tabulate(data['high_volume'][data['high_volume']['currency'] == 'BTC'].head(), 
                                  headers='keys', tablefmt='pipe', floatfmt='.2f')
        f.write(f"{btc_volume_table}\n\n")
        
        f.write("### ETH High Volume Strikes\n\n")
        eth_volume_table = tabulate(data['high_volume'][data['high_volume']['currency'] == 'ETH'].head(), 
                                  headers='keys', tablefmt='pipe', floatfmt='.2f')
        f.write(f"{eth_volume_table}\n\n")
        
        # Put/Call Ratio by Expiration
        f.write("## Put/Call Ratio by Expiration\n\n")
        f.write("### BTC Put/Call Ratio by Expiration\n\n")
        btc_pc_table = tabulate(data['put_call'][data['put_call']['currency'] == 'BTC'], 
                              headers='keys', tablefmt='pipe', floatfmt='.2f')
        f.write(f"{btc_pc_table}\n\n")
        
        f.write("### ETH Put/Call Ratio by Expiration\n\n")
        eth_pc_table = tabulate(data['put_call'][data['put_call']['currency'] == 'ETH'], 
                              headers='keys', tablefmt='pipe', floatfmt='.2f')
        f.write(f"{eth_pc_table}\n\n")
        
        # Footer
        f.write("\n---\n\n")
        f.write(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"Saved markdown report to {report_file}")
    return report_file

def calculate_skew_metrics(currency, output_dir):
    """Calculate volatility skew metrics for a given currency."""
    # Read volatility data
    timestamp = get_latest_timestamp(output_dir, currency)
    vol_file = os.path.join(output_dir, f'{currency}_volatility_hotspots_{timestamp}.csv')
    
    if not os.path.exists(vol_file):
        return {
            '25d_skew': 0.0,
            '10d_skew': 0.0,
            'atm_vol': 0.0,
            'term_slope': 0.0
        }
    
    df = pd.read_csv(vol_file)
    
    # Calculate ATM volatility (using closest to current price)
    current_price = get_current_price(currency, output_dir)
    atm_options = df[abs(df['strike'] - current_price) < current_price * 0.05]
    atm_vol = atm_options['implied_volatility'].mean() if not atm_options.empty else 0.0
    
    # Calculate 25-delta skew (approximately 25% OTM puts vs calls)
    otm_25d_puts = df[(df['option_type'] == 'put') & 
                      (df['strike'] <= current_price * 0.75)]['implied_volatility'].mean()
    otm_25d_calls = df[(df['option_type'] == 'call') & 
                       (df['strike'] >= current_price * 1.25)]['implied_volatility'].mean()
    skew_25d = otm_25d_puts - otm_25d_calls if not (np.isnan(otm_25d_puts) or np.isnan(otm_25d_calls)) else 0.0
    
    # Calculate 10-delta skew (approximately 10% OTM puts vs calls)
    otm_10d_puts = df[(df['option_type'] == 'put') & 
                      (df['strike'] <= current_price * 0.90)]['implied_volatility'].mean()
    otm_10d_calls = df[(df['option_type'] == 'call') & 
                       (df['strike'] >= current_price * 1.10)]['implied_volatility'].mean()
    skew_10d = otm_10d_puts - otm_10d_calls if not (np.isnan(otm_10d_puts) or np.isnan(otm_10d_calls)) else 0.0
    
    # Calculate term structure slope
    df['days_to_expiry'] = pd.to_numeric(df['days_to_expiration'])
    near_term = df[df['days_to_expiry'] <= 30]['implied_volatility'].mean()
    far_term = df[df['days_to_expiry'] > 180]['implied_volatility'].mean()
    term_slope = (far_term - near_term) / near_term * 100 if not (np.isnan(near_term) or np.isnan(far_term)) else 0.0
    
    return {
        '25d_skew': skew_25d,
        '10d_skew': skew_10d,
        'atm_vol': atm_vol,
        'term_slope': term_slope
    }

def get_current_price(currency, output_dir):
    """Get the current price for a currency from summary stats."""
    timestamp = get_latest_timestamp(output_dir, currency)
    stats_file = os.path.join(output_dir, f'{currency}_summary_stats_{timestamp}.csv')
    
    if os.path.exists(stats_file):
        df = pd.read_csv(stats_file)
        if 'current_price' in df.columns:
            return float(df['current_price'].iloc[0])
    return 0.0

def get_latest_timestamp(output_dir, currency):
    """Get the latest timestamp from files for a given currency."""
    pattern = os.path.join(output_dir, f'{currency}_*')
    files = glob.glob(pattern)
    if not files:
        return None
    
    timestamps = []
    for file in files:
        match = re.search(r'\d{8}_\d{6}', file)
        if match:
            timestamps.append(match.group())
    
    return max(timestamps) if timestamps else None

def analyze_volatility_hotspots(currency, output_dir):
    """Analyze volatility hotspots for a given currency."""
    timestamp = get_latest_timestamp(output_dir, currency)
    hotspots_file = os.path.join(output_dir, f'{currency}_volatility_hotspots_{timestamp}.csv')
    
    if not os.path.exists(hotspots_file):
        return {
            'total': 0,
            'max_dev': 0.0,
            'avg_dev': 0.0,
            'calls': 0,
            'puts': 0,
            'active_strikes': []
        }
    
    df = pd.read_csv(hotspots_file)
    
    # Calculate metrics
    total = len(df)
    max_dev = df['deviation_pct'].abs().max()
    avg_dev = df['deviation_pct'].abs().mean()
    calls = len(df[df['option_type'] == 'call'])
    puts = len(df[df['option_type'] == 'put'])
    
    # Find most active strikes by volume
    active_strikes = df.nlargest(5, 'volume')['strike'].unique().tolist()
    
    return {
        'total': total,
        'max_dev': max_dev,
        'avg_dev': avg_dev,
        'calls': calls,
        'puts': puts,
        'active_strikes': active_strikes
    }

def generate_pdf_report(md_file, plot_files, output_dir):
    """Generate a PDF report from the markdown file."""
    # Get the timestamp from the markdown filename
    timestamp = os.path.basename(md_file).replace("consolidated_report_", "").replace(".md", "")
    
    # Create the PDF filename
    pdf_file = os.path.join(output_dir, f"consolidated_report_{timestamp}.pdf")
    
    # Read the markdown content
    with open(md_file, 'r') as f:
        md_content = f.read()
    
    # Create the PDF document
    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=12
    )
    
    heading1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=10,
        spaceBefore=20
    )
    
    heading2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=15
    )
    
    normal_style = styles['Normal']
    
    # Parse the markdown content
    lines = md_content.split('\n')
    
    # Create a list to hold the PDF elements
    elements = []
    
    # Process the markdown content
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Title (# Heading)
        if line.startswith('# '):
            elements.append(Paragraph(line[2:], title_style))
            elements.append(Spacer(1, 0.2 * inch))
        
        # Heading 1 (## Heading)
        elif line.startswith('## '):
            elements.append(Paragraph(line[3:], heading1_style))
        
        # Heading 2 (### Heading)
        elif line.startswith('### '):
            elements.append(Paragraph(line[4:], heading2_style))
        
        # Table
        elif line.startswith('|'):
            # Find the end of the table
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            i -= 1  # Adjust for the outer loop increment
            
            # Process the table
            if len(table_lines) >= 3:  # Header, separator, and at least one row
                # Parse the table
                table_data = []
                for table_line in table_lines:
                    if '|-' in table_line:  # Skip separator line
                        continue
                    cells = [cell.strip() for cell in table_line.split('|')[1:-1]]
                    table_data.append(cells)
                
                # Create the table
                if table_data:
                    table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))
                    elements.append(table)
                    elements.append(Spacer(1, 0.2 * inch))
        
        # Image
        elif line.startswith('!['):
            try:
                # Extract image path and description
                img_desc = line[2:].split(']')[0]
                img_path = line.split('(')[1].split(')')[0]
                
                # First try to find the image in plot_files
                actual_path = None
                for _, path in plot_files.items():
                    if os.path.basename(path) == img_path:
                        actual_path = path
                        break
                
                # If not found in plot_files, check in output directory
                if not actual_path:
                    potential_path = os.path.join(output_dir, img_path)
                    if os.path.exists(potential_path):
                        actual_path = potential_path
                
                if actual_path and os.path.exists(actual_path):
                    # Add image description
                    elements.append(Paragraph(img_desc, styles['Italic']))
                    elements.append(Spacer(1, 0.1 * inch))
                    
                    # Add image with proper scaling
                    img = Image(actual_path)
                    # Scale image to fit page width while maintaining aspect ratio
                    aspect = img.imageHeight / float(img.imageWidth)
                    img.drawWidth = 6 * inch
                    img.drawHeight = 6 * inch * aspect
                    elements.append(img)
                    elements.append(Spacer(1, 0.3 * inch))
            except Exception as e:
                print(f"Warning: Failed to process image {img_path}: {str(e)}")
        
        # Normal paragraph
        elif line and not line.startswith('---'):
            elements.append(Paragraph(line, normal_style))
            elements.append(Spacer(1, 0.1 * inch))
        
        i += 1
    
    # Add footer
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Italic']))
    
    # Build the PDF
    doc.build(elements)
    
    print(f"Saved PDF report to {pdf_file}")
    return pdf_file

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
    md_file = None
    if args.markdown and summary_data:
        md_file = generate_markdown_report(summary_data, plot_files, output_dir)
    
    # Generate PDF report if requested
    if args.pdf and summary_data:
        if not md_file:
            md_file = generate_markdown_report(summary_data, plot_files, output_dir)
        generate_pdf_report(md_file, plot_files, output_dir)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 