{{ config(materialized='view') }}

WITH integration_summary AS (

    SELECT
        customer_id,

        COUNT(DISTINCT integration_name) AS integration_depth,

        MAX(
            CASE
                WHEN integration_name = 'Claygent'
                THEN 1
                ELSE 0
            END
        ) AS claygent_used,

        MAX(
            CASE
                WHEN integration_name = 'Waterfall'
                THEN 1
                ELSE 0
            END
        ) AS waterfall_used

    FROM {{ ref('stg_integration_runs') }}
    GROUP BY customer_id

),

base AS (

    SELECT
        h.customer_id,
        h.company_name,
        h.industry,
        h.plan_tier,
        h.arr,
        h.subscription_status,

        h.actions_used,
        h.data_credits_used,
        h.workflow_runs,
        h.successful_workflows,
        h.support_tickets,
        h.high_priority_tickets,
        h.meetings_booked,
        h.opportunities_created,
        h.pipeline_generated,
        h.closed_won_revenue,

        COALESCE(i.integration_depth, 0) AS integration_depth,
        COALESCE(i.claygent_used, 0) AS claygent_used,
        COALESCE(i.waterfall_used, 0) AS waterfall_used,

        ROUND(
            h.pipeline_generated /
            NULLIF(h.data_credits_used, 0),
            2
        ) AS pipeline_per_credit,

        ROUND(
            h.successful_workflows /
            NULLIF(h.workflow_runs, 0),
            4
        ) AS successful_workflow_rate

    FROM {{ ref('customer_health') }} h

    LEFT JOIN integration_summary i
        ON h.customer_id = i.customer_id

),

thresholds AS (

    SELECT
        PERCENTILE_CONT(0.65)
            WITHIN GROUP (ORDER BY data_credits_used)
            AS high_credit_threshold,

        PERCENTILE_CONT(0.30)
            WITHIN GROUP (ORDER BY pipeline_generated)
            AS low_pipeline_threshold,

        PERCENTILE_CONT(0.25)
            WITHIN GROUP (ORDER BY workflow_runs)
            AS low_workflow_threshold,

        PERCENTILE_CONT(0.30)
            WITHIN GROUP (ORDER BY pipeline_per_credit)
            AS low_efficiency_threshold

    FROM base

),

scored AS (

    SELECT
        b.*,

        CASE
            WHEN b.pipeline_generated <= t.low_pipeline_threshold
            THEN 1
            ELSE 0
        END AS low_pipeline_flag,

        CASE
            WHEN b.workflow_runs <= t.low_workflow_threshold
            THEN 1
            ELSE 0
        END AS low_workflow_flag,

        CASE
            WHEN b.data_credits_used >= t.high_credit_threshold
            THEN 1
            ELSE 0
        END AS high_credit_burn_flag,

        CASE
            WHEN b.claygent_used = 0
            THEN 1
            ELSE 0
        END AS no_claygent_flag,

        CASE
            WHEN b.support_tickets >= 2
            THEN 1
            ELSE 0
        END AS support_friction_flag,

        CASE
            WHEN b.pipeline_per_credit <= t.low_efficiency_threshold
            THEN 1
            ELSE 0
        END AS low_efficiency_flag

    FROM base b
    CROSS JOIN thresholds t

),

risk_math AS (

    SELECT
        *,

        LEAST(
            97,
            GREATEST(
                5,
                12
                + 24 * low_pipeline_flag
                + 16 * low_workflow_flag
                + 12 * high_credit_burn_flag
                + 8 * no_claygent_flag
                + 12 * support_friction_flag
                + 10 * low_efficiency_flag
                + ROUND(7 * (1 - COALESCE(successful_workflow_rate, 0)), 0)
            )
        ) AS churn_risk_score,

        ROUND(
            35 * PERCENT_RANK() OVER (ORDER BY pipeline_per_credit)
            + 25 * PERCENT_RANK() OVER (ORDER BY pipeline_generated)
            + 15 * PERCENT_RANK() OVER (ORDER BY workflow_runs)
            + 15 * PERCENT_RANK() OVER (ORDER BY integration_depth)
            + 10 * claygent_used,
            1
        ) AS expansion_score

    FROM scored

)

SELECT
    *,

    CASE
        WHEN churn_risk_score >= 65 THEN 'HIGH'
        WHEN churn_risk_score >= 40 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS risk_band,

    CASE
        WHEN plan_tier IN ('Starter', 'Explorer', 'Pro')
             AND expansion_score >= 70
        THEN 'Enterprise upsell'

        WHEN churn_risk_score >= 65
        THEN 'CS intervention'

        WHEN claygent_used = 0
             AND plan_tier <> 'Free'
        THEN 'Claygent onboarding'

        ELSE 'Monitor'
    END AS recommended_action

FROM risk_math