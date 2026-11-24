# HR Attendance Data Pipeline - Cloud Hackathon Project

End-to-end ETL pipeline: Raw -> Staging -> Warehouse (Star Schema SCD2) -> Analytics

Data: 345K+ biometric records, 53K payroll lines, 1.3K employees

Key Results:
- Cleaned 16,178 duplicate punches (2-min dedup) + 6,784 rejected records
- Built 254,814 daily attendance rows
- Built Star Schema with SCD2 dim_employee (3,686 records)
- Found 5 paid with zero attendance & 20 paid after separation
- 10 Analytics queries + DQ Checks - 100% Reconciled

Tech: Python | SQL | ETL | Data Warehousing | Data Quality

How to Run:
python run_pipeline.py