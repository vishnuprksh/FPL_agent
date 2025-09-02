# FPL Analyst Tool

A comprehensive Fantasy Premier League (FPL) analysis tool that provides data-driven transfer and chip recommendations based on strict mathematical formulas and step-by-step analysis.

## Features

🎯 **Comprehensive Analysis**
- 8-step structured analysis process with completion tracking
- Mathematical formulas for fixture ease and predicted points
- Transfer evaluation with cost-benefit analysis
- Chip recommendation with numeric thresholds

📊 **Data-Driven Insights**
- Player watchlist generation by position
- Current team analysis with weak link identification
- Linear regression modeling for point predictions
- Rotation risk assessment based on minutes played

💰 **Transfer Recommendations**
- Free transfer suggestions
- 4-point and 8-point hit evaluations
- Budget and squad composition validation
- Net uplift calculations

🎮 **Chip Analysis**
- Triple Captain recommendations (≥15 point threshold)
- Bench Boost analysis (≥15 point threshold)
- Wildcard evaluation (≥40 point boost threshold)
- Free Hit recommendations (≥15 point boost threshold)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/vishnuprksh/FPL_agent.git
cd FPL_agent
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Interactive Web Interface (Recommended)

Run the Streamlit web application:
```bash
streamlit run fpl_analyst.py
```

Then open your browser to `http://localhost:8501`

**Features:**
- Upload your current squad via CSV, manual entry, or text import
- Configure analysis parameters (prediction week, planning horizon)
- Generate comprehensive analysis reports
- Download analysis as markdown file

### Command Line Interface

For basic analysis and testing:
```bash
python3 analysis.py
```

### Generate Sample Analysis

To test the tool with sample data:
```bash
python3 test_analysis.py
```

This will generate a sample `FPL_analysis.md` report using a test squad.

## Input Methods

### Option 1: Current Squad Input
Provide your existing 15-player squad with:
- Player names, positions, clubs, and current prices
- Team status: Bank amount, free transfers available, chips remaining

### Option 2: New Squad Builder
Build a new squad from the watchlist with:
- Total budget constraint
- Maximum players per club
- Formation requirements (GK/DEF/MID/FWD distribution)

## Analysis Output

The tool generates a comprehensive `FPL_analysis.md` report containing:

### Step 1: Key Metrics and Parameters
- Definitions and formulas for all calculations

### Step 2: Watchlist 
- Top 10 players per position by predicted points per million
- Recent form data and fixture difficulty ratings

### Step 3: Current Team Analysis
- Individual player analysis with predicted points
- Identification of 3 weakest links

### Step 4: Transfer Evaluation
- Comparison of weak links with watchlist replacements
- Transfer cost analysis and net uplift calculations

### Step 5: Recommendations
- Prioritized transfer suggestions (free, 4-hit, 8-hit)
- Cost-benefit analysis for each option

### Step 6: Chip Analysis
- Evaluation of all available chips with numeric thresholds
- Clear recommendations based on projected gains

### Step 7: Verification & Assumptions
- Data freshness confirmation
- Assumptions and limitations documented

### Step 8: Next Week Watchlist
- Key players to monitor for future weeks
- Reasoning based on form, fixtures, and tactical changes

## Data Source

The tool uses historical FPL data from the `fpl_data.csv` file, containing:
- Player performance data from 2016/17 to 2023/24 seasons
- Match statistics, points, values, and team information
- 185,000+ records for comprehensive analysis

## Key Formulas

### Fixture Ease Calculation
```
FixtureEase = (5.00 - FDR) / 4.00
```

### Predicted Points (Linear Regression)
```
PredictedPoints = max(0.00, a + b * FixtureEase)
where a = y_mean - b * x_mean
      b = Σ((x_i - x_mean)(y_i - y_mean)) / Σ((x_i - x_mean)²)
```

### Points Per Million
```
PointsPerMillion = PredictedPoints_3GW ÷ Price
```

### Transfer Net Uplift
```
NetUplift = PredictedPoints(new) - PredictedPoints(outgoing) - TransferCostPoints
```

## Requirements

- Python 3.8+
- pandas >= 2.0.0
- numpy >= 1.24.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0
- streamlit >= 1.28.0

## File Structure

```
FPL_agent/
├── fpl_analyst.py          # Main Streamlit UI application
├── analysis_engine.py      # Core analysis logic and calculations
├── report_generator.py     # Markdown report generation
├── analysis.py            # Legacy CLI interface
├── test_analysis.py       # Sample analysis generator
├── fpl_data.csv           # Historical FPL data
├── requirements.txt       # Python dependencies
├── FPL_analysis.md        # Generated analysis report (example)
└── README.md             # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for entertainment and educational purposes. FPL decisions should consider the latest official data, team news, and personal judgment. The tool's predictions are based on historical data and may not reflect current player form, injuries, or tactical changes.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
