import os
import random
import json
from datetime import datetime, timedelta
import pandas as pd

random.seed(42)

OUTPUT_DIR = "generated_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_DATE = datetime(2026, 1, 1)

plans = {
    "Free": {"monthly": 0, "annual": 0},
    "Starter": {"monthly": 149, "annual": 1500},
    "Explorer": {"monthly": 349, "annual": 3600},
    "Pro": {"monthly": 800, "annual": 9000},
    "Enterprise": {"monthly": 4000, "annual": 48000},
}

industries = [
    "SaaS", "FinTech", "Healthcare", "Ecommerce", "HR Tech",
    "AI Software", "Cybersecurity", "Marketing Tech", "Data Infrastructure"
]

customer_names = [
    "Figma", "Rippling", "Intercom", "Verkada", "Notion", "Hex", "Oyster", "Linear",
    "Ramp", "Gong", "Loom", "Vercel", "Retool", "Airtable", "Canva", "Datadog",
    "ClickUp", "Miro", "Webflow", "Plaid", "Mercury", "Brex", "Apollo", "Amplitude",
    "Segment", "PostHog", "Navan", "Deel", "Zapier", "Attio"
]

while len(customer_names) < 100:
    customer_names.append(f"GrowthCo {len(customer_names) + 1}")

segments = (
    ["Expansion Candidate"] * 15 +
    ["Power User"] * 10 +
    ["Healthy"] * 55 +
    ["Churn Risk"] * 20
)
random.shuffle(segments)

plan_distribution = (
    ["Free"] * 25 +
    ["Starter"] * 25 +
    ["Explorer"] * 20 +
    ["Pro"] * 20 +
    ["Enterprise"] * 10
)
random.shuffle(plan_distribution)

integrations = [
    "Claygent", "Waterfall", "Apollo", "OpenAI",
    "LinkedIn Sales Navigator", "Salesforce", "HubSpot"
]

customers = []
users = []
subscriptions = []
product_events = []
usage_ledger = []
workflow_runs = []
integration_runs = []
gtm_outcomes = []
crm_pipeline_events = []
support_tickets = []
plan_changes = []
account_owners = []

owners = [
    (1, "Maya Chen", "Customer Success Manager", "West"),
    (2, "Alex Rivera", "Growth Account Manager", "East"),
    (3, "Priya Shah", "Enterprise CSM", "Central"),
    (4, "Jordan Lee", "Revenue Operations", "West"),
    (5, "Sam Patel", "Customer Success Manager", "East"),
]

for owner_id, owner_name, owner_role, assigned_region in owners:
    account_owners.append({
        "account_owner_id": owner_id,
        "owner_name": owner_name,
        "owner_role": owner_role,
        "assigned_region": assigned_region
    })

event_id = 1
usage_id = 1
workflow_run_id_counter = 1
integration_run_id = 1
outcome_id = 1
crm_event_id = 1
ticket_id = 1
plan_change_id = 1
subscription_id = 1
user_id_counter = 1

