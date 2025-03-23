import os
import shutil
import subprocess

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

# === FUNCTIONS === #

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

def create_env_files():
    env_vars = {
        "ai-automation-suite": {
            "ANYTHINGLLM_API_KEY": "your-anythingllm-api-key",
            "PORT": 8000
        },
        "telegram-bot": {
            "TELEGRAM_BOT_TOKEN": "your-telegram-bot-token",
            "WEBHOOK_URL": "https://your-webhook-url",
            "PORT": 8000
        },
        "regenerate-ai-content": {
            "OPENAI_API_KEY": "your-openai-api-key",
            "PORT": 8000
        },
        "inbox-ai-agent": {
            "TELEGRAM_BOT_TOKEN": "your-telegram-bot-token",
            "TELEGRAM_CHAT_ID": "your-chat-id",
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

def create_readme():
    content = f"""
# FINAL AI AUTOMATION SUITE

## Services Included
- ai-automation-suite (Backend)
- telegram-bot (Alerts + AI Chatbot)
- regenerate-ai-content (AI Content Engine)
- regenerate-ai-frontend (Vercel Client Dashboards)
- inbox-ai-agent (Email Parsing + CRM Routing)
- super-duper-meme (Optional Viral Content Generator)

## Deployment (Railway)
Run this in your terminal:
```bash
./deploy_services.sh
