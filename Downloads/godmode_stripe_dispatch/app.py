import os
import shutil
import requests
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

# === ENV VARIABLES === #
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")
ANYTHINGLLM_API_URL = os.getenv("ANYTHINGLLM_API_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === TELEGRAM ALERT === #
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ Telegram alert sent.")
    else:
        print(f"❌ Telegram alert failed: {response.text}")

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
            "ANYTHINGLLM_API_KEY": ANYTHINGLLM_API_KEY,
            "PORT": 8000
        },
        "telegram-bot": {
            "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
            "WEBHOOK_URL": "https://your-webhook-url",
            "PORT": 8000
        },
        "regenerate-ai-content": {
            "OPENAI_API_KEY": "your-openai-api-key",
            "PORT": 8000
        },
        "inbox-ai-agent": {
            "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
            "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
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

def deploy_railway_services():
    for service in RAILWAY_SERVICES:
        service_dir = os.path.join(FINAL_DIR, service)
        os.chdir(service_dir)
        send_telegram_alert(f"🚀 Deploying Railway service: {service}")
        result = subprocess.run(["railway", "up"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Deployed {service}")
            send_telegram_alert(f"✅ Railway service {service} deployed successfully!")
        else:
            print(f"❌ Deployment failed for {service}: {result.stderr}")
            send_telegram_alert(f"🚨 Deployment failed for {service}: {result.stderr}")
        os.chdir(FINAL_DIR)

def create_anythingllm_workspace(client_name):
    url = f"{ANYTHINGLLM_API_URL}/workspaces"
    headers = {"Authorization": f"Bearer {ANYTHINGLLM_API_KEY}"}
    payload = {"name": client_name}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print(f"✅ AnythingLLM Workspace Created: {client_name}")
        send_telegram_alert(f"✅ AnythingLLM workspace created for {client_name}")
    else:
        print(f"❌ AnythingLLM Workspace Failed: {response.text}")
        send_telegram_alert(f"🚨 AnythingLLM workspace failed for {client_name}: {response.text}")

def upload_documents_to_anythingllm(client_name, file_paths):
    workspace_url = f"{ANYTHINGLLM_API_URL}/workspaces/{client_name}/files"
    headers = {"Authorization": f"Bearer {ANYTHINGLLM_API_KEY}"}

    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f)}
            response = requests.post(workspace_url, headers=headers, files=files)

        if response.status_code == 200:
            print(f"✅ Uploaded {file_name} to {client_name}'s workspace")
            send_telegram_alert(f"✅ Uploaded {file_name} to {client_name}'s workspace")
        else:
            print(f"❌ Failed to upload {file_name}: {response.text}")
            send_telegram_alert(f"❌ Upload failed for {file_name}: {response.text}")

def deploy_vercel(client_name):
    vercel_token = os.getenv("VERCEL_TOKEN")
    vercel_project_id = os.getenv("VERCEL_PROJECT_ID")
    vercel_team_id = os.getenv("VERCEL_ORG_ID")
    url = "https://api.vercel.com/v13/deployments"
    headers = {"Authorization": f"Bearer {vercel_token}"}
    payload = {
        "name": client_name,
        "project": vercel_project_id,
        "teamId": vercel_team_id
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"✅ Vercel deployment triggered for {client_name}")
        send_telegram_alert(f"✅ Vercel deployment triggered for {client_name}")
    else:
        print(f"❌ Vercel deployment failed for {client_name}: {response.text}")
        send_telegram_alert(f"🚨 Vercel deployment failed for {client_name}: {response.text}")

# === EXECUTION === #
if __name__ == "__main__":
    create_final_directory()
    copy_repos()
    create_env_files()
    deploy_railway_services()

    client_name = "new-client"
    create_anythingllm_workspace(client_name)

    default_docs = [
        "/app/documents/welcome-guide.pdf",
        "/app/documents/ai-agent-manual.pdf"
    ]
    upload_documents_to_anythingllm(client_name, default_docs)
    deploy_vercel(client_name)
    send_telegram_alert("🎉 Godmode Stripe Dispatch Completed!")
