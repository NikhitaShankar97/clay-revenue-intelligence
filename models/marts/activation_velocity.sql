{{ config(materialized='view') }}

WITH first_14_days AS (

    SELECT
        c.customer_id,
        c.company_name,

        COUNT(DISTINCT w.workflow_run_id) AS workflows_first_14d,

        COUNT(DISTINCT i.integration_name) AS integrations_used,

        MAX(
            CASE
                WHEN i.integration_name = 'Claygent'
                THEN 1
                ELSE 0
            END
        ) AS claygent_adopted

    FROM {{ ref('stg_customers') }} c

    LEFT JOIN {{ ref('stg_workflow_runs') }} w
        ON c.customer_id = w.customer_id
        AND w.started_at <= DATEADD(day, 14, c.created_at)

    LEFT JOIN {{ ref('stg_integration_runs') }} i
        ON w.workflow_run_id = i.workflow_run_id

    GROUP BY 1, 2

)

SELECT
    f.customer_id,
    f.company_name,
    f.workflows_first_14d,
    f.integrations_used,
    f.claygent_adopted,

    COALESCE(g.pipeline_generated, 0) AS pipeline_generated,
    COALESCE(g.meetings_booked, 0) AS meetings_booked,
    COALESCE(g.opportunities_created, 0) AS opportunities_created

FROM first_14_days f

LEFT JOIN {{ ref('stg_gtm_outcomes') }} g
    ON f.customer_id = g.customer_id