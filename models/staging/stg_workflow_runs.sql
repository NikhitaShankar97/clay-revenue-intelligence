{{ config(materialized='view') }}

SELECT
    workflow_run_id,
    customer_id,
    user_id,
    workflow_id,
    started_at,
    completed_at,
    run_status,
    run_metadata

FROM {{ source('raw', 'workflow_runs') }}