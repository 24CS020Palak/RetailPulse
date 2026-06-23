# 🛍️ RetailPulse – AI-Powered Retail Analytics Platform

### Transforming Retail Data into Actionable Business Intelligence

RetailPulse is a comprehensive end-to-end Data Science and Analytics platform designed to help retail businesses make smarter decisions through forecasting, customer intelligence, inventory optimization, and real-time monitoring.

Built using Machine Learning, Deep Learning, and Interactive Business Intelligence techniques, RetailPulse converts raw retail transactions into meaningful insights that improve revenue forecasting, customer retention, and operational efficiency.

---

## 🚀 Live Features

✅ Sales Analytics Dashboard

✅ Customer Segmentation (RFM Analysis)

✅ Churn Prediction & Explainability

✅ Demand Forecasting (Prophet + LSTM Hybrid)

✅ Inventory Optimization

✅ Real-Time Monitoring & Alerts

✅ PDF Business Reports

✅ CSV Export Center

✅ Interactive What-If Simulations

---

# 📌 Business Problem

Modern retailers generate millions of transactions but often struggle to answer critical questions:

* Which customers are most valuable?
* Which customers are likely to churn?
* What will future demand look like?
* How much inventory should be maintained?
* Which products require immediate replenishment?
* How can operational risks be detected early?

RetailPulse addresses these challenges using advanced analytics and machine learning models.

---

# 📊 Dataset

### UCI Online Retail II Dataset

A real-world transactional dataset containing:

| Metric            | Value               |
| ----------------- | ------------------- |
| Transactions      | ~1,000,000          |
| Customers         | 5,878               |
| Countries         | 37                  |
| Time Period       | Dec 2009 – Dec 2011 |
| Revenue Processed | £17.7M+             |

The dataset consists of customer purchases from a UK-based online retailer.

---

# 🏗️ System Architecture

```text
Raw Retail Data
        │
        ▼
Data Cleaning & Validation
        │
        ▼
Feature Engineering
        │
 ┌──────┼──────┐
 ▼      ▼      ▼
Forecast Churn Inventory
Model    Model  Model
 ▼       ▼      ▼
Predictions Insights Recommendations
        │
        ▼
Interactive Streamlit Dashboard
        │
        ▼
Reports & Business Decisions
```

# 🧠 Machine Learning Pipeline

## Demand Forecasting

Models Used:

* Prophet
* LSTM (PyTorch)
* Hybrid Ensemble Model

Forecasting Objective:

Predict future retail demand while minimizing forecasting error.

### Results

| Model   | MAPE  |
| ------- | ----- |
| Prophet | XX%   |
| LSTM    | XX%   |
| Hybrid  | 11.2% |

---

## Customer Analytics

### RFM Segmentation

Customers are segmented using:

* Recency
* Frequency
* Monetary Value

Segments include:

* Champions
* Loyal Customers
* Potential Loyalists
* At Risk
* Lost Customers

---

## Churn Prediction

Algorithm:

* XGBoost Classifier

Features:

* RFM Metrics
* Behavioral Features
* Purchase Trends

### Performance

| Metric    | Score |
| --------- | ----- |
| AUC-ROC   | 0.814 |
| Accuracy  | XX%   |
| Precision | XX%   |

---

## Inventory Optimization

Techniques Used:

* ABC Classification
* Economic Order Quantity (EOQ)
* Safety Stock Calculation
* Reorder Point Optimization

Benefits:

* Reduced Stockouts
* Improved Inventory Turnover
* Better Capital Utilization

---

# 📈 Dashboard Modules

## 🏠 Home Dashboard

Executive overview of business performance.

Features:

* Revenue KPIs
* Customer KPIs
* Forecast KPIs
* Inventory KPIs

---

## 💰 Sales Dashboard

Business performance monitoring.

Features:

* Revenue Trends
* Monthly Sales Analysis
* Country Performance
* Top Products
* KPI Monitoring

---

## 👥 Customer Dashboard

Customer intelligence center.

Features:

* RFM Segmentation
* Customer Profiles
* Churn Risk Explorer
* Churn Explainability

---

## 📊 Forecast Dashboard

Demand forecasting and scenario analysis.

Features:

* Forecast Visualization
* Model Comparison
* Confidence Intervals
* What-If Analysis
* Forecast Export

---

## 📦 Inventory Dashboard

Inventory decision support system.

Features:

* ABC Analysis
* Reorder Recommendations
* Product Drill-Down
* Inventory Policy Simulator

---

## 🔴 Real-Time Alerts Dashboard

Operational monitoring.

Features:

* Revenue Alerts
* Churn Alerts
* Stockout Alerts
* Forecast Drift Detection

---

## ⬇️ Export Center

Stakeholder reporting tools.

Features:

* CSV Downloads
* PDF Business Reports
* Dataset Preview
* Export Management

---

# ⚙️ Technology Stack

## Programming

* Python 3.11

## Data Processing

* Pandas
* NumPy

## Machine Learning

* Scikit-Learn
* XGBoost

## Deep Learning

* PyTorch
* LSTM

## Forecasting

* Prophet

## Dashboard

* Streamlit

## Experiment Tracking

* MLflow

## Monitoring

* Evidently AI

---

# 🚀 Installation

Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/RetailPulse.git
```

Move to Project Directory

```bash
cd RetailPulse
```

Install Dependencies

```bash
pip install -r requirements.txt
```

Run Dashboard

```bash
streamlit run streamlit_app/app.py
```

---

# 🎯 Key Achievements

✅ Built an End-to-End Analytics Platform

✅ Processed 1M+ Retail Transactions

✅ Achieved Forecast MAPE of 11.2%

✅ Developed Customer Churn Prediction System

✅ Implemented Inventory Optimization Engine

✅ Built Interactive Business Dashboard

✅ Enabled Exportable Business Reports

---

# 🔮 Future Enhancements

* Real-Time Transaction Streaming
* Cloud Deployment
* Automated Model Retraining
* Mobile Responsive Dashboard
* Generative AI Business Assistant
* Advanced Time-Series Models

---

# 👨‍💻 Author

### Palak Donga

Computer Science & Engineering Student

CHARUSAT University

Data Science | Machine Learning | Analytics

GitHub: https://github.com/24CS020Palak

---

⭐ If you found this project useful, consider giving the repository a star!