for cid in range(1, 101):
    segment = segments[cid - 1]
    plan = plan_distribution[cid - 1]
    signup_date = BASE_DATE + timedelta(days=random.randint(0, 120))
    company_name = customer_names[cid - 1]

    customers.append({
        "customer_id": cid,
        "company_name": company_name,
        "industry": random.choice(industries),
        "employee_count": random.randint(50, 5000),
        "created_at": signup_date,
        "customer_status": "churned" if segment == "Churn Risk" and random.random() < 0.35 else "active",
        "primary_use_case": random.choice([
            "Outbound prospecting",
            "Sales enrichment",
            "Pipeline generation",
            "AI account research",
            "CRM enrichment"
        ])
    })

    billing_interval = random.choice(["monthly", "annual"])
    subscriptions.append({
        "subscription_id": subscription_id,
        "customer_id": cid,
        "plan_tier": plan,
        "billing_interval": billing_interval,
        "subscription_start_date": signup_date.date(),
        "subscription_end_date": "",
        "monthly_amount": plans[plan]["monthly"],
        "annual_contract_value": plans[plan]["annual"],
        "subscription_status": "cancelled" if segment == "Churn Risk" and random.random() < 0.25 else "active",
        "billing_metadata": json.dumps({
            "billing_source": "synthetic_stripe_export",
            "currency": "USD",
            "payment_status": "free" if plan == "Free" else "paid"
        })
    })
    subscription_id += 1

    num_users = random.randint(1, 8)
    customer_user_ids = []

    for _ in range(num_users):
        created_at = signup_date + timedelta(days=random.randint(0, 14))
        last_active = created_at + timedelta(days=random.randint(3, 90))

        users.append({
            "user_id": user_id_counter,
            "customer_id": cid,
            "email_domain": company_name.lower().replace(" ", "") + ".com",
            "user_role": random.choice(["Admin", "RevOps", "SDR", "AE", "Founder", "Marketing Ops"]),
            "created_at": created_at,
            "last_active_at": last_active
        })

        customer_user_ids.append(user_id_counter)
        user_id_counter += 1

    if segment in ["Expansion Candidate", "Power User"]:
        num_workflows = random.randint(18, 40)
        claygent_probability = 0.75
        success_rate = 0.90
        support_ticket_rate = 0.10
    elif segment == "Healthy":
        num_workflows = random.randint(6, 18)
        claygent_probability = 0.35
        success_rate = 0.75
        support_ticket_rate = 0.20
    else:
        num_workflows = random.randint(1, 8)
        claygent_probability = 0.10
        success_rate = 0.45
        support_ticket_rate = 0.55

    total_data_credits = 0

    for workflow_index in range(num_workflows):
        run_start = signup_date + timedelta(days=random.randint(1, 90))
        run_end = run_start + timedelta(minutes=random.randint(5, 120))
        status = "completed" if random.random() < success_rate else "failed"

        workflow_category = random.choice([
            "lead_enrichment",
            "ai_account_research",
            "crm_sync",
            "waterfall_enrichment",
            "personalized_outbound"
        ])

        current_workflow_run_id = workflow_run_id_counter

        workflow_runs.append({
            "workflow_run_id": current_workflow_run_id,
            "customer_id": cid,
            "user_id": random.choice(customer_user_ids),
            "workflow_id": f"wf_{cid}_{workflow_index + 1}",
            "started_at": run_start,
            "completed_at": run_end if status == "completed" else "",
            "run_status": status,
            "run_metadata": json.dumps({
                "workflow_category": workflow_category,
                "template_used": random.choice([
                    "account_research",
                    "lead_enrichment",
                    "crm_enrichment",
                    "personalized_outbound"
                ]),
                "records_input": random.randint(100, 3000)
            })
        })

        event_names = ["workflow_created", "workflow_run_started"]
        if status == "completed":
            event_names += ["workflow_run_completed", "lead_enriched", "crm_sync_completed"]
        else:
            event_names += ["workflow_run_failed"]

        related_event_id = None

        for event_name in event_names:
            related_event_id = event_id
            product_events.append({
                "event_id": event_id,
                "customer_id": cid,
                "user_id": random.choice(customer_user_ids),
                "event_timestamp": run_start,
                "event_name": event_name,
                "source_system": "clay_app_events",
                "properties": json.dumps({
                    "workflow_run_id": current_workflow_run_id,
                    "workflow_category": workflow_category,
                    "status": status
                })
            })
            event_id += 1

        selected_integrations = random.sample(integrations, random.randint(1, 4))
        if random.random() < claygent_probability and "Claygent" not in selected_integrations:
            selected_integrations.append("Claygent")

        for integration in selected_integrations:
            provider_category = "AI" if integration in ["Claygent", "OpenAI"] else "Data Provider"

            integration_runs.append({
                "integration_run_id": integration_run_id,
                "customer_id": cid,
                "workflow_run_id": current_workflow_run_id,
                "integration_name": integration,
                "started_at": run_start,
                "run_status": status,
                "records_processed": random.randint(50, 2500),
                "integration_metadata": json.dumps({
                    "provider_category": provider_category,
                    "response_time_ms": random.randint(200, 2500),
                    "error_code": None if status == "completed" else random.choice([
                        "timeout",
                        "rate_limit",
                        "mapping_error"
                    ])
                })
            })
            integration_run_id += 1

        actions_used = random.randint(100, 3000)
        data_credits_used = random.randint(20, 800)
        total_data_credits += data_credits_used

        usage_ledger.append({
            "usage_transaction_id": usage_id,
            "customer_id": cid,
            "event_timestamp": run_start,
            "usage_type": "action",
            "usage_category": workflow_category,
            "units_consumed": actions_used,
            "related_event_id": related_event_id,
            "usage_metadata": json.dumps({
                "workflow_run_id": current_workflow_run_id,
                "source": "workflow_execution"
            })
        })
        usage_id += 1

        usage_ledger.append({
            "usage_transaction_id": usage_id,
            "customer_id": cid,
            "event_timestamp": run_start,
            "usage_type": "data_credit",
            "usage_category": random.choice(["enrichment", "ai_research", "waterfall"]),
            "units_consumed": data_credits_used,
            "related_event_id": related_event_id,
            "usage_metadata": json.dumps({
                "workflow_run_id": current_workflow_run_id,
                "source": "data_provider_or_ai"
            })
        })
        usage_id += 1

        workflow_run_id_counter += 1

    if segment == "Expansion Candidate":
        meeting_multiplier = random.uniform(0.045, 0.075)
    elif segment == "Power User":
        meeting_multiplier = random.uniform(0.060, 0.090)
    elif segment == "Healthy":
        meeting_multiplier = random.uniform(0.020, 0.045)
    else:
        meeting_multiplier = random.uniform(0.002, 0.015)

    meetings = int(total_data_credits * meeting_multiplier)
    opportunities = int(meetings * random.uniform(0.25, 0.55))
    pipeline = opportunities * random.randint(6000, 25000)
    closed_won = int(pipeline * random.uniform(0.05, 0.25))

    outcome_date = signup_date + timedelta(days=random.randint(30, 100))

    gtm_outcomes.append({
        "outcome_id": outcome_id,
        "customer_id": cid,
        "event_date": outcome_date.date(),
        "meetings_booked": meetings,
        "opportunities_created": opportunities,
        "pipeline_generated": pipeline,
        "closed_won_revenue": closed_won,
        "outcome_metadata": json.dumps({
            "source": "synthetic_crm_attribution",
            "attribution_model": "first_touch_plus_workflow_assisted"
        })
    })
    outcome_id += 1

    if pipeline > 0:
        num_crm_events = random.randint(1, 5)
        for i in range(num_crm_events):
            event_type = random.choice(["meeting_booked", "opportunity_created", "closed_won"])
            crm_pipeline_events.append({
                "crm_event_id": crm_event_id,
                "customer_id": cid,
                "event_date": (signup_date + timedelta(days=random.randint(20, 110))).date(),
                "crm_event_type": event_type,
                "opportunity_id": f"opp_{cid}_{i + 1}",
                "pipeline_amount": int(pipeline / num_crm_events) if event_type != "meeting_booked" else 0,
                "closed_won_amount": int(closed_won / num_crm_events) if event_type == "closed_won" else 0,
                "crm_metadata": json.dumps({
                    "source": "synthetic_crm_export",
                    "crm": random.choice(["Salesforce", "HubSpot"])
                })
            })
            crm_event_id += 1

    if segment in ["Expansion Candidate", "Power User"] and plan != "Enterprise" and random.random() < 0.55:
        new_plan = "Enterprise" if plan in ["Pro", "Explorer"] else "Pro"
        plan_changes.append({
            "plan_change_id": plan_change_id,
            "customer_id": cid,
            "changed_at": signup_date + timedelta(days=random.randint(45, 120)),
            "old_plan_tier": plan,
            "new_plan_tier": new_plan,
            "change_type": "upgrade",
            "plan_change_metadata": json.dumps({
                "reason": "high_usage_and_pipeline_generated",
                "influenced_by": "activation_velocity"
            })
        })
        plan_change_id += 1

    if segment == "Churn Risk" and random.random() < 0.45:
        plan_changes.append({
            "plan_change_id": plan_change_id,
            "customer_id": cid,
            "changed_at": signup_date + timedelta(days=random.randint(50, 120)),
            "old_plan_tier": plan,
            "new_plan_tier": "Free",
            "change_type": random.choice(["downgrade", "churn"]),
            "plan_change_metadata": json.dumps({
                "reason": "low_activation_or_credit_confusion",
                "support_escalation": True
            })
        })
        plan_change_id += 1

    if random.random() < support_ticket_rate:
        for _ in range(random.randint(1, 4)):
            created_ticket = signup_date + timedelta(days=random.randint(2, 45))
            resolved = random.random() > 0.20

            support_tickets.append({
                "ticket_id": ticket_id,
                "customer_id": cid,
                "created_at": created_ticket,
                "ticket_category": random.choice([
                    "onboarding",
                    "credits",
                    "workflow_setup",
                    "integration_issue",
                    "billing"
                ]),
                "priority": random.choice(["low", "medium", "high"]),
                "resolved_at": created_ticket + timedelta(days=random.randint(1, 7)) if resolved else "",
                "ticket_metadata": json.dumps({
                    "source": "synthetic_support_export",
                    "raw_ticket_text": random.choice([
                        "I am not sure why this workflow consumed so many credits.",
                        "I need help setting up Apollo and Claygent together.",
                        "The workflow failed and I do not know what to fix.",
                        "Can someone explain how actions are different from data credits?",
                        "This is working well but I want to improve deliverability."
                    ]),
                    "customer_sentiment": random.choice([
                        "confused",
                        "neutral",
                        "happy",
                        "frustrated"
                    ]),
                    "sentiment_note": "In a real environment, this sentiment would be derived from support text using sentiment analysis or LLM classification."
                })
            })
            ticket_id += 1

