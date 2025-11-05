# Error Prevention Notes

- [2025-11-05]: When adding custom loss functions for regression, always check that database helper methods handle missing tables gracefully (check table existence before querying).
- [2025-11-05]: For variance-based penalties in ML models, apply penalties during training (in the loss function) rather than post-prediction adjustments for better model behavior.
- [2025-11-05]: When tuning variance penalty strength (lambda), test with both high-variance (CV>100%) and moderate-variance (CV~50%) players. Lambda=0.1 was too weak; Lambda=1.0 provides appropriate differentiation between consistent and erratic players.
