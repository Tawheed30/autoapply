# Job Application Accelerator - Hybrid Deployment Guide

This guide sets up your app to run both locally AND on the cloud 24/7.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  Local Dev      │         │  Cloud Prod      │
│  (Your Laptop)  │         │  (Railway/Fly.io)│
├─────────────────┤         ├──────────────────┤
│ Port: 8787      │         │ Public Domain    │
│ SQLite (local)  │◄───────►│ PostgreSQL       │
│ Full access     │ Webhook │ 24/7 running     │
└─────────────────┘         └──────────────────┘
```

## Part 1: Local 24/7 Setup (macOS)

### Option A: LaunchAgent (Native macOS)

1. Create launch script:
```bash
cat > ~/Library/LaunchAgents/com.accelerator.job-application.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.accelerator.job-application</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/claude\ projects\ /Job-Application-Accelerator && source venv/bin/activate && uvicorn app.main:app --host localhost --port 8787</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/job-accelerator.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/job-accelerator-error.log</string>
</dict>
</plist>
EOF

chmod 644 ~/Library/LaunchAgents/com.accelerator.job-application.plist
launchctl load ~/Library/LaunchAgents/com.accelerator.job-application.plist
```

2. Verify running:
```bash
launchctl list | grep accelerator
```

3. View logs:
```bash
tail -f /tmp/job-accelerator.log
```

### Option B: Docker Compose (Isolated)

```bash
# Start containers
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop
docker-compose down
```

## Part 2: Cloud Deployment (Railway - Recommended)

Railway is simplest and has a generous free tier.

### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
```

### Step 2: Deploy to Railway

```bash
# Login to Railway
railway login

# Create project
railway init

# Link to this repository
railway link

# Deploy
railway up
```

### Step 3: Set Environment Variables in Railway

In Railway Dashboard → Project Settings → Variables:
```
ANTHROPIC_API_KEY=your_api_key_here
LOG_LEVEL=INFO
```

### Step 4: Get Public URL

Railway automatically assigns a domain. Find it in:
- Railway Dashboard → Deployments → View Logs
- Or: `railway open` 

Your app will be live at: `https://your-app.railway.app`

## Part 3: Custom Domain (Optional)

### Using Railway + Cloudflare (Free)

1. Register domain on Namecheap/GoDaddy ($10/year)
2. Point to Cloudflare nameservers
3. In Cloudflare, create CNAME:
   - Name: `app`
   - Target: `your-app.railway.app`
4. In Railway, add custom domain settings

Your app will be live at: `https://app.yourdomain.com`

## Part 4: Hybrid Configuration

### Local → Cloud Sync (Webhook)

When you make changes locally, notify the cloud deployment:

1. In your local app, after approval:
```python
import requests

# After approval, sync to cloud
requests.post(
    "https://your-app.railway.app/api/webhook/sync-data",
    headers={"X-API-Token": os.environ["WEBHOOK_API_TOKEN"]},
    json={"action": "sync", "data": "..."}
)
```

2. Add this endpoint to `app/main.py`:
```python
@app.post("/api/webhook/sync-data")
async def sync_data(request: SyncRequest, x_api_token: str = Header(None)):
    webhook_token = config.get_webhook_token()
    if not webhook_token or x_api_token != webhook_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    # Merge local changes into cloud database
    db.log_activity("sync_initiated", "webhook", "Local → Cloud sync", "success")
    return {"status": "syncing"}
```

### Cloud → Local Sync (Background Job)

Cloud app periodically pulls updates from local:

```python
# In background_worker.py, add:
@app.on_event("startup")
async def start_sync_job():
    scheduler.add_job(
        sync_from_cloud,
        trigger=IntervalTrigger(hours=1),
        id="cloud_sync",
        name="Sync from Cloud"
    )

async def sync_from_cloud():
    try:
        response = requests.get(
            "http://localhost:8787/api/data/export",
            headers={"Authorization": f"Bearer {LOCAL_TOKEN}"}
        )
        # Merge cloud data back
    except Exception as e:
        logger.error(f"Cloud sync failed: {e}")
```

## Part 5: Accessing Your App

### Local:
```
http://localhost:8787
```

### Cloud:
```
https://your-app.railway.app
or
https://app.yourdomain.com
```

### Remote Access to Local (Using ngrok - temporary):
```bash
# Install ngrok: https://ngrok.com
ngrok http 8787

# Get shareable URL:
# https://12345-12-345-678-90.ngrok.io
```

## Monitoring

### Local Logs:
```bash
tail -f /tmp/job-accelerator.log
tail -f /tmp/job-accelerator-error.log
```

### Cloud Logs (Railway):
```bash
railway logs
```

### Health Check:
```bash
# Local
curl http://localhost:8787/health

# Cloud
curl https://your-app.railway.app/health
```

## Troubleshooting

### App not starting on Mac?
```bash
# Check LaunchAgent
launchctl load ~/Library/LaunchAgents/com.accelerator.job-application.plist

# Unload if needed
launchctl unload ~/Library/LaunchAgents/com.accelerator.job-application.plist
```

### Cloud deployment failed?
```bash
# Check Railway logs
railway logs

# Rebuild
railway up --detach
```

### Sync not working?
```bash
# Verify webhook token
echo $WEBHOOK_API_TOKEN

# Test endpoint
curl -X POST https://your-app.railway.app/api/webhook/sync-data \
  -H "X-API-Token: $WEBHOOK_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"test"}'
```

## Summary

✅ Local: Runs 24/7 via LaunchAgent  
✅ Cloud: Deployed on Railway for public access  
✅ Hybrid: Both sync via webhooks  
✅ Domain: Custom domain via Cloudflare (optional)  
✅ Monitoring: Logs from both sources  

Total setup time: **30-45 minutes**
