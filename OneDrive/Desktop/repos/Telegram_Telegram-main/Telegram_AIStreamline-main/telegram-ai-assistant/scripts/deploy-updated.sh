#!/bin/bash

# Navigate to the frontend directory
cd telegram-ai-assistant/frontend

# Install dependencies
echo "Installing dependencies..."
npm install

# Build the frontend
echo "Building the frontend..."
npm run build

# Deploy to Vercel
echo "Deploying to Vercel..."
vercel --prod

# Deploy to Railway
echo "Deploying to Railway..."
railway up

echo "Deployment completed successfully!"
