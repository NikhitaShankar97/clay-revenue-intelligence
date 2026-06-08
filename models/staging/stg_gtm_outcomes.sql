{{ config(materialized='view') }}

SELECT
    outcome_id,
    customer_id,
    event_date,
    meetings_booked,
    opportunities_created,
    pipeline_generated,
    closed_won_revenue,
    outcome_metadata

FROM {{ source('raw', 'gtm_outcomes') }}