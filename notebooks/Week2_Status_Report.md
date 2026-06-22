# RetailPulse Week 2 - Checkpoint Report

## Scope
Week 2 covers advanced modeling and MLOps foundations: hybrid demand
forecasting, churn prediction, inventory optimization, hyperparameter
tuning, drift detection, and an automated retraining pipeline.

## F03 - Demand Forecasting (Day 8)
- Prophet MAPE: 31.08%
- LSTM MAPE: 38.08%
- Hybrid Ensemble MAPE: 30.80% (alpha=0.85)
- Target: MAPE <= 12% -> FAIL

## F04 - Churn Prediction (Day 9)
- AUC-ROC: 0.8143 (target >= 0.88)
- Precision@Top20%: 0.8863 (target >= 0.75)
- Churn rate observed: 56.6%
- Explainability: SHAP summary, dependence, and waterfall plots generated

## F05 - Inventory Optimization (Day 10)
- Stockout day reduction: 57.7%
- Average inventory reduction: -38.1%
- Demand growth factor applied: 1.1214
- Methods: ABC analysis, Safety Stock, Reorder Point, EOQ

## Model Tuning (Day 11)
- Churn model AUC improved from 0.8143 to 0.8183 (50 Optuna trials)
- Forecasting model tuned MAPE: 38.91% (25 Optuna trials)
- Permutation importance computed and compared against XGBoost built-in importance

## MLOps Maturity (Days 12-13)
- Drift detection (Evidently AI): data drift, target drift, and performance
  drift reports generated for both forecasting and churn pipelines
- Automated retraining pipeline (Airflow): drift-triggered retraining with
  a safety comparison gate before promoting any new model to production
- Model registry pattern: production / candidates / archive folders for
  safe versioning and rollback

## Week 2 Status
Partially Complete - some files missing, see checklist