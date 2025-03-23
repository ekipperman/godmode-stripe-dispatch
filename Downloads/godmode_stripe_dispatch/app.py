import os
import hmac
import json
import time
import hashlib
import requests
from fastapi import FastAPI, Request, Header
import subprocess

app = FastAPI()

# === ENV VARIABLES === #
STRIPE_SECRET_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
ANYTHINGLLM_API_URL = os.getenv("ANYTHINGLLM_API_URL")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")
ANYTHINGLLM_ADMIN_EMAIL = os.getenv("ANYTHINGLLM_ADMIN_EMAIL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === PACKAGE MAPPING === #
PACKAGE_MAP = {
    "starter": {
        "repos": ["ai-automation-suite"],
        "workspace_tags": ["Starter", "Automation"],
    },
    "pro": {
        "repos": ["ai-automation-suite", "telegram-bot"],
        "workspace_tags": ["Pro", "LeadGen", "Telegram"],
    },
    "enterprise": {
        "repos": ["ai-automation-suite", "telegram-bot", "inbox-ai-agent"],
        "workspace_tags": ["Enterprise", "FullSuite"],
    },
}

# === HELPERS === #

def verify_signature(payload, sig_header):
    try:
        expected_sig = hmac.new(
            STRIPE_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        received_sig = sig_header.split(",")[1].split("=")[1]
        return hmac.compare_digest(expected_sig, received_sig)
    except Exception as e:
        print(f"Signature verification error: {e}")
        return False

def create_anythingllm_workspace(client_name, tags):
    url = f"{ANYTHINGLLM_API_URL}/workspaces"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": client_name,
        "description": f"Workspace for {client_name}",
        "adminEmail": ANYTHINGLLM_ADMIN_EMAIL,
        "tags": tags
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print(f"✅ AnythingLLM Workspace Created for {client_name}")
    else:
        print(f"❌ Failed to create AnythingLLM Workspace: {response.text}")

def deploy_services(repos):
    for repo in repos:
        print(f"🚀 Deploying {repo}...")
        subprocess.run(["railway", "up", "--service", repo])
        send_telegram_alert(f"✅ Deployed {repo} successfully!")

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured, skipping alert.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"⚠️ Failed to send Telegram alert: {e}")

# === STRIPE WEBHOOK === #

@app.post("/stripe/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()

    if not verify_signature(payload, stripe_signature):
        print("❌ Webhook signature invalid")
        return {"status": "invalid signature"}

    event = json.loads(payload)
    event_type = event["type"]
    print(f"📦 Stripe Event: {event_type}")

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_email", "unknown@client.com")
        client_name = customer_email.split("@")[0]
        package_name = session.get("metadata", {}).get("package", "starter")

        print(f"🎉 New Subscription: {client_name} for {package_name}")

        # Get repos and tags
        package = PACKAGE_MAP.get(package_name.lower(), PACKAGE_MAP["starter"])
        repos = package["repos"]
        tags = package["workspace_tags"]

        # Deploy and create workspace
        deploy_services(repos)
        create_anythingllm_workspace(client_name, tags)

        send_telegram_alert(f"🎉 New {package_name.capitalize()} Client: {client_name}")

    return {"status": "success"}

# === HEALTHCHECK ENDPOINT === #
@app.get("/health")
@app.get("/health/")
async def healthcheck():
    return {"status": "healthy"}

@app.get("/routes")
async def get_routes():
    return [{"path": route.path, "name": route.name} for route in app.routes]
