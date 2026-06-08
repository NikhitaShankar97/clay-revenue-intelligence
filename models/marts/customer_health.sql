{{ config(materialized='view') }}

WITH usage_summary AS (

    SELECT
        customer_id,

        SUM(
            CASE
                WHEN usage_type = 'action'
                THEN units_consumed
                ELSE 0
            END
        ) AS actions_used,

        SUM(
            CASE
                WHEN usage_type = 'data_credit'
                THEN units_consumed
                ELSE 0
            END
        ) AS data_credits_used

    FROM {{ ref('stg_usage_ledger') }}
    GROUP BY customer_id

),

workflow_summary AS (

    SELECT
        customer_id,

        COUNT(*) AS workflow_runs,

        COUNT_IF(run_status = 'completed') AS successful_workflows

    FROM {{ ref('stg_workflow_runs') }}
    GROUP BY customer_id

),

support_summary AS (

    SELECT
        customer_id,

        COUNT(*) AS support_tickets,

        COUNT_IF(priority = 'high') AS high_priority_tickets

    FROM {{ ref('stg_support_tickets') }}
    GROUP BY customer_id

)

SELECT
    c.customer_id,
    c.company_name,
    c.industry,
    c.employee_count,
    c.created_at,
    c.customer_status,
    c.primary_use_case,

    s.plan_tier,
    s.billing_interval,
    s.arr,
    s.subscription_status,

    COALESCE(u.actions_used, 0) AS actions_used,
    COALESCE(u.data_credits_used, 0) AS data_credits_used,

    COALESCE(w.workflow_runs, 0) AS workflow_runs,
    COALESCE(w.successful_workflows, 0) AS successful_workflows,

    COALESCE(sp.support_tickets, 0) AS support_tickets,
    COALESCE(sp.high_priority_tickets, 0) AS high_priority_tickets,

    COALESCE(g.meetings_booked, 0) AS meetings_booked,
    COALESCE(g.opportunities_created, 0) AS opportunities_created,
    COALESCE(g.pipeline_generated, 0) AS pipeline_generated,
    COALESCE(g.closed_won_revenue, 0) AS closed_won_revenue

FROM {{ ref('stg_customers') }} c

LEFT JOIN {{ ref('stg_subscriptions') }} s
    ON c.customer_id = s.customer_id

LEFT JOIN usage_summary u
    ON c.customer_id = u.customer_id

LEFT JOIN workflow_summary w
    ON c.customer_id = w.customer_id

LEFT JOIN support_summary sp
    ON c.customer_id = sp.customer_id

LEFT JOIN {{ ref('stg_gtm_outcomes') }} g
    ON c.customer_id = g.customer_id