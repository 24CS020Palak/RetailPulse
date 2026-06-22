
"""
RetailPulse Automated Retraining Pipeline
==========================================
This DAG checks for new data, runs drift detection, and conditionally
retrains and promotes the churn prediction model.

Save this file to your Airflow dags/ folder, e.g.:
  $AIRFLOW_HOME/dags/retailpulse_retraining_dag.py
"""

from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException
from pendulum import datetime
import pickle, json, os, shutil
from datetime import datetime as dt


default_args = {
    "owner": "retailpulse_mlops",
    "retries": 3,
    "retry_delay": 300,   # seconds (5 minutes) between retries
}


@dag(
    dag_id="retailpulse_churn_retraining",
    description="Automated drift-triggered retraining for the churn model",
    schedule="@daily",          # run once every day
    start_date=datetime(2026, 1, 1),
    catchup=False,               # do not backfill past missed runs
    default_args=default_args,
    tags=["retailpulse", "mlops", "churn"],
)
def retailpulse_retraining_pipeline():

    @task
    def check_for_new_data():
        import pandas as pd
        path = "/opt/retailpulse/data/clean_retail.csv"
        df = pd.read_csv(path)
        return {"row_count": len(df), "new_data_available": True}

    @task
    def run_drift_detection(data_info: dict):
        summary_path = "/opt/retailpulse/models/day12_drift_summary.json"
        if os.path.exists(summary_path):
            with open(summary_path) as f:
                summary = json.load(f)
            should_retrain = summary["churn_pipeline"]["drifted_scenario"]["alert"]
        else:
            should_retrain = True
        return {"should_retrain": should_retrain}

    @task.branch
    def decide_retrain_or_skip(drift_info: dict):
        # task.branch must return the task_id (string) of the NEXT task to run
        if drift_info["should_retrain"]:
            return "retrain_churn_model"
        else:
            return "skip_retraining"

    @task
    def skip_retraining():
        print("No drift detected today - skipping retraining.")

    @task
    def retrain_churn_model():
        import pandas as pd
        import xgboost as xgb
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import roc_auc_score

        features = pd.read_csv("/opt/retailpulse/data/churn_features.csv")
        feature_cols = ["Recency","Frequency","Monetary","UniqueProducts",
                         "TotalQuantity","Tenure","AvgOrderValue",
                         "AvgDaysBetweenOrders","AvgBasketSize","RecencyRatio"]
        X, y = features[feature_cols], features["Churn"]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y)
        scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

        model = xgb.XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            scale_pos_weight=scale_pos_weight, eval_metric="auc",
            random_state=42)
        model.fit(X_train, y_train)
        auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])

        ts = dt.now().strftime("%Y%m%d_%H%M%S")
        path = f"/opt/retailpulse/models/candidates/churn_xgb_{ts}.pkl"
        with open(path, "wb") as f:
            pickle.dump(model, f)

        return {"candidate_path": path, "auc_roc": float(auc), "trained_at": ts}

    @task
    def compare_with_production(candidate: dict):
        metrics_path = "/opt/retailpulse/models/churn_metrics.json"
        prod_auc = 0.0
        if os.path.exists(metrics_path):
            with open(metrics_path) as f:
                prod_auc = json.load(f)["auc_roc"]
        improvement = candidate["auc_roc"] - prod_auc
        return {"should_promote": improvement >= -0.01,
                "production_auc": prod_auc,
                "candidate_auc": candidate["auc_roc"],
                "improvement": improvement}

    @task
    def promote_or_archive(candidate: dict, comparison: dict):
        prod_path = "/opt/retailpulse/models/churn_xgboost.pkl"
        if not comparison["should_promote"]:
            print("Candidate rejected - production model unchanged.")
            return {"action": "rejected"}
        if os.path.exists(prod_path):
            shutil.copy(prod_path,
                f"/opt/retailpulse/models/archive/retired_{candidate['trained_at']}.pkl")
        shutil.copy(candidate["candidate_path"], prod_path)
        with open("/opt/retailpulse/models/churn_metrics.json", "w") as f:
            json.dump({"auc_roc": candidate["auc_roc"],
                       "promoted_at": str(dt.now())}, f, indent=2)
        return {"action": "promoted"}

    @task(trigger_rule="none_failed_min_one_success")
    def send_notification(promotion: dict = None):
        # trigger_rule lets this final task run whether we came from the
        # "retrain" branch OR the "skip" branch - it always sends a status update
        action = promotion["action"] if promotion else "skipped"
        print(f"RetailPulse retraining pipeline finished. Action: {action}")

    # ---- Define the task dependency graph ----
    data_info = check_for_new_data()
    drift_info = run_drift_detection(data_info)
    branch = decide_retrain_or_skip(drift_info)

    skip = skip_retraining()
    candidate = retrain_churn_model()
    comparison = compare_with_production(candidate)
    promotion = promote_or_archive(candidate, comparison)

    branch >> [skip, candidate]
    candidate >> comparison >> promotion

    notify = send_notification(promotion)
    [skip, promotion] >> notify


retailpulse_retraining_pipeline()
