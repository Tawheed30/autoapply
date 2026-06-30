#!/bin/bash

# 🚀 AutoApply Deployment Script for Railway
# This script automates cloud deployment to Railway

set -e

echo "🚀 Deploying AutoApply to Railway..."
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed"
    echo "   Install Node.js from https://nodejs.org/"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📂 Working directory: $SCRIPT_DIR"
echo ""

# Step 1: Check git status
echo "📝 Checking git status..."
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "⚠️  Not a git repository. Initializing..."
    git init
fi

# Step 2: Ensure Procfile exists
if [ ! -f "Procfile" ]; then
    echo "❌ Procfile not found!"
    exit 1
fi

echo "✅ Procfile found"
echo ""

# Step 3: Railway authentication
echo "🔐 Authenticating with Railway..."
echo "   (A browser window will open)"
railway login || true

echo ""
echo "📦 Initializing Railway project..."

# Check if already linked
if [ ! -f ".railway" ]; then
    echo "   Creating new Railway project..."
    railway init || true
else
    echo "   Using existing Railway project"
fi

echo ""
echo "🔗 Linking to git repository..."
railway link || true

echo ""
echo "🚀 Deploying to Railway..."
echo "   This may take 2-5 minutes..."
echo ""

railway up --detach

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📊 Checking deployment status..."
sleep 5

# Get the Railway project info
echo ""
echo "🌐 Getting your public URL..."
railway open || true

echo ""
echo "✅ Your app is deploying!"
echo ""
echo "📍 Next steps:"
echo "   1. Visit: railway open"
echo "   2. Check logs: railway logs"
echo "   3. Add API key in: Railway Dashboard → Variables"
echo ""
echo "💡 Tip: Set ANTHROPIC_API_KEY in Railway dashboard:"
echo "   railway variables set ANTHROPIC_API_KEY your_key_here"
echo ""
echo "🎉 Done! Your app will be live in a few minutes."
echo ""
echo "Need help? See DEPLOYMENT.md or QUICK_START.md"
