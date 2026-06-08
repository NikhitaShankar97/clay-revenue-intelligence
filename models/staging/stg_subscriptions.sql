{{ config(materialized='view') }}

SELECT
    subscription_id,
    customer_id,
    plan_tier,
    billing_interval,
    subscription_start_date,
    subscription_end_date,
    monthly_amount,
    annual_contract_value,
    subscription_status,

    CASE
        WHEN billing_interval = 'monthly'
        THEN monthly_amount * 12
        ELSE annual_contract_value
    END AS arr

FROM {{ source('raw', 'subscriptions') }}