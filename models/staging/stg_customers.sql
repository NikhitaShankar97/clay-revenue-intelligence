{{ config(materialized='view') }}

SELECT
    customer_id,
    company_name,
    industry,
    employee_count,
    created_at,
    customer_status,
    primary_use_case
FROM {{ source('raw', 'customers') }}