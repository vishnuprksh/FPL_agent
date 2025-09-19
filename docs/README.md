# FP## Features

- 📊 **Excel-like Interface**: Sortable, filterable table with pagination
- 🔍 **Advanced Search**: Search across all player data
- 👁️ **Column Visibility**: Show/hide columns to customize your view
- ↔️ **Horizontal Scrolling**: Scroll horizontally to view all columns on any screen size
- 📤 **Export Options**: Export to Excel, CSV, or print
- 📈 **Statistics Dashboard**: Key metrics at a glance
- 🔄 **Auto-refresh**: Data updates every 5 minutes
- 📱 **Responsive Design**: Works on desktop and mobile
- 🎨 **Modern UI**: Clean, professional interfacewer

An Excel-like web interface for viewing Fantasy Premier League (FPL) data with advanced filtering, sorting, and export capabilities.

## Features

- 📊 **Excel-like Interface**: Sortable, filterable table with pagination
- 🔍 **Advanced Search**: Search across all player data
- �️ **Column Visibility**: Show/hide columns to customize your view
- �📤 **Export Options**: Export to Excel, CSV, or print
- 📈 **Statistics Dashboard**: Key metrics at a glance
- 🔄 **Auto-refresh**: Data updates every 5 minutes
- 📱 **Responsive Design**: Works on desktop and mobile
- 🎨 **Modern UI**: Clean, professional interface

## Data Included

- Player names and positions
- Team information
- Current costs and total points
- Performance statistics (goals, assists, clean sheets, etc.)
- Advanced metrics (ICT Index, Influence, Creativity, Threat)
- Form and selection percentages
- Transfer data
- Injury/news status

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd FPL_agent
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application**:
   ```bash
   python run.py
   ```

2. **Open your browser**:
   Navigate to `http://localhost:5000`

3. **Explore the data**:
   - Use the search box to find specific players
   - Click column headers to sort
   - Use the "Show X entries" dropdown for pagination
   - **Scroll horizontally** to view all columns (especially useful on mobile devices)
   - **Customize columns**: Click the "Columns" dropdown in the navbar to show/hide specific columns
   - **Use bulk actions**: "Show All" or "Hide Advanced" buttons for quick column management
   - Export data using the buttons at the bottom

## Column Visibility

The application includes powerful column visibility controls:

- **Navbar Dropdown**: Click "Columns" in the top navigation to access a comprehensive list of all columns
- **DataTables Button**: Use the "Show/Hide Columns" button in the table footer for quick access
- **Smart Defaults**: Less important columns (like advanced stats) are hidden by default on mobile devices
- **Essential Columns**: Core columns (Name, Team, Position, Total Points) cannot be hidden
- **Bulk Actions**: "Show All" displays all columns, "Hide Advanced" hides detailed statistics

### Column Categories:
- **Core**: Name, Team, Position, Cost, Total Points (always visible)
- **Basic Stats**: Points/Game, Minutes, Goals, Assists, Clean Sheets, Form
- **Advanced Stats**: Influence, Creativity, Threat, ICT Index, BPS, Bonus
- **Disciplinary**: Yellow Cards, Red Cards, Saves, Goals Conceded
- **Transfer Info**: Selected %, Transfers In/Out
- **Status**: News, Status

## Horizontal Scrolling

The table features smooth horizontal scrolling to handle the wide range of player statistics:

- **Automatic Scrolling**: Enabled by default for all screen sizes
- **Touch-Friendly**: Optimized for mobile devices with touch scrolling
- **Visual Indicator**: Blue indicator bar shows scrollable content
- **Smooth Experience**: Custom scrollbar styling for better UX
- **Responsive**: Adapts to different screen sizes automatically

**Pro Tip**: On mobile devices, try scrolling horizontally to access all the detailed statistics that might be hidden by default!

## API Endpoints

- `GET /` - Main web interface
- `GET /api/bootstrap-static` - Player and team data
- `GET /api/fixtures` - Fixture information

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: Bootstrap 5, DataTables, jQuery
- **Data Source**: Official FPL API
- **Export**: Excel, CSV, Print functionality

## Features Overview

### Table Features
- **Sorting**: Click any column header to sort
- **Filtering**: Use the search box for global filtering
- **Pagination**: Navigate through pages of data
- **Responsive**: Automatically adjusts to screen size

### Export Options
- **Excel**: Export current view to Excel spreadsheet
- **CSV**: Export data as CSV file
- **Print**: Print-friendly version

### Statistics Dashboard
- Total number of players
- Average points per player
- Total goals and assists across the league

## Development

The application fetches live data from the FPL API, so it always shows the most current information available.

## License

See LICENSE file for details.
