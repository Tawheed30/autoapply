# 🚀 Quick Start - Access Your App Now

Your app is **already running 24/7** locally! Here are your immediate access options:

## 📱 Local Access (Right Now)
```bash
# Your app is running at:
http://localhost:8787
```

**Status Check:**
```bash
# Verify it's running
curl http://localhost:8787/health

# View logs
tail -f /tmp/job-accelerator.log
```

---

## 🌐 Remote Access Options (Choose One)

### Option 1: Quick Temporary Access (ngrok - 30 seconds)
```bash
# Install ngrok (one-time)
brew install ngrok

# Create public URL
ngrok http 8787

# You'll get a URL like: https://abc123-456-789.ngrok.io
# Share this link to access from anywhere
```

**⏱️ Free tier:** 2 hours per session | **💰 Premium:** 24/7 access

---

### Option 2: Permanent Cloud Access (Railway - 5 minutes)

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway:**
   ```bash
   railway login
   ```
   (Opens browser to authenticate)

3. **Deploy:**
   ```bash
   cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/claude\ projects\ /Job-Application-Accelerator
   railway init
   railway link
   railway up
   ```

4. **Get your public URL:**
   ```bash
   railway open
   ```
   
   Your app is live at: `https://your-app-name.railway.app` ✅

---

### Option 3: Custom Domain (Railway + Cloudflare)

After Railway deployment:

1. Buy domain on [Namecheap](https://namecheap.com) (~$10/year)
2. Point to Cloudflare nameservers (free)
3. Add CNAME in Cloudflare dashboard:
   - Name: `app`
   - Target: `your-app-name.railway.app`
4. Add custom domain in Railway dashboard

Result: `https://app.yourdomain.com` ✅

---

## 📊 Dashboard Tabs (What You Have)

- **📝 Submit** - Submit new applications
- **⏳ Queue** - View processing queue
- **📊 Tracker** - Track application status
- **✅ Applications** - View approved/rejected
- **🔧 Status** - System health & analytics

---

## 🔑 Set Your API Key

Before using the app, set your Anthropic API key:

**Local:**
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

**Cloud (Railway):**
- Dashboard → Project Settings → Variables
- Add: `ANTHROPIC_API_KEY` = `your-key-here`

---

## ✅ Verification

**Is your app running?**
```bash
# Check if LaunchAgent is loaded
launchctl list | grep accelerator

# Should show something like:
# -	0	com.accelerator.job-application
```

**Can you access it?**
```bash
# Local
curl -s http://localhost:8787 | grep "⚡ AutoApply"

# Should return the dashboard HTML
```

---

## 🆘 Troubleshooting

**App not running?**
```bash
# Restart it
launchctl unload ~/Library/LaunchAgents/com.accelerator.job-application.plist
launchctl load ~/Library/LaunchAgents/com.accelerator.job-application.plist

# Or manually:
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/claude\ projects\ /Job-Application-Accelerator
source venv/bin/activate
uvicorn app.main:app --port 8787
```

**Port 8787 already in use?**
```bash
# Kill existing process
lsof -i :8787 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Then restart LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.accelerator.job-application.plist
launchctl load ~/Library/LaunchAgents/com.accelerator.job-application.plist
```

---

## 📈 Next Steps

1. **Test locally** → Visit http://localhost:8787
2. **Try ngrok** → Get temporary public URL in 30 seconds
3. **Deploy to Railway** → Get permanent public URL in 5 minutes
4. **Add custom domain** → Make it look professional

**Your app is production-ready!** 🎉

For detailed info, see [DEPLOYMENT.md](DEPLOYMENT.md)