def save_csv(rows, filename):
    pd.DataFrame(rows).to_csv(os.path.join(OUTPUT_DIR, filename), index=False)

save_csv(customers, "customers.csv")
save_csv(users, "users.csv")
save_csv(subscriptions, "subscriptions.csv")
save_csv(product_events, "product_events.csv")
save_csv(usage_ledger, "usage_ledger.csv")
save_csv(workflow_runs, "workflow_runs.csv")
save_csv(integration_runs, "integration_runs.csv")
save_csv(gtm_outcomes, "gtm_outcomes.csv")
save_csv(crm_pipeline_events, "crm_pipeline_events.csv")
save_csv(support_tickets, "support_tickets.csv")
save_csv(plan_changes, "plan_change_events.csv")
save_csv(account_owners, "account_owners.csv")

print("Synthetic Clay revenue intelligence data generated successfully.")
print(f"Customers: {len(customers)}")
print(f"Users: {len(users)}")
print(f"Subscriptions: {len(subscriptions)}")
print(f"Product events: {len(product_events)}")
print(f"Workflow runs: {len(workflow_runs)}")
print(f"Integration runs: {len(integration_runs)}")
print(f"Usage ledger rows: {len(usage_ledger)}")
print(f"GTM outcomes: {len(gtm_outcomes)}")
print(f"CRM pipeline events: {len(crm_pipeline_events)}")
print(f"Support tickets: {len(support_tickets)}")
print(f"Plan changes: {len(plan_changes)}")
print(f"Account owners: {len(account_owners)}")
