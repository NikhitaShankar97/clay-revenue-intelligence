# Snowflake Load Notes

Synthetic CSV files from `generated_data/` were loaded into the `RAW` schema in Snowflake.

The raw tables were then referenced in dbt using `source()` definitions and transformed into staging models and analytics marts.

Flow:

generated_data CSVs → Snowflake RAW tables → dbt staging models → dbt analytics marts → Streamlit and Sigma
