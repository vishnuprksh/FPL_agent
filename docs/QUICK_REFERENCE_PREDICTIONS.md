# Quick Reference - Final Predictions Table

## Quick Stats
- **20,944** total predictions
- **748** unique players
- **280** remaining fixtures  
- **28** average fixtures per player
- **20** teams covered

## Quick Queries

### Best Players Next Gameweek
```sql
SELECT player_web_name, team_name, opponent_name, predicted_points
FROM final_predictions
WHERE gameweek = 11
ORDER BY predicted_points DESC
LIMIT 20;
```

### Top Season Predictions
```sql
SELECT player_web_name, team_name, SUM(predicted_points) as total
FROM final_predictions
GROUP BY player_id
ORDER BY total DESC
LIMIT 20;
```

### Player Fixture Schedule
```sql
SELECT gameweek, opponent_name, 
       CASE WHEN is_home=1 THEN 'H' ELSE 'A' END as venue,
       predicted_points
FROM final_predictions
WHERE player_web_name = 'Haaland'
ORDER BY gameweek;
```

### Best Value by Position
```sql
SELECT fp.player_web_name, fp.team_name, 
       e.now_cost/10.0 as price,
       SUM(fp.predicted_points) as total_points,
       SUM(fp.predicted_points)/(e.now_cost/10.0) as value
FROM final_predictions fp
JOIN elements e ON fp.player_id = e.id
WHERE fp.element_type_name = 'MID'
GROUP BY fp.player_id
ORDER BY value DESC
LIMIT 20;
```

## Table Schema (Essential Fields)

| Field | Type | Description |
|-------|------|-------------|
| player_id | INTEGER | Player unique ID |
| player_web_name | TEXT | Display name |
| team_name | TEXT | Player's team |
| opponent_name | TEXT | Opponent team |
| gameweek | INTEGER | Gameweek number |
| is_home | BOOLEAN | 1=Home, 0=Away |
| own_team_attack | REAL | Team attack value |
| own_team_defense | REAL | Team defense value |
| opponent_attack | REAL | Opponent attack value |
| opponent_defense | REAL | Opponent defense value |
| predicted_points | REAL | **ML predicted points** |

## Regenerate Predictions
```bash
python scripts/create_final_predictions.py
```

## Files
- **Script**: `scripts/create_final_predictions.py`
- **Database**: `data/fpl_agent.db`
- **Models**: `models/player_points_predictors.pkl`
- **Docs**: `docs/FINAL_PREDICTIONS.md`
