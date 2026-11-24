# Indus Weave HR Pipeline - PeopleOps Hackathon

## Setup
pip install pandas sqlalchemy pyodbc
# Create DB etl_db in SQL Server

## Run
python run_pipeline.py

## Design Decisions
- SCD2: valid_to = next effective_from -1 day (PDF Rule)
- Faulty device: Profiling avg hour per device, corrected -1hr
- 2-min dedup: LAG() window
- Weekly roster -> Daily expand: week_start x 7 days
- Night shift: punch belongs to start date
- Leave: Both Manager+HR Approved and not Cancelled

## Team: [Your Name]