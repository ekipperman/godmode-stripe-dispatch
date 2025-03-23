import os
import hmac
import json
import time
import shutil
import hashlib
import requests
from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse

app = FastAPI()

# === ENVIRONMENT VARIABLES ===
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")
ANYTHINGLLM_API_URL = os.getenv("ANYTHINGLLM_API_URL")
ANYTHINGLLM_ADMIN_EMAIL = os.getenv("ANYTHINGLLM_ADMIN_EMAIL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RAILWAY_SERVICES = {
    "starter": ["telegram-bot", "ai-automation-suite"],
    "pro": ["telegram-bot", "ai-automation-suite", "inbox-ai-agent"],
    "enterprise": ["telegram-bot", "ai-automation-suite", "inbox-ai-agent", "regenerate-ai-content"]
}

# === TELEGRAM ALERT FUNCTION ===
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"❌ Telegram alert failed: {e}")

# === ANYTHINGLLM WORKSPACE CREATION ===
def create_anythingllm_workspace(client_name, tags="default"):
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "workspace_name": client_name,
        "admin_email": ANYTHINGLLM_ADMIN_EMAIL,
        "workspace_tags": tags
    }
    response = requests.post(f"{ANYTHINGLLM_API_URL}/workspaces", headers=headers, json=payload)

    if response.status_code == 201:
        print(f"✅ Created AnythingLLM workspace: {client_name}")
        send_telegram_alert(f"✅ AnythingLLM workspace created for {client_name}")
    else:
        print(f"❌ Failed to create AnythingLLM workspace: {response.text}")
        send_telegram_alert(f"❌ Failed to create AnythingLLM workspace for {client_name}: {response.text}")

# === RAILWAY DEPLOY FUNCTION ===
def deploy_services(services, client_name):
    for service in services:
        print(f"🚀 Deploying {service} for {client_name}")
        os.system(f"railway link --service {service}")
        os.system("railway up")
        time.sleep(5)

    send_telegram_alert(f"✅ Deployment complete for {client_name}")

# === STRIPE WEBHOOK HANDLER ===
@app.post("/stripe/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    sig_header = stripe_signature
    event = None

    try:
        event = verify_stripe_signature(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        print(f"❌ Invalid payload: {e}")
        return JSONResponse(status_code=400, content={"error": "Invalid payload"})
    except Exception as e:
        print(f"❌ Signature verification failed: {e}")
        return JSONResponse(status_code=400, content={"error": "Signature verification failed"})

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        client_name = session.get('customer_details', {}).get('name', 'Unknown Client')
        customer_email = session.get('customer_details', {}).get('email', 'No email')
        package = session.get('metadata', {}).get('package', 'starter').lower()

        print(f"✅ Payment received from {client_name} ({customer_email}), package: {package}")

        # Create AnythingLLM Workspace
        create_anythingllm_workspace(client_name)

        # Deploy relevant services
        services = RAILWAY_SERVICES.get(package, RAILWAY_SERVICES['starter'])
        deploy_services(services, client_name)

        return JSONResponse(status_code=200, content={"message": "Success"})

    print("Unhandled event type", event['type'])
    return JSONResponse(status_code=200, content={"message": "Unhandled event"})

# === STRIPE SIGNATURE VERIFICATION ===
def verify_stripe_signature(payload, sig_header, secret):
    timestamp, signatures = parse_sig_header(sig_header)
    expected_sig = generate_signature(secret, f'{timestamp}.{payload.decode()}')

    if expected_sig in signatures:
        return json.loads(payload)
    else:
        raise Exception("Signature verification failed.")

def parse_sig_header(sig_header):
    parts = sig_header.split(',')
    timestamp = parts[0].split('=')[1]
    signatures = [part.split('=')[1] for part in parts[1:]]
    return timestamp, signatures

def generate_signature(secret, payload):
    mac = hmac.new(secret.encode(), msg=payload.encode(), digestmod=hashlib.sha256)
    return mac.hexdigest()

# === ROOT ENDPOINT ===
@app.get("/")
async def root():
    return {"message": "✅ Godmode Stripe Dispatch is running!"}
