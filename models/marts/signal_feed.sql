{{ config(materialized='view') }}

WITH activation_summary AS (

    SELECT
        CASE
            WHEN workflows_first_14d >= 3
            THEN '3+ Workflows'
            ELSE '<3 Workflows'
        END AS activation_group,

        AVG(pipeline_generated) AS avg_pipeline

    FROM {{ ref('activation_velocity') }}
    GROUP BY 1

),

activation_metric AS (

    SELECT
        ROUND(
            MAX(
                CASE
                    WHEN activation_group = '3+ Workflows'
                    THEN avg_pipeline
                END
            ) /
            NULLIF(
                MAX(
                    CASE
                        WHEN activation_group = '<3 Workflows'
                        THEN avg_pipeline
                    END
                ),
                0
            ),
            2
        ) AS activation_multiplier

    FROM activation_summary

),

claygent_summary AS (

    SELECT
        claygent_adopted,
        AVG(pipeline_generated) AS avg_pipeline

    FROM {{ ref('activation_velocity') }}
    GROUP BY 1

),

claygent_metric AS (

    SELECT
        ROUND(
            MAX(
                CASE
                    WHEN claygent_adopted = 1
                    THEN avg_pipeline
                END
            ) /
            NULLIF(
                MAX(
                    CASE
                        WHEN claygent_adopted = 0
                        THEN avg_pipeline
                    END
                ),
                0
            ),
            2
        ) AS claygent_multiplier

    FROM claygent_summary

),

expansion_metric AS (

    SELECT
        COUNT(*) AS expansion_candidates,

        SUM(
            CASE
                WHEN plan_tier <> 'Enterprise'
                THEN GREATEST(48000 - COALESCE(arr, 0), 0)
                ELSE 0
            END
        ) AS expansion_arr_opportunity

    FROM {{ ref('churn_risk_scores') }}

    WHERE plan_tier IN ('Starter', 'Explorer', 'Pro')
      AND expansion_score >= 70

),

risk_metric AS (

    SELECT
        COUNT(*) AS high_risk_accounts,
        SUM(arr) AS arr_at_risk

    FROM {{ ref('churn_risk_scores') }}

    WHERE risk_band = 'HIGH'

)

SELECT
    'Activation' AS signal_type,
    'Activation threshold is highly predictive' AS signal_title,
    activation_multiplier AS metric_value,
    NULL AS comparison_value,
    'P0' AS severity,
    'Customers reaching 3+ workflows in the first 14 days generate materially more pipeline.' AS hypothesis,
    'Add onboarding prompts that push new users to create 3 workflows within 14 days.' AS recommended_action

FROM activation_metric

WHERE activation_multiplier >= 2

UNION ALL

SELECT
    'Product Adoption' AS signal_type,
    'Claygent adoption has strong pipeline lift' AS signal_title,
    claygent_multiplier AS metric_value,
    NULL AS comparison_value,
    'P0' AS severity,
    'Claygent adopters generate materially more pipeline than non-adopters.' AS hypothesis,
    'Promote Claygent templates earlier in onboarding and Customer Success playbooks.' AS recommended_action

FROM claygent_metric

WHERE claygent_multiplier >= 2

UNION ALL

SELECT
    'Expansion' AS signal_type,
    'Expansion-ready accounts detected' AS signal_title,
    expansion_candidates AS metric_value,
    expansion_arr_opportunity AS comparison_value,
    'P1' AS severity,
    'Non-enterprise customers show Enterprise-like usage and outcome patterns.' AS hypothesis,
    'Send the account list to Sales and Customer Success for upsell review.' AS recommended_action

FROM expansion_metric

WHERE expansion_candidates > 0

UNION ALL

SELECT
    'Churn Risk' AS signal_type,
    'High-risk credit waste segment detected' AS signal_title,
    high_risk_accounts AS metric_value,
    arr_at_risk AS comparison_value,
    'P1' AS severity,
    'Some accounts show poor outcome efficiency, support friction, and elevated churn risk.' AS hypothesis,
    'Trigger proactive Customer Success intervention for high-risk accounts.' AS recommended_action

FROM risk_metric

WHERE high_risk_accounts > 0