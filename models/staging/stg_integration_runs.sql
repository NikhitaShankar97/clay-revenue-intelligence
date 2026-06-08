{{ config(materialized='view') }}

SELECT
    integration_run_id,
    customer_id,
    workflow_run_id,
    integration_name,
    started_at,
    run_status,
    records_processed,
    integration_metadata

FROM {{ source('raw', 'integration_runs') }}