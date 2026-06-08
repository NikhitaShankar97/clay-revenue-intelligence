{{ config(materialized='view') }}

SELECT
    usage_transaction_id,
    customer_id,
    event_timestamp,
    usage_type,
    usage_category,
    units_consumed,
    related_event_id,
    usage_metadata

FROM {{ source('raw', 'usage_ledger') }}