#!/usr/bin/env python3

import os
import sys
import json
import argparse
from datetime import datetime
import pandas as pd
from pathlib import Path

from deribit_client import DeribitClient
from options_analyzer import OptionsAnalyzer


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Crypto Options Chain Aggregator")
    
    parser.add_argument(
        "--currency", 
        type=str, 
        default="BTC", 
        choices=["BTC", "ETH"],
        help="Cryptocurrency to analyze (BTC or ETH)"
    )
    
    parser.add_argument(
        "--output", 
        type=str, 
        default="console", 
        choices=["console", "csv", "json"],
        help="Output format (console, csv, or json)"
    )
    
    parser.add_argument(
        "--plot", 
        action="store_true",
        help="Generate and save plots"
    )
    
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="output",
        help="Directory to save output files"
    )
    
    return parser.parse_args()


def ensure_output_dir(output_dir):
    """Ensure the output directory exists."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_summary_to_csv(summary, output_path):
    """Save the summary data to CSV files."""
    # Create a timestamp for the filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    currency = summary["currency"]
    
    # Save open interest data
    oi_data = []
    for call in summary["top_open_interest"]["calls"]:
        call["option_type"] = "call"
        oi_data.append(call)
    
    for put in summary["top_open_interest"]["puts"]:
        put["option_type"] = "put"
        oi_data.append(put)
    
    oi_df = pd.DataFrame(oi_data)
    oi_file = output_path / f"{currency}_top_open_interest_{timestamp}.csv"
    oi_df.to_csv(oi_file, index=False)
    print(f"Saved open interest data to {oi_file}")
    
    # Save volume data
    vol_data = []
    for call in summary["top_volume"]["calls"]:
        call["option_type"] = "call"
        vol_data.append(call)
    
    for put in summary["top_volume"]["puts"]:
        put["option_type"] = "put"
        vol_data.append(put)
    
    vol_df = pd.DataFrame(vol_data)
    vol_file = output_path / f"{currency}_top_volume_{timestamp}.csv"
    vol_df.to_csv(vol_file, index=False)
    print(f"Saved volume data to {vol_file}")
    
    # Save summary statistics
    stats = {
        "timestamp": summary["timestamp"],
        "currency": currency,
        "current_price": summary["current_price"],
        "total_open_interest": summary["open_interest_summary"]["total_open_interest"],
        "calls_open_interest": summary["open_interest_summary"]["calls_open_interest"],
        "puts_open_interest": summary["open_interest_summary"]["puts_open_interest"],
        "put_call_ratio": summary["open_interest_summary"]["put_call_ratio"],
        "total_volume": summary["volume_statistics"]["total_volume"],
        "calls_volume": summary["volume_statistics"]["calls_volume"],
        "puts_volume": summary["volume_statistics"]["puts_volume"],
        "volume_put_call_ratio": summary["volume_statistics"]["volume_put_call_ratio"],
        # Add implied volatility metrics
        "average_iv": summary["implied_volatility_summary"]["average_iv"],
        "min_iv": summary["implied_volatility_summary"]["min_iv"],
        "max_iv": summary["implied_volatility_summary"]["max_iv"]
    }
    
    stats_df = pd.DataFrame([stats])
    stats_file = output_path / f"{currency}_summary_stats_{timestamp}.csv"
    stats_df.to_csv(stats_file, index=False)
    print(f"Saved summary statistics to {stats_file}")
    
    # Save put/call ratio by expiration
    pc_by_expiry = summary["open_interest_analysis"]["put_call_by_expiry"]
    pc_data = [{"expiration_date": date, "put_call_ratio": ratio} for date, ratio in pc_by_expiry.items()]
    pc_df = pd.DataFrame(pc_data)
    pc_file = output_path / f"{currency}_put_call_by_expiry_{timestamp}.csv"
    pc_df.to_csv(pc_file, index=False)
    print(f"Saved put/call ratio by expiration to {pc_file}")
    
    # Save high volume strikes data
    high_vol_strikes = summary["open_interest_analysis"]["high_volume_strikes"]
    high_vol_data = [
        {
            "strike": strike,
            "volume": data["volume"],
            "distance_pct": data["distance_pct"]
        }
        for strike, data in high_vol_strikes.items()
    ]
    high_vol_df = pd.DataFrame(high_vol_data)
    high_vol_file = output_path / f"{currency}_high_volume_strikes_{timestamp}.csv"
    high_vol_df.to_csv(high_vol_file, index=False)
    print(f"Saved high volume strikes data to {high_vol_file}")
    
    # Save segmented data
    for segment_key, segment_data in summary["segmented_data"].items():
        segment_stats = {
            "name": segment_data["name"],
            "total_open_interest": segment_data["total_open_interest"],
            "calls_open_interest": segment_data["calls_open_interest"],
            "puts_open_interest": segment_data["puts_open_interest"],
            "put_call_ratio": segment_data["put_call_ratio"],
            "total_volume": segment_data["total_volume"],
            "calls_volume": segment_data["calls_volume"],
            "puts_volume": segment_data["puts_volume"],
            "volume_put_call_ratio": segment_data["volume_put_call_ratio"]
        }
        
        segment_df = pd.DataFrame([segment_stats])
        segment_file = output_path / f"{currency}_{segment_key}_stats_{timestamp}.csv"
        segment_df.to_csv(segment_file, index=False)
        print(f"Saved {segment_key} segment data to {segment_file}")


def save_summary_to_json(summary, output_path):
    """Save the summary data to a JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    currency = summary["currency"]
    
    json_file = output_path / f"{currency}_options_summary_{timestamp}.json"
    
    with open(json_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"Saved summary data to {json_file}")


