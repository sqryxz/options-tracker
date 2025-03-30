# Crypto Options Analytics Suite

A comprehensive analytics tool for cryptocurrency options markets, featuring advanced volatility surface analysis and market inefficiency detection.

## Features

### Core Analytics
- Real-time options chain data processing for BTC and ETH
- Open interest and volume tracking across strikes and expiries
- Put/call ratio analysis with temporal segmentation
- Automated report generation in both Markdown and PDF formats

### Advanced Volatility Analysis
- 3D volatility surface visualization
- Volatility skew hotspot detection
- Implied volatility smile construction
- Market inefficiency identification

### Data Visualization
- Interactive 3D surface plots
- Open interest heatmaps
- Segmented market analysis charts
- Comparative BTC/ETH analytics

### Export Capabilities
- Structured CSV data exports
- High-resolution plot generation
- Consolidated market reports
- Volatility anomaly tracking

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/options-tracker.git
cd options-tracker

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Analysis
```bash
python3 src/main.py --currency BTC --plot --output csv
```

### Generate Consolidated Report
```bash
python3 src/consolidated_summary.py --markdown --pdf
```

### Command Line Arguments
- `--currency`: Specify the cryptocurrency (BTC or ETH)
- `--plot`: Generate visualization plots
- `--output`: Output format (csv, json)
- `--markdown`: Generate markdown report
- `--pdf`: Generate PDF report

## Output Structure

```
output/
├── consolidated_report_[timestamp].md
├── consolidated_report_[timestamp].pdf
├── [currency]_volatility_surface_[timestamp].png
├── [currency]_volatility_hotspots_[timestamp].csv
├── [currency]_open_interest_[timestamp].csv
└── ...
```

## Volatility Surface Analysis

The volatility surface module provides a comprehensive view of options market dynamics:

1. **Surface Construction**
   - 3D visualization of implied volatility
   - Strike price and expiry date mapping
   - Separate call/put surface rendering

2. **Hotspot Detection**
   - Automated anomaly identification
   - Configurable deviation thresholds
   - Statistical significance testing

3. **Market Inefficiency Analysis**
   - Volatility skew pattern recognition
   - Temporal volatility evolution tracking
   - Cross-expiry volatility comparison

## Sample Output

### Volatility Surface
```
Analyzing volatility skew hotspots...
Total hotspots found: 148
Maximum deviation: 84.77%
Average deviation: 33.05%
Calls hotspots: 74
Puts hotspots: 74
```

## Dependencies

- Python 3.8+
- NumPy
- Pandas
- Matplotlib
- Seaborn
- tabulate

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Deribit API for options data
- Matplotlib for 3D surface visualization
- Seaborn for statistical visualizations 