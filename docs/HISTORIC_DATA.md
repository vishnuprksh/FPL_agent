# Historic Gameweek Data

This module provides functionality to load and query historic gameweek data for FPL players.

## Database Table

The `player_gameweek_history` table stores detailed performance data for each player in each gameweek:

- **season**: Season identifier (e.g., '2025-26')
- **gw**: Gameweek number (1-38)
- **element**: Player ID (matches the `id` in the `elements` table)
- **name**: Player name
- **position**: Player position (GK, DEF, MID, FWD)
- **team**: Team name
- **total_points**: FPL points scored in that gameweek
- **minutes**: Minutes played
- **goals_scored**: Goals scored
- **assists**: Assists provided
- **bonus**: Bonus points
- **bps**: Bonus Points System score
- Plus many other performance metrics

## Loading Data

To load historic gameweek data from the vaastav/Fantasy-Premier-League repository:

```bash
python scripts/load_historic_gameweek_data.py
```

This script will:
1. Create the `player_gameweek_history` table if it doesn't exist
2. Download all available gameweek CSV files for the 2025-26 season
3. Insert the data into the database with `season` and `gw` columns
4. Display a summary of loaded data

## Querying Data

### Python API

```python
from fpl_agent.database import FPLDatabase

db = FPLDatabase("data/fpl.db")

# Get all gameweek history for a specific player
player_history = db.get_player_gameweek_history(element_id=430)  # Erling Haaland

# Get player history for a specific season only
player_history = db.get_player_gameweek_history(element_id=430, season="2025-26")
```

### SQL Queries

```sql
-- Average points per gameweek for all players
SELECT season, gw, AVG(total_points) as avg_points
FROM player_gameweek_history
GROUP BY season, gw
ORDER BY season, gw;

-- Top performers in a specific gameweek
SELECT name, position, team, total_points, minutes
FROM player_gameweek_history
WHERE season = '2025-26' AND gw = 1
ORDER BY total_points DESC
LIMIT 10;

-- Player consistency (variance in points)
SELECT 
    element,
    name,
    AVG(total_points) as avg_points,
    COUNT(*) as games_played,
    SUM(total_points) as total_points
FROM player_gameweek_history
WHERE season = '2025-26' AND minutes > 0
GROUP BY element, name
HAVING games_played >= 3
ORDER BY avg_points DESC
LIMIT 20;

-- Form analysis (last 5 gameweeks)
SELECT 
    element,
    name,
    position,
    team,
    AVG(total_points) as avg_points_last_5
FROM player_gameweek_history
WHERE season = '2025-26' 
    AND gw >= (SELECT MAX(gw) - 4 FROM player_gameweek_history WHERE season = '2025-26')
GROUP BY element, name, position, team
ORDER BY avg_points_last_5 DESC
LIMIT 20;
```

## Data Source

Data is sourced from the [vaastav/Fantasy-Premier-League](https://github.com/vaastav/Fantasy-Premier-League) repository, which provides historical FPL data in CSV format.

## Current Data

As of the last run:
- **Season**: 2025-26
- **Gameweeks loaded**: 6
- **Total records**: 4,330 player performances
- **Data includes**: All players who appeared in matches during gameweeks 1-6
