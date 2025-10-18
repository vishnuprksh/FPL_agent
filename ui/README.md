# FPL Agent Dashboard

A modern web-based dashboard for managing and viewing Fantasy Premier League data using the FPL Agent library.

## Features

### 🔄 Database Management
- **Update Database**: Fetch and update all FPL data for selected season
- **Season Selection**: Choose from available seasons (2025-26, 2024-25, 2023-24)
- **Real-time Status**: Live updates during database operations

### 📊 Data Viewer
- **Multiple Tables**: View all available database tables
  - Players (Seasonal data)
  - Teams
  - Player History
  - Fixtures
  - Null Value Analysis
- **Interactive Features**:
  - Sorting and filtering
  - Pagination
  - CSV export
  - Responsive design

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Dashboard
```bash
# From the project root
cd ui
python run_dashboard.py

# Or directly
python ui/dashboard.py
```

### 3. Access the Dashboard
Open your browser and navigate to: `http://localhost:8050`

## Usage Guide

### Updating the Database
1. Select the desired season from the dropdown
2. Click "Update Database" button
3. Monitor the progress through status messages
4. Data includes teams, players, history, and fixtures

### Viewing Data
1. Select a table from the "Data Viewer" section
2. Choose how many records to display
3. Use the interactive table features:
   - Sort by clicking column headers
   - Filter using the search boxes
   - Export data to CSV

### Table Descriptions

- **Players**: Current season player statistics and details
- **Teams**: Team information including strength ratings
- **Player History**: Historical performance data for all players
- **Fixtures**: Match fixtures with results and difficulty ratings
- **Null Percentages**: Data quality analysis showing missing values

## Configuration

The dashboard uses the FPL Agent configuration from `config.yaml`. Ensure your configuration is properly set up before running the dashboard.

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check that your `config.yaml` is properly configured
   - Ensure database directory exists and is writable

2. **Update Failures**
   - Verify internet connection for API/CSV downloads
   - Check FPL API status
   - Ensure sufficient disk space

3. **Table Display Issues**
   - Try refreshing the tables using "Refresh Tables" button
   - Check that database update completed successfully

### Debug Mode

The dashboard runs in debug mode by default, providing detailed error messages in the console.

## Development

### Project Structure
```
ui/
├── __init__.py          # Package initialization
├── dashboard.py         # Main dashboard application
├── run_dashboard.py     # Launcher script
└── README.md           # This file
```

### Key Components
- **FPLDashboard**: Main application class
- **Layout**: Bootstrap-based responsive design
- **Callbacks**: Interactive functionality using Dash callbacks
- **Error Handling**: Comprehensive error management

## Dependencies

- **Dash**: Web application framework
- **Dash Bootstrap Components**: UI components
- **Plotly**: Data visualization
- **Pandas**: Data manipulation
- **FPL Agent**: Core library for FPL data management

## License

This project is part of the FPL Agent library and follows the same licensing terms.