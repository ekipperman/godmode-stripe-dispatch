import os
import stripe
import requests
from fastapi import FastAPI, Request

app = FastAPI()

# === CONFIGURATION === #
stripe.api_key = os.getenv("STRIPE_API_KEY")
endpoint_secret = os.getenv("STRIPE_ENDPOINT_SECRET")

ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")
ANYTHINGLLM_API_URL = os.getenv("ANYTHINGLLM_API_URL")

VERCEL_PROJECT_ID = os.getenv("VERCEL_PROJECT_ID")
VERCEL_ORG_ID = os.getenv("VERCEL_ORG_ID")
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")

RAILWAY_SERVICES = {
    "starter": ["ai-automation-suite"],
    "pro": ["ai-automation-suite", "telegram-bot", "regenerate-ai-content"],
    "enterprise": ["ai-automation-suite", "telegram-bot", "regenerate-ai-content", "inbox-ai-agent"]
}

# === STRIPE WEBHOOK === #
@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        print(f"❌ Webhook Error: {str(e)}")
        return {"error": str(e)}

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        client_name = session.get('client_reference_id', 'demo-client')
        package_tier = session.get('metadata', {}).get('package', 'starter')

        print(f"✅ Payment received for {client_name} - Package: {package_tier}")

        create_anythingllm_workspace(client_name)
        deploy_railway_services(package_tier)
        trigger_vercel_deployment(client_name)

        return {"status": f"✅ Onboarding complete for {client_name}"}

    return {"status": "Webhook event ignored."}

# === ANYTHINGLLM WORKSPACE === #
def create_anythingllm_workspace(client_name):
    url = f"{ANYTHINGLLM_API_URL}"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": client_name,
        "description": f"Workspace for {client_name}",
        "tags": ["automation", "paid-client"],
        "visibility": "private"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        print(f"✅ AnythingLLM Workspace created for {client_name}")
    else:
        print(f"❌ AnythingLLM Workspace failed: {response.text}")

# === RAILWAY DEPLOYMENT === #
def deploy_railway_services(package_tier):
    services = RAILWAY_SERVICES.get(package_tier, [])

    for service in services:
        print(f"🚀 Deploying Railway service: {service}")
        os.system(f"railway up --service {service}")

    print("✅ Railway services deployed.")

# === VERCEL DEPLOYMENT === #
def trigger_vercel_deployment(client_name):
    url = "https://api.vercel.com/v13/deployments"
    headers = {
        "Authorization": f"Bearer {VERCEL_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": f"{client_name}-dashboard",
        "project": VERCEL_PROJECT_ID,
        "teamId": VERCEL_ORG_ID,
        "target": "production",
        "env": {
            "CLIENT_NAME": client_name,
            "ANYTHINGLLM_API_URL": ANYTHINGLLM_API_URL
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        print(f"✅ Vercel Deployment triggered for {client_name}")
    else:
        print(f"❌ Vercel Deployment failed: {response.text}")