def main():
    """Main function to run the options chain aggregator."""
    args = parse_arguments()
    
    # Create the Deribit client
    client = DeribitClient()
    
    # Create the options analyzer
    analyzer = OptionsAnalyzer(client)
    
    try:
        # Fetch options data
        print(f"Fetching options data for {args.currency}...")
        analyzer.fetch_options_data(args.currency)
        
        # Generate daily summary
        print("Generating options summary...")
        summary = analyzer.generate_daily_summary()
        
        # Output the summary based on the specified format
        if args.output == "console":
            analyzer.print_summary(summary)
        else:
            # Ensure output directory exists
            output_path = ensure_output_dir(args.output_dir)
            
            if args.output == "csv":
                save_summary_to_csv(summary, output_path)
            elif args.output == "json":
                save_summary_to_json(summary, output_path)
        
        # Generate plots if requested
        if args.plot:
            output_path = ensure_output_dir(args.output_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            currency = args.currency
            
            # Plot open interest distribution
            oi_plot_path = output_path / f"{currency}_open_interest_distribution_{timestamp}.png"
            print(f"Generating open interest distribution plot...")
            analyzer.plot_open_interest_distribution(save_path=oi_plot_path)
            print(f"Saved open interest plot to {oi_plot_path}")
            
            # Plot implied volatility smile
            iv_plot_path = output_path / f"{currency}_implied_volatility_smile_{timestamp}.png"
            print(f"Generating implied volatility smile plot...")
            analyzer.plot_implied_volatility_smile(save_path=iv_plot_path)
            print(f"Saved implied volatility plot to {iv_plot_path}")
            
            # Plot open interest heatmap
            heatmap_path = output_path / f"{currency}_open_interest_heatmap_{timestamp}.png"
            print(f"Generating open interest heatmap...")
            analyzer.plot_open_interest_heatmap(save_path=heatmap_path)
            print(f"Saved open interest heatmap to {heatmap_path}")
            
            # Plot segmented open interest
            segment_path = output_path / f"{currency}_segmented_open_interest_{timestamp}.png"
            print(f"Generating segmented open interest plot...")
            analyzer.plot_segmented_open_interest(save_path=segment_path)
            print(f"Saved segmented open interest plot to {segment_path}")
        
        print("Options analysis completed successfully.")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 