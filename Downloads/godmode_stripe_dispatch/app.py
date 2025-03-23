import os
import stripe
import requests
from fastapi import FastAPI, Request

app = FastAPI()
stripe.api_key = os.getenv("STRIPE_API_KEY")

@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = os.getenv("STRIPE_ENDPOINT_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        return {"error": str(e)}

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        client_name = session.get('client_reference_id', 'demo-client')

        github_dispatch_url = "https://api.github.com/repos/YOUR_ORG/YOUR_REPO/dispatches"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
        }
        data = {
            "event_type": "stripe-onboarding",
            "client_name": client_name
        }

        response = requests.post(github_dispatch_url, headers=headers, json=data)

        if response.status_code == 204:
            return {"status": "✅ GitHub Action triggered successfully!"}
        else:
            return {"status": "❌ GitHub Action trigger failed!", "response": response.json()}

    return {"status": "Ignored"}
