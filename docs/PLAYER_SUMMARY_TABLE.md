# Player Summary Table

## Overview

The `player_summary` table is a pre-aggregated table that stores player information with summed predictions for the next N gameweeks. This table serves as the primary data source for all optimization and analysis scripts, providing faster query performance compared to joining `elements` and `final_predictions` tables on-the-fly.

## Schema

| Column | Type | Description |
|--------|------|-------------|
| `player_id` | INTEGER | Primary key, player ID from FPL API |
| `name` | TEXT | Player web name (e.g., "Haaland") |
| `position` | TEXT | Position (GK, DEF, MID, FWD) |
| `team` | INTEGER | Team ID |
| `team_name` | TEXT | Team name (e.g., "Man City") |
| `price` | REAL | Current player price in £m |
| `predicted_points` | REAL | Sum of predicted points for next N gameweeks |
| `num_weeks` | INTEGER | Number of weeks predictions are summed over |
| `updated_at` | TIMESTAMP | Last update timestamp |

## Usage

### Automatic Refresh

The table is automatically created/refreshed when:
- Running `scripts/run_pipeline.py` (populates with 3 weeks after predictions)
- Calling `FPLDatabase.load_player_data(num_weeks=N)` with different `num_weeks` than stored
- Calling `FPLDatabase.load_top_performers_for_weeks(num_weeks=N)` with different `num_weeks`

### Manual Refresh

To manually refresh the table with a specific number of weeks:

```bash
python scripts/refresh_player_summary.py --weeks 3
```

### Scripts Using This Table

All the following scripts now use `player_summary` via `FPLDatabase.load_player_data()`:

1. **scripts/create_best_team.py** - ILP squad optimizer
2. **scripts/list_top_performers.py** - Top performers by position
3. **scripts/optimize_transfers.py** - Transfer optimizer
4. **ui/app.py** - Web UI for team management

## Benefits

1. **Performance**: Single table query vs. complex JOIN with aggregation
2. **Consistency**: All scripts use the same aggregated data
3. **Flexibility**: Easy to change prediction window (1, 3, 5 weeks, etc.)
4. **Simplicity**: Clean separation between raw data (final_predictions) and processed data (player_summary)

## Example Query

```sql
-- Get top 10 players by predicted points
SELECT name, position, team_name, price, predicted_points
FROM player_summary
ORDER BY predicted_points DESC
LIMIT 10;
```

## Data Flow

```
elements (API data)
    +
final_predictions (per gameweek)
    ↓
player_summary (aggregated, N weeks)
    ↓
All optimization & analysis scripts
```

## Notes

- The table stores predictions for a **configurable** number of weeks (default: 3)
- When scripts request different `num_weeks`, the table is automatically rebuilt
- The `num_weeks` column tracks the current configuration
- Indexes on `position`, `team`, and `predicted_points` ensure fast queries
