# Godmode Stripe Webhook + GitHub Dispatch

## How it Works
1. Stripe checkout triggers webhook on Railway.
2. FastAPI validates webhook and triggers GitHub repository_dispatch event.
3. GitHub Action deploys Vercel client dashboard.

## Deployment on Railway
- Push to GitHub.
- Deploy on Railway.
- Add ENV variables: STRIPE_API_KEY, STRIPE_ENDPOINT_SECRET, GITHUB_TOKEN.

## Webhook URL for Stripe
```
https://your-railway-deployment-url/stripe/webhook
```
