import os
import shutil
import subprocess
import requests
from fastapi import FastAPI, Request
import stripe

# === CONFIGURATION === #

REPOS = {
    "ai_automation_suite": "/path/to/ai-automation-suite",
    "telegram_bot": "/path/to/telegram-bot",
    "regenerate_ai_content": "/path/to/regenerate-ai-content",
    "regenerate_ai_frontend": "/path/to/regenerate-ai-frontend",
    "super_duper_meme": "/path/to/super-duper-meme",
    "inbox_ai_agent": "/path/to/inbox-ai-agent"
}

FINAL_DIR = "/path/to/final-ai-automation-suite"

RAILWAY_SERVICES = [
    "ai-automation-suite",
    "telegram-bot",
    "regenerate-ai-content",
    "inbox-ai-agent"
]

# Stripe Setup
stripe.api_key = os.getenv("STRIPE_API_KEY")
endpoint_secret = os.getenv("STRIPE_ENDPOINT_SECRET")

# === FASTAPI SERVER === #
app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        print("✅ Stripe Signature Verified")
    except ValueError as e:
        print("❌ Invalid payload:", e)
        return {"status": "invalid payload"}
    except stripe.error.SignatureVerificationError as e:
        print("❌ Invalid signature:", e)
        return {"status": "invalid signature"}

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        client_name = session.get("client_reference_id", "demo-client")
        customer_email = session.get("customer_email", "unknown@example.com")

        print(f"🚀 Checkout completed for {client_name} ({customer_email})")
        onboarding_pipeline(client_name, customer_email)

        return {"status": f"✅ Onboarding Complete for {client_name}"}

    return {"status": "Webhook Received"}


# === FUNCTIONS === #

def onboarding_pipeline(client_name, customer_email):
    print("🚀 Starting onboarding pipeline...")

    create_final_directory()
    copy_repos()
    create_env_files(client_name)
    create_github_actions()
    create_deploy_script()
    create_readme(client_name)

    create_anythingllm_workspace(client_name)
    deploy_vercel_dashboard(client_name)
    send_telegram_alert(client_name, customer_email)

    print("✅ Onboarding pipeline complete!")


def create_final_directory():
    if not os.path.exists(FINAL_DIR):
        os.makedirs(FINAL_DIR)
        print(f"✅ Created: {FINAL_DIR}")
    else:
        print(f"✅ Exists: {FINAL_DIR}")


def copy_repos():
    for name, path in REPOS.items():
        dest = os.path.join(FINAL_DIR, name)
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(path, dest)
        print(f"✅ Copied {name} to {dest}")


def create_env_files(client_name):
    env_vars = {
        "ai-automation-suite": {
            "ANYTHINGLLM_API_KEY": os.getenv("ANYTHINGLLM_API_KEY"),
            "CLIENT_NAME": client_name,
            "PORT": 8000
        },
        "telegram-bot": {
            "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
            "WEBHOOK_URL": f"https://{client_name}.vercel.app/webhook",
            "PORT": 8000
        },
        "regenerate-ai-content": {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "PORT": 8000
        },
        "inbox-ai-agent": {
            "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
            "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
            "CRM_WEBHOOK_URL": "https://your-crm-webhook",
            "SECRET_KEY": "super-secret-jwt-key",
            "PORT": 8000
        }
    }

    for service, vars in env_vars.items():
        env_file = os.path.join(FINAL_DIR, service, ".env")
        with open(env_file, "w") as f:
            for key, value in vars.items():
                f.write(f"{key}={value}\n")
        print(f"✅ Created .env for {service}")


def create_github_actions():
    workflow_dir = os.path.join(FINAL_DIR, ".github", "workflows")
    os.makedirs(workflow_dir, exist_ok=True)

    workflow = f"""
name: Railway CI/CD

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Railway Install CLI
        run: curl -fsSL https://railway.app/install.sh | sh
"""

    for service in RAILWAY_SERVICES:
        workflow += f"""
      - name: Deploy {service}
        run: |
          cd {service}
          railway up
          cd ..
"""

    workflow_path = os.path.join(workflow_dir, "railway-deploy.yml")
    with open(workflow_path, "w") as f:
        f.write(workflow)
    print(f"✅ GitHub Actions Workflow created at {workflow_path}")


def create_deploy_script():
    script_path = os.path.join(FINAL_DIR, "deploy_services.sh")
    with open(script_path, "w") as f:
        f.write("#!/bin/bash\n\n")
        f.write("echo '🚀 Starting Deployment...'\n\n")

        for service in RAILWAY_SERVICES:
            f.write(f"cd {service} && railway up && cd ..\n")

        f.write("echo '✅ Deployment Complete!'\n")

    os.chmod(script_path, 0o775)
    print(f"✅ Deployment script created at {script_path}")


def create_readme(client_name):
    content = f"""
# FINAL AI AUTOMATION SUITE

## Services Included
- ai-automation-suite (Backend)
- telegram-bot (Alerts + AI Chatbot)
- regenerate-ai-content (AI Content Engine)
- regenerate-ai-frontend (Vercel Client Dashboards)
- inbox-ai-agent (Email Parsing + CRM Routing)
- super-duper-meme (Optional Viral Content Generator)

## Client
{client_name}

## Deployment (Railway)
Run this in your terminal:
```bash
./deploy_services.sh
