{{ config(materialized='view') }}

SELECT
    ticket_id,
    customer_id,
    created_at,
    ticket_category,
    priority,
    resolved_at,
    ticket_metadata

FROM {{ source('raw', 'support_tickets') }}