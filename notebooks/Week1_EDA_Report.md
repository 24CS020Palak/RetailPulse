
# RetailPulse Week 1 - EDA Report

## Dataset
- Source: UCI Online Retail II
- Total clean rows: 805,549
- Date range: 2009-12-01 07:45:00 to 2011-12-09 12:50:00
- Unique customers: 5878
- Unique products: 4631
- Countries: 41

## Key Findings
- Approximately 25% of rows had missing Customer ID -> removed
- Cancellations (C-invoices) removed
- UK accounts for most transactions
- Strong weekly seasonality observed
- Strong yearly seasonality around Nov-Dec

## Model Results
- Prophet Baseline MAPE: 10.85
- LSTM Baseline MAPE: 12.34

## Features Created
- TotalRevenue
- Year
- Month
- DayOfWeek
- Hour

### RFM Features
- Recency
- Frequency
- Monetary

### Time-Series Features
- 7-day Rolling Average
- 30-day Rolling Average
- Lag-1
- Lag-7
- Lag-30

### Customer Segmentation
- K-Means Clusters (K=4)
- Champions
- Loyal Customers
- At-Risk Customers
- New Customers

## Week 1 Status
Completed Successfully
