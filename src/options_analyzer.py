import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import matplotlib.pyplot as plt
from tabulate import tabulate
import seaborn as sns

from deribit_client import DeribitClient


class OptionsAnalyzer:
    """
    Analyzer for processing and analyzing options data from Deribit.
    """
    
    def __init__(self, client: DeribitClient):
        """
        Initialize the options analyzer.
        
        Args:
            client: DeribitClient instance for API interactions
        """
        self.client = client
        self.data = {}
    
    def _timestamp_to_date(self, timestamp: int) -> str:
        """
        Convert a Unix timestamp to a human-readable date string.
        
        Args:
            timestamp: Unix timestamp in milliseconds
            
        Returns:
            Date string in YYYY-MM-DD format
        """
        return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
    
    def fetch_options_data(self, currency: str) -> Dict[str, Any]:
        """
        Fetch all relevant options data for a currency.
        
        Args:
            currency: Currency code (BTC or ETH)
            
        Returns:
            Dictionary containing options data
        """
        # Get current index price
        index_price = self.client.get_index_price(currency)
        
        # Get all option instruments
        instruments = self.client.get_option_instruments_by_currency(currency)
        
        # Get option summaries
        summaries = self.client.get_option_summary_by_currency(currency)
        
        # Create a lookup dictionary for summaries by instrument name
        summary_by_name = {s["instrument_name"]: s for s in summaries}
        
        # Combine instrument data with summary data
        options_data = []
        for instrument in instruments:
            instrument_name = instrument["instrument_name"]
            if instrument_name in summary_by_name:
                option_data = {**instrument, **summary_by_name[instrument_name]}
                options_data.append(option_data)
        
        # Store the data
        self.data = {
            "currency": currency,
            "index_price": index_price["index_price"],
            "timestamp": datetime.now().isoformat(),
            "options": options_data
        }
        
        return self.data
    
    def create_options_dataframe(self) -> pd.DataFrame:
        """
        Create a pandas DataFrame from the options data.
        
        Returns:
            DataFrame containing options data
        """
        if not self.data or "options" not in self.data:
            raise ValueError("No options data available. Call fetch_options_data first.")
        
        df = pd.DataFrame(self.data["options"])
        
        # Extract option type (call/put) from instrument name
        df["option_type"] = df["instrument_name"].apply(
            lambda x: "call" if "-C" in x else "put" if "-P" in x else "unknown"
        )
        
        # Convert timestamps to dates
        df["expiration_date"] = df["expiration_timestamp"].apply(self._timestamp_to_date)
        df["creation_date"] = df["creation_timestamp"].apply(self._timestamp_to_date)
        
        # Calculate days to expiration
        current_time = datetime.now().timestamp() * 1000
        df["days_to_expiration"] = df["expiration_timestamp"].apply(
            lambda x: max(0, round((x - current_time) / (1000 * 60 * 60 * 24)))
        )
        
        # Calculate distance from current price (as percentage)
        current_price = self.data["index_price"]
        df["price_distance_pct"] = ((df["strike"] - current_price) / current_price * 100).round(2)
        
        return df
    
    def get_expiration_dates(self) -> List[str]:
        """
        Get a list of available expiration dates.
        
        Returns:
            List of expiration dates
        """
        df = self.create_options_dataframe()
        return sorted(df["expiration_date"].unique())
    
    def get_strike_prices(self) -> List[float]:
        """
        Get a list of available strike prices.
        
        Returns:
            List of strike prices
        """
        df = self.create_options_dataframe()
        return sorted(df["strike"].unique())
    
    def get_options_by_expiration(self, expiration_date: str) -> pd.DataFrame:
        """
        Get options data for a specific expiration date.
        
        Args:
            expiration_date: Expiration date in YYYY-MM-DD format
            
        Returns:
            DataFrame containing options for the specified expiration date
        """
        df = self.create_options_dataframe()
        return df[df["expiration_date"] == expiration_date]
    
    def get_options_by_strike(self, strike: float) -> pd.DataFrame:
        """
        Get options data for a specific strike price.
        
        Args:
            strike: Strike price
            
        Returns:
            DataFrame containing options for the specified strike price
        """
        df = self.create_options_dataframe()
        return df[df["strike"] == strike]
    
    def get_calls_and_puts(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split options data into calls and puts.
        
        Returns:
            Tuple of (calls_df, puts_df)
        """
        df = self.create_options_dataframe()
        calls = df[df["option_type"] == "call"]
        puts = df[df["option_type"] == "put"]
        return calls, puts
    
    def calculate_open_interest_summary(self) -> Dict[str, Any]:
        """
        Calculate summary statistics for open interest.
        
        Returns:
            Dictionary with open interest summary
        """
        df = self.create_options_dataframe()
        calls, puts = self.get_calls_and_puts()
        
        total_oi = df["open_interest"].sum()
        calls_oi = calls["open_interest"].sum()
        puts_oi = puts["open_interest"].sum()
        
        # Calculate put/call ratio
        put_call_ratio = puts_oi / calls_oi if calls_oi > 0 else float('inf')
        
        # Get top expirations by open interest
        expiration_oi = df.groupby("expiration_date")["open_interest"].sum().sort_values(ascending=False)
        
        # Get top strikes by open interest
        strike_oi = df.groupby("strike")["open_interest"].sum().sort_values(ascending=False)
        
        return {
            "total_open_interest": total_oi,
            "calls_open_interest": calls_oi,
            "puts_open_interest": puts_oi,
            "put_call_ratio": put_call_ratio,
            "top_expirations": expiration_oi.head(5).to_dict(),
            "top_strikes": strike_oi.head(5).to_dict()
        }
    
    def analyze_open_interest_by_strike_and_expiry(self) -> Dict[str, Any]:
        """
        Analyze open interest distribution by strike price and expiration date.
        
        Returns:
            Dictionary with open interest analysis by strike and expiration
        """
        df = self.create_options_dataframe()
        calls, puts = self.get_calls_and_puts()
        
        # Get current price
        current_price = self.data["index_price"]
        
        # Group by expiration date and strike
        oi_by_expiry_strike = df.pivot_table(
            index="expiration_date", 
            columns="strike", 
            values="open_interest", 
            aggfunc="sum",
            fill_value=0
        )
        
        # Group calls by expiration date and strike
        calls_oi_by_expiry_strike = calls.pivot_table(
            index="expiration_date", 
            columns="strike", 
            values="open_interest", 
            aggfunc="sum",
            fill_value=0
        )
        
        # Group puts by expiration date and strike
        puts_oi_by_expiry_strike = puts.pivot_table(
            index="expiration_date", 
            columns="strike", 
            values="open_interest", 
            aggfunc="sum",
            fill_value=0
        )
        
        # Calculate put/call ratio by expiration date
        put_call_by_expiry = {}
        for expiry in df["expiration_date"].unique():
            expiry_calls = calls[calls["expiration_date"] == expiry]["open_interest"].sum()
            expiry_puts = puts[puts["expiration_date"] == expiry]["open_interest"].sum()
            put_call_by_expiry[expiry] = expiry_puts / expiry_calls if expiry_calls > 0 else float('inf')
        
        # Calculate volume by strike
        volume_by_strike = df.groupby("strike")["volume"].sum().to_dict()
        
        # Find strikes with highest volume (potential oversubscribed zones)
        high_volume_strikes = pd.Series(volume_by_strike).sort_values(ascending=False).head(10).to_dict()
        
        # Calculate distance from current price for high volume strikes
        high_volume_strikes_distance = {
            strike: {
                "volume": volume,
                "distance_pct": ((strike - current_price) / current_price * 100)
            }
            for strike, volume in high_volume_strikes.items()
        }
        
        return {
            "oi_by_expiry_strike": oi_by_expiry_strike.to_dict(),
            "calls_oi_by_expiry_strike": calls_oi_by_expiry_strike.to_dict(),
            "puts_oi_by_expiry_strike": puts_oi_by_expiry_strike.to_dict(),
            "put_call_by_expiry": put_call_by_expiry,
            "volume_by_strike": volume_by_strike,
            "high_volume_strikes": high_volume_strikes_distance
        }
    
    def segment_by_expiration_timeframe(self) -> Dict[str, Any]:
        """
        Segment options data by expiration timeframes (near-term, mid-term, far-dated).
        
        Returns:
            Dictionary with segmented options data
        """
        df = self.create_options_dataframe()
        
        # Define timeframes (in days)
        near_term_days = 14  # 0-14 days
        mid_term_days = 45   # 15-45 days
        # far-dated: > 45 days
        
        # Segment data by timeframe
        near_term = df[df["days_to_expiration"] <= near_term_days]
        mid_term = df[(df["days_to_expiration"] > near_term_days) & (df["days_to_expiration"] <= mid_term_days)]
        far_dated = df[df["days_to_expiration"] > mid_term_days]
        
        # Calculate open interest and volume statistics for each segment
        segments = {
            "near_term": self._calculate_segment_stats(near_term, "Near-term (0-14 days)"),
            "mid_term": self._calculate_segment_stats(mid_term, "Mid-term (15-45 days)"),
            "far_dated": self._calculate_segment_stats(far_dated, "Far-dated (>45 days)")
        }
        
        return segments
    
    def _calculate_segment_stats(self, segment_df: pd.DataFrame, segment_name: str) -> Dict[str, Any]:
        """
        Calculate statistics for a segment of options data.
        
        Args:
            segment_df: DataFrame containing the segment data
            segment_name: Name of the segment
            
        Returns:
            Dictionary with segment statistics
        """
        if segment_df.empty:
            return {
                "name": segment_name,
                "total_open_interest": 0,
                "total_volume": 0,
                "put_call_ratio": 0,
                "volume_put_call_ratio": 0,
                "expirations": [],
                "top_strikes_by_oi": {},
                "top_strikes_by_volume": {}
            }
        
        # Split into calls and puts
        calls = segment_df[segment_df["option_type"] == "call"]
        puts = segment_df[segment_df["option_type"] == "put"]
        
        # Calculate open interest statistics
        total_oi = segment_df["open_interest"].sum()
        calls_oi = calls["open_interest"].sum()
        puts_oi = puts["open_interest"].sum()
        put_call_ratio = puts_oi / calls_oi if calls_oi > 0 else float('inf')
        
        # Calculate volume statistics
        total_volume = segment_df["volume"].sum()
        calls_volume = calls["volume"].sum()
        puts_volume = puts["volume"].sum()
        volume_put_call_ratio = puts_volume / calls_volume if calls_volume > 0 else float('inf')
        
        # Get expirations in this segment
        expirations = sorted(segment_df["expiration_date"].unique())
        
        # Get top strikes by open interest
        top_strikes_by_oi = segment_df.groupby("strike")["open_interest"].sum().sort_values(ascending=False).head(5).to_dict()
        
        # Get top strikes by volume
        top_strikes_by_volume = segment_df.groupby("strike")["volume"].sum().sort_values(ascending=False).head(5).to_dict()
        
        return {
            "name": segment_name,
            "total_open_interest": total_oi,
            "calls_open_interest": calls_oi,
            "puts_open_interest": puts_oi,
            "put_call_ratio": put_call_ratio,
            "total_volume": total_volume,
            "calls_volume": calls_volume,
            "puts_volume": puts_volume,
            "volume_put_call_ratio": volume_put_call_ratio,
            "expirations": expirations,
            "top_strikes_by_oi": top_strikes_by_oi,
            "top_strikes_by_volume": top_strikes_by_volume
        }
    
    def plot_open_interest_heatmap(self, save_path: Optional[str] = None) -> None:
        """
        Plot a heatmap of open interest by strike and expiration date.
        
        Args:
            save_path: Path to save the plot (optional)
        """
        df = self.create_options_dataframe()
        
        # Create pivot table of open interest by expiration date and strike
        pivot = df.pivot_table(
            index="expiration_date", 
            columns="strike", 
            values="open_interest", 
            aggfunc="sum",
            fill_value=0
        )
        
        # Sort by expiration date
        pivot = pivot.sort_index()
        
        # Create plot
        plt.figure(figsize=(14, 10))
        
        # Create heatmap
        sns.heatmap(pivot, cmap="YlGnBu", annot=False, fmt=".0f", linewidths=0.5)
        
        # Add labels and title
        plt.xlabel("Strike Price")
        plt.ylabel("Expiration Date")
        plt.title(f"{self.data['currency']} Open Interest Heatmap")
        
        # Format x-axis labels
        plt.xticks(rotation=45)
        
        # Save or show the plot
        if save_path:
            plt.savefig(save_path, bbox_inches="tight")
        else:
            plt.show()
        
        plt.close()
    
    def plot_segmented_open_interest(self, save_path: Optional[str] = None) -> None:
        """
        Plot open interest by expiration timeframe segments.
        
        Args:
            save_path: Path to save the plot (optional)
        """
        # Get segmented data
        segments = self.segment_by_expiration_timeframe()
        
        # Extract data for plotting
        segment_names = []
        calls_oi = []
        puts_oi = []
        
        for name, data in segments.items():
            segment_names.append(data["name"])
            calls_oi.append(data["calls_open_interest"])
            puts_oi.append(data["puts_open_interest"])
        
        # Create plot
        plt.figure(figsize=(12, 8))
        
        # Set up bar positions
        x = range(len(segment_names))
        width = 0.35
        
        # Plot bars
        plt.bar([i - width/2 for i in x], calls_oi, width, label="Calls", color="green", alpha=0.7)
        plt.bar([i + width/2 for i in x], puts_oi, width, label="Puts", color="red", alpha=0.7)
        
        # Add labels and title
        plt.xlabel("Expiration Timeframe")
        plt.ylabel("Open Interest")
        plt.title(f"{self.data['currency']} Open Interest by Expiration Timeframe")
        plt.xticks(x, segment_names)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Add put/call ratio labels
        for i, name in enumerate(segment_names):
            if calls_oi[i] > 0:
                ratio = puts_oi[i] / calls_oi[i]
                plt.text(i, max(calls_oi[i], puts_oi[i]) + 1000, f"P/C: {ratio:.2f}", 
                         ha="center", va="bottom", fontweight="bold")
        
        # Save or show the plot
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
        
        plt.close()
    
    def calculate_implied_volatility_summary(self) -> Dict[str, Any]:
        """
        Calculate summary statistics for implied volatility.
        
        Returns:
            Dictionary with implied volatility summary
        """
        df = self.create_options_dataframe()
        
        # Filter out rows with missing mark_iv
        df_with_iv = df[df["mark_iv"].notna()]
        
        if df_with_iv.empty:
            return {
                "average_iv": None,
                "min_iv": None,
                "max_iv": None,
                "iv_by_expiration": {},
                "iv_by_strike": {}
            }
        
        # Calculate overall IV statistics
        avg_iv = df_with_iv["mark_iv"].mean()
        min_iv = df_with_iv["mark_iv"].min()
        max_iv = df_with_iv["mark_iv"].max()
        
        # Calculate IV by expiration
        iv_by_expiration = df_with_iv.groupby("expiration_date")["mark_iv"].mean().sort_index().to_dict()
        
        # Calculate IV by strike (for strikes near the current price)
        current_price = self.data["index_price"]
        near_strikes = df_with_iv[
            (df_with_iv["strike"] >= current_price * 0.8) & 
            (df_with_iv["strike"] <= current_price * 1.2)
        ]
        iv_by_strike = near_strikes.groupby("strike")["mark_iv"].mean().sort_index().to_dict()
        
        return {
            "average_iv": avg_iv,
            "min_iv": min_iv,
            "max_iv": max_iv,
            "iv_by_expiration": iv_by_expiration,
            "iv_by_strike": iv_by_strike
        }
    
    def generate_daily_summary(self) -> Dict[str, Any]:
        """
        Generate a daily summary of options data.
        
        Returns:
            Dictionary with daily summary
        """
        # Fetch current data if not already available
        if not self.data or "options" not in self.data:
            raise ValueError("No options data available. Call fetch_options_data first.")
        
        # Calculate summaries
        oi_summary = self.calculate_open_interest_summary()
        iv_summary = self.calculate_implied_volatility_summary()
        
        # Get current price
        current_price = self.data["index_price"]
        
        # Get calls and puts
        calls, puts = self.get_calls_and_puts()
        
        # Calculate volume statistics
        total_volume = calls["volume"].sum() + puts["volume"].sum()
        calls_volume = calls["volume"].sum()
        puts_volume = puts["volume"].sum()
        volume_put_call_ratio = puts_volume / calls_volume if calls_volume > 0 else float('inf')
        
        # Identify options with largest open interest
        top_oi_calls = calls.sort_values("open_interest", ascending=False).head(5)
        top_oi_puts = puts.sort_values("open_interest", ascending=False).head(5)
        
        # Identify options with largest volume
        top_volume_calls = calls.sort_values("volume", ascending=False).head(5)
        top_volume_puts = puts.sort_values("volume", ascending=False).head(5)
        
        # Get open interest by strike and expiry analysis
        oi_by_strike_expiry = self.analyze_open_interest_by_strike_and_expiry()
        
        # Get segmented data by expiration timeframe
        segmented_data = self.segment_by_expiration_timeframe()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "currency": self.data["currency"],
            "current_price": current_price,
            "open_interest_summary": oi_summary,
            "implied_volatility_summary": iv_summary,
            "volume_statistics": {
                "total_volume": total_volume,
                "calls_volume": calls_volume,
                "puts_volume": puts_volume,
                "volume_put_call_ratio": volume_put_call_ratio
            },
            "top_open_interest": {
                "calls": top_oi_calls[["instrument_name", "strike", "expiration_date", "open_interest"]].to_dict("records"),
                "puts": top_oi_puts[["instrument_name", "strike", "expiration_date", "open_interest"]].to_dict("records")
            },
            "top_volume": {
                "calls": top_volume_calls[["instrument_name", "strike", "expiration_date", "volume"]].to_dict("records"),
                "puts": top_volume_puts[["instrument_name", "strike", "expiration_date", "volume"]].to_dict("records")
            },
            "open_interest_analysis": {
                "by_strike_and_expiry": oi_by_strike_expiry,
                "put_call_by_expiry": oi_by_strike_expiry["put_call_by_expiry"],
                "high_volume_strikes": oi_by_strike_expiry["high_volume_strikes"]
            },
            "segmented_data": segmented_data
        }
    
    def print_summary(self, summary: Dict[str, Any]) -> None:
        """
        Print a formatted summary of options data.
        
        Args:
            summary: Summary dictionary from generate_daily_summary
        """
        print(f"\n{'=' * 80}")
        print(f"OPTIONS SUMMARY FOR {summary['currency']} - {summary['timestamp']}")
        print(f"{'=' * 80}")
        
        print(f"\nCurrent Price: ${summary['current_price']:,.2f}")
        
        # Print open interest summary
        oi = summary["open_interest_summary"]
        print(f"\n{'-' * 40}")
        print("OPEN INTEREST SUMMARY")
        print(f"{'-' * 40}")
        print(f"Total Open Interest: {oi['total_open_interest']:,.0f}")
        print(f"Calls Open Interest: {oi['calls_open_interest']:,.0f}")
        print(f"Puts Open Interest: {oi['puts_open_interest']:,.0f}")
        print(f"Put/Call Ratio: {oi['put_call_ratio']:.2f}")
        
        # Print top expirations by open interest
        print("\nTop Expirations by Open Interest:")
        for date, oi_value in oi["top_expirations"].items():
            print(f"  {date}: {oi_value:,.0f}")
        
        # Print top strikes by open interest
        print("\nTop Strikes by Open Interest:")
        for strike, oi_value in oi["top_strikes"].items():
            print(f"  ${strike:,.0f}: {oi_value:,.0f}")
        
        # Print implied volatility summary
        iv = summary["implied_volatility_summary"]
        print(f"\n{'-' * 40}")
        print("IMPLIED VOLATILITY SUMMARY")
        print(f"{'-' * 40}")
        
        if iv["average_iv"] is not None:
            print(f"Average IV: {iv['average_iv']:.2%}")
            print(f"Min IV: {iv['min_iv']:.2%}")
            print(f"Max IV: {iv['max_iv']:.2%}")
            
            # Print IV by expiration
            print("\nIV by Expiration:")
            for date, iv_value in iv["iv_by_expiration"].items():
                print(f"  {date}: {iv_value:.2%}")
        else:
            print("No implied volatility data available.")
        
        # Print volume statistics
        vol = summary["volume_statistics"]
        print(f"\n{'-' * 40}")
        print("VOLUME STATISTICS")
        print(f"{'-' * 40}")
        print(f"Total Volume: {vol['total_volume']:,.0f}")
        print(f"Calls Volume: {vol['calls_volume']:,.0f}")
        print(f"Puts Volume: {vol['puts_volume']:,.0f}")
        print(f"Volume Put/Call Ratio: {vol['volume_put_call_ratio']:.2f}")
        
        # Print segmented data
        print(f"\n{'-' * 40}")
        print("EXPIRATION TIMEFRAME ANALYSIS")
        print(f"{'-' * 40}")
        
        for segment_key, segment_data in summary["segmented_data"].items():
            print(f"\n{segment_data['name']}:")
            print(f"  Open Interest: {segment_data['total_open_interest']:,.0f} (Calls: {segment_data['calls_open_interest']:,.0f}, Puts: {segment_data['puts_open_interest']:,.0f})")
            print(f"  Put/Call Ratio: {segment_data['put_call_ratio']:.2f}")
            print(f"  Volume: {segment_data['total_volume']:,.0f} (Calls: {segment_data['calls_volume']:,.0f}, Puts: {segment_data['puts_volume']:,.0f})")
            print(f"  Volume Put/Call Ratio: {segment_data['volume_put_call_ratio']:.2f}")
            
            if segment_data['top_strikes_by_oi']:
                print("  Top Strikes by Open Interest:")
                for strike, oi_value in segment_data['top_strikes_by_oi'].items():
                    print(f"    ${strike:,.0f}: {oi_value:,.0f}")
        
        # Print high volume strikes (potential oversubscribed zones)
        print(f"\n{'-' * 40}")
        print("HIGH VOLUME STRIKES (POTENTIAL OVERSUBSCRIBED ZONES)")
        print(f"{'-' * 40}")
        
        high_vol_strikes = summary["open_interest_analysis"]["high_volume_strikes"]
        high_vol_data = []
        
        for strike, data in high_vol_strikes.items():
            high_vol_data.append([
                f"${strike:,.0f}", 
                f"{data['volume']:,.0f}", 
                f"{data['distance_pct']:.2f}%"
            ])
        
        print(tabulate(high_vol_data, headers=["Strike", "Volume", "Distance from Current Price"]))
        
        # Print put/call ratio by expiration
        print(f"\n{'-' * 40}")
        print("PUT/CALL RATIO BY EXPIRATION")
        print(f"{'-' * 40}")
        
        pc_by_expiry = summary["open_interest_analysis"]["put_call_by_expiry"]
        pc_by_expiry_data = [[date, f"{ratio:.2f}"] for date, ratio in pc_by_expiry.items()]
        print(tabulate(pc_by_expiry_data, headers=["Expiration Date", "Put/Call Ratio"]))
        
        # Print top open interest options
        print(f"\n{'-' * 40}")
        print("TOP OPTIONS BY OPEN INTEREST")
        print(f"{'-' * 40}")
        
        print("\nTop Calls by Open Interest:")
        calls_oi_data = [[c["instrument_name"], f"${c['strike']:,.0f}", c["expiration_date"], f"{c['open_interest']:,.0f}"] 
                        for c in summary["top_open_interest"]["calls"]]
        print(tabulate(calls_oi_data, headers=["Instrument", "Strike", "Expiration", "Open Interest"]))
        
        print("\nTop Puts by Open Interest:")
        puts_oi_data = [[p["instrument_name"], f"${p['strike']:,.0f}", p["expiration_date"], f"{p['open_interest']:,.0f}"] 
                       for p in summary["top_open_interest"]["puts"]]
        print(tabulate(puts_oi_data, headers=["Instrument", "Strike", "Expiration", "Open Interest"]))
        
        # Print top volume options
        print(f"\n{'-' * 40}")
        print("TOP OPTIONS BY VOLUME")
        print(f"{'-' * 40}")
        
        print("\nTop Calls by Volume:")
        calls_vol_data = [[c["instrument_name"], f"${c['strike']:,.0f}", c["expiration_date"], f"{c['volume']:,.0f}"] 
                         for c in summary["top_volume"]["calls"]]
        print(tabulate(calls_vol_data, headers=["Instrument", "Strike", "Expiration", "Volume"]))
        
        print("\nTop Puts by Volume:")
        puts_vol_data = [[p["instrument_name"], f"${p['strike']:,.0f}", p["expiration_date"], f"{p['volume']:,.0f}"] 
                        for p in summary["top_volume"]["puts"]]
        print(tabulate(puts_vol_data, headers=["Instrument", "Strike", "Expiration", "Volume"]))
        
        print(f"\n{'=' * 80}\n")
    
    def plot_open_interest_distribution(self, save_path: Optional[str] = None) -> None:
        """
        Plot the distribution of open interest across strike prices.
        
        Args:
            save_path: Path to save the plot (optional)
        """
        df = self.create_options_dataframe()
        calls, puts = self.get_calls_and_puts()
        
        # Get current price
        current_price = self.data["index_price"]
        
        # Filter to strikes within a reasonable range of current price
        min_strike = current_price * 0.5
        max_strike = current_price * 1.5
        
        filtered_calls = calls[(calls["strike"] >= min_strike) & (calls["strike"] <= max_strike)]
        filtered_puts = puts[(puts["strike"] >= min_strike) & (puts["strike"] <= max_strike)]
        
        # Group by strike
        calls_by_strike = filtered_calls.groupby("strike")["open_interest"].sum()
        puts_by_strike = filtered_puts.groupby("strike")["open_interest"].sum()
        
        # Create plot
        plt.figure(figsize=(12, 8))
        
        # Plot calls and puts
        plt.bar(calls_by_strike.index, calls_by_strike.values, alpha=0.7, color="green", label="Calls")
        plt.bar(puts_by_strike.index, -puts_by_strike.values, alpha=0.7, color="red", label="Puts")
        
        # Add current price line
        plt.axvline(x=current_price, color="black", linestyle="--", label=f"Current Price (${current_price:,.0f})")
        
        # Add labels and title
        plt.xlabel("Strike Price")
        plt.ylabel("Open Interest")
        plt.title(f"{self.data['currency']} Options Open Interest Distribution")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Format x-axis labels
        plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        
        # Save or show the plot
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
        
        plt.close()
    
    def plot_implied_volatility_smile(self, expiration_date: Optional[str] = None, save_path: Optional[str] = None) -> None:
        """
        Plot the implied volatility smile for a specific expiration date.
        
        Args:
            expiration_date: Expiration date to plot (optional, uses nearest if not specified)
            save_path: Path to save the plot (optional)
        """
        df = self.create_options_dataframe()
        
        # Filter out rows with missing mark_iv
        df = df[df["mark_iv"].notna()]
        
        if df.empty:
            print("No implied volatility data available.")
            return
        
        # If no expiration date is specified, use the nearest one
        if not expiration_date:
            expirations = df["expiration_date"].unique()
            if len(expirations) == 0:
                print("No expiration dates available.")
                return
            
            # Sort by days to expiration and take the first one
            df_exp = df[["expiration_date", "days_to_expiration"]].drop_duplicates()
            df_exp = df_exp.sort_values("days_to_expiration")
            expiration_date = df_exp.iloc[0]["expiration_date"]
        
        # Filter to the specified expiration date
        df_exp = df[df["expiration_date"] == expiration_date]
        
        if df_exp.empty:
            print(f"No data available for expiration date {expiration_date}.")
            return
        
        # Get current price
        current_price = self.data["index_price"]
        
        # Create plot
        plt.figure(figsize=(12, 8))
        
        # Plot calls and puts
        calls = df_exp[df_exp["option_type"] == "call"]
        puts = df_exp[df_exp["option_type"] == "put"]
        
        if not calls.empty:
            plt.scatter(calls["strike"], calls["mark_iv"], color="green", alpha=0.7, label="Calls")
        
        if not puts.empty:
            plt.scatter(puts["strike"], puts["mark_iv"], color="red", alpha=0.7, label="Puts")
        
        # Add current price line
        plt.axvline(x=current_price, color="black", linestyle="--", label=f"Current Price (${current_price:,.0f})")
        
        # Add labels and title
        plt.xlabel("Strike Price")
        plt.ylabel("Implied Volatility")
        plt.title(f"{self.data['currency']} Implied Volatility Smile - {expiration_date}")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Format axes
        plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.1%}"))
        
        # Save or show the plot
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
        
        plt.close()
    
    def plot_volatility_surface(self, save_path: Optional[str] = None) -> None:
        """
        Plot a 3D volatility surface showing implied volatility across strikes and expiries.
        
        Args:
            save_path: Path to save the plot (optional)
        """
        df = self.create_options_dataframe()
        
        # Filter out rows with missing mark_iv
        df = df[df["mark_iv"].notna()]
        
        if df.empty:
            print("No implied volatility data available.")
            return
        
        # Convert expiration dates to numerical values (days to expiration)
        df = df.copy()  # Create a copy to avoid SettingWithCopyWarning
        
        # Create the 3D plot
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot surface for calls and puts separately
        for option_type, color in [("call", "green"), ("put", "red")]:
            option_data = df[df["option_type"] == option_type]
            
            if not option_data.empty:
                # Create a meshgrid for the surface
                strikes = np.array(sorted(option_data["strike"].unique()))
                days = np.array(sorted(option_data["days_to_expiration"].unique()))
                X, Y = np.meshgrid(strikes, days)
                
                # Create Z values (implied volatility)
                Z = np.zeros_like(X)
                for i, day in enumerate(days):
                    for j, strike in enumerate(strikes):
                        matching_data = option_data[
                            (option_data["days_to_expiration"] == day) & 
                            (option_data["strike"] == strike)
                        ]
                        if not matching_data.empty:
                            Z[i, j] = matching_data["mark_iv"].iloc[0]
                        else:
                            # Use NaN for missing values
                            Z[i, j] = np.nan
                
                # Plot the surface
                surf = ax.plot_surface(X, Y, Z, alpha=0.5, cmap=plt.cm.coolwarm, label=option_type.capitalize())
                surf._facecolors2d = surf._facecolor3d
                surf._edgecolors2d = surf._edgecolor3d
        
        # Add labels and title
        ax.set_xlabel('Strike Price')
        ax.set_ylabel('Days to Expiration')
        ax.set_zlabel('Implied Volatility')
        ax.set_title(f'{self.data["currency"]} Volatility Surface')
        
        # Add legend
        ax.legend()
        
        # Format axes
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:,.0f}'))
        ax.zaxis.set_major_formatter(plt.FuncFormatter(lambda z, _: f'{z:.1%}'))
        
        # Save or show the plot
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
        else:
            plt.show()
        
        plt.close()
    
    def identify_volatility_skew_hotspots(self, threshold_pct: float = 20.0) -> Dict[str, Any]:
        """
        Identify areas of significant volatility skew in the options chain.
        
        Args:
            threshold_pct: Percentage threshold for IV deviation from the mean
            
        Returns:
            Dictionary containing identified hotspots and their characteristics
        """
        df = self.create_options_dataframe()
        
        # Filter out rows with missing mark_iv
        df = df[df["mark_iv"].notna()]
        
        if df.empty:
            return {"hotspots": [], "summary": "No implied volatility data available."}
        
        hotspots = []
        
        # Analyze each expiration date separately
        for expiry in df["expiration_date"].unique():
            expiry_data = df[df["expiration_date"] == expiry]
            
            # Calculate mean IV for this expiration
            mean_iv = expiry_data["mark_iv"].mean()
            
            # Find strikes with significant IV deviation
            for option_type in ["call", "put"]:
                type_data = expiry_data[expiry_data["option_type"] == option_type]
                
                for _, row in type_data.iterrows():
                    iv_deviation_pct = ((row["mark_iv"] - mean_iv) / mean_iv) * 100
                    
                    if abs(iv_deviation_pct) >= threshold_pct:
                        hotspots.append({
                            "expiration_date": expiry,
                            "strike": row["strike"],
                            "option_type": option_type,
                            "implied_volatility": row["mark_iv"],
                            "mean_iv": mean_iv,
                            "deviation_pct": iv_deviation_pct,
                            "days_to_expiration": row["days_to_expiration"],
                            "volume": row["volume"],
                            "open_interest": row["open_interest"]
                        })
        
        # Sort hotspots by absolute deviation percentage
        hotspots.sort(key=lambda x: abs(x["deviation_pct"]), reverse=True)
        
        # Create summary statistics
        summary = {
            "total_hotspots": len(hotspots),
            "max_deviation": max([abs(h["deviation_pct"]) for h in hotspots]) if hotspots else 0,
            "avg_deviation": np.mean([abs(h["deviation_pct"]) for h in hotspots]) if hotspots else 0,
            "hotspots_by_type": {
                "calls": len([h for h in hotspots if h["option_type"] == "call"]),
                "puts": len([h for h in hotspots if h["option_type"] == "put"])
            }
        }
        
        return {
            "hotspots": hotspots,
            "summary": summary
        } 