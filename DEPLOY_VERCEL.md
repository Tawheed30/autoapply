# 🚀 Deploy AutoApply to Vercel

**Status:** QA Approved ✅  
**Version:** 1.0.0  
**Estimated Time:** 5-10 minutes  

---

## ⚠️ IMPORTANT: Vercel vs Railway for FastAPI

### Why Railway is Recommended (Skip Vercel steps if you want best experience)
- ✅ Native Python/FastAPI support
- ✅ No cold start issues (like Vercel)
- ✅ Better database integration
- ✅ Simpler deployment
- ✅ Lower latency

**Recommendation: Deploy to Railway instead** (see bottom of this guide)

---

## 🎯 Deploy to Vercel (If You Prefer)

### Prerequisites
- [ ] GitHub account with repository
- [ ] Vercel account (free tier OK)
- [ ] Environment variables ready
- [ ] Code pushed to GitHub

---

## 📋 Step 1: Push Code to GitHub

### 1.1 Initialize Git Repository
```bash
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/claude\ projects\ /Job-Application-Accelerator

# Already a git repo, just verify
git log --oneline -1
```

### 1.2 Create GitHub Repository
1. Go to https://github.com/new
2. Name: `autoapply`
3. Description: "AI-powered job application accelerator"
4. Make it **Public** (for easier deployment)
5. Click "Create repository"

### 1.3 Push to GitHub
```bash
# If no remote yet
git remote add origin https://github.com/YOUR_USERNAME/autoapply.git
git branch -M main
git push -u origin main

# Or if remote exists
git push origin main
```

---

## 🔧 Step 2: Prepare Environment Variables

Generate a strong JWT secret key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

You'll need these for Vercel:
```
ANTHROPIC_API_KEY: sk-ant-xxxxxxxxxxxxx
JWT_SECRET_KEY: (generated above)
DATABASE_URL: postgresql://... (or leave default for SQLite)
LOG_LEVEL: INFO
ENVIRONMENT: production
```

---

## 🚀 Step 3: Deploy to Vercel

### 3.1 Connect Vercel to GitHub
1. Go to https://vercel.com
2. Sign up / Log in
3. Click "Import Project"
4. Select "GitHub"
5. Find and select `autoapply` repository
6. Click "Import"

### 3.2 Configure Project
1. **Project Name:** autoapply
2. **Framework:** Python
3. **Root Directory:** ./ (default)
4. Click "Continue"

### 3.3 Add Environment Variables
1. Click "Environment Variables"
2. Add each variable:
   - `ANTHROPIC_API_KEY` = your key
   - `JWT_SECRET_KEY` = generated key
   - `DATABASE_URL` = postgresql://... (or skip for SQLite)
   - `LOG_LEVEL` = INFO
   - `ENVIRONMENT` = production

### 3.4 Deploy
1. Click "Deploy"
2. Wait 2-5 minutes for deployment
3. You'll see: "Congratulations! Your project has been successfully deployed"

### 3.5 Get Your URL
- Your app is live at: `https://autoapply-xxxxx.vercel.app`
- Copy this URL!

---

## ✅ Step 4: Verify Deployment

### 4.1 Test Health Check
```bash
curl https://autoapply-xxxxx.vercel.app/health
```

Expected response:
```json
{"status": "healthy", "version": "0.1.0", ...}
```

### 4.2 Test Landing Page
Visit: `https://autoapply-xxxxx.vercel.app/`
- Should see AutoApply landing page
- Features visible
- Pricing section visible

### 4.3 Test Signup
1. Click "Get Started"
2. Fill in form
3. Create account
4. Should redirect to dashboard

### 4.4 Test API
```bash
curl -X POST https://autoapply-xxxxx.vercel.app/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","password":"TestPass123"}'
```

---

## 🔗 Step 5: Set Custom Domain (Optional)

### 5.1 In Vercel Dashboard
1. Go to your project settings
2. Click "Domains"
3. Add custom domain: `autoapply.com` (or yours)
4. Follow DNS instructions

### 5.2 Using Cloudflare (Free)
1. Buy domain at Namecheap (~$10/year)
2. Point to Cloudflare nameservers
3. In Cloudflare, add CNAME:
   - Name: `app`
   - Target: `autoapply-xxxxx.vercel.app`
4. In Vercel, add domain verification

---

## ⚠️ Known Vercel Limitations with FastAPI

| Issue | Impact | Workaround |
|-------|--------|-----------|
| Cold starts | 5-10s first request | None (Vercel limitation) |
| SQLite persistence | Data lost on redeploy | Switch to PostgreSQL |
| Background jobs | Limited support | Use external service |
| WebSocket timeout | 25s limit | Use polling instead |

---

## 🎯 RECOMMENDED: Deploy to Railway Instead

Railway is **much better for FastAPI apps**. Here's why:

- ✅ No cold starts
- ✅ Persistent storage
- ✅ Full WebSocket support
- ✅ Background jobs native
- ✅ Better performance

### Railway Deployment (5 minutes)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/claude\ projects\ /Job-Application-Accelerator
railway init
railway link
railway up

# Get your URL
railway open
```

**That's it!** Your app is live at `https://your-app.railway.app`

---

## 🆘 Troubleshooting

### Deployment Failed
- Check build logs in Vercel dashboard
- Verify `vercel.json` exists
- Ensure all dependencies in `requirements.txt`

### 500 Errors
- Check Vercel Function logs
- Verify environment variables set
- Check database connection

### Slow Response
- This is normal for Vercel's Python runtime
- Consider switching to Railway
- Or use a different platform

### Database Issues
- Vercel doesn't persist filesystem
- Use PostgreSQL from managed service
- Or use Railway (persistent storage)

---

## 📊 Deployment Options Comparison

| Feature | Vercel | Railway | Heroku |
|---------|--------|---------|--------|
| FastAPI | ⚠️ Limited | ✅ Perfect | ✅ Good |
| Cold Starts | ❌ 5-10s | ✅ None | ✅ ~1s |
| WebSocket | ⚠️ Limited | ✅ Full | ✅ Full |
| Database | ⚠️ Managed | ✅ Included | ✅ Included |
| Free Tier | ✅ Yes | ✅ Yes | ❌ Paid |
| Ease | ⚠️ Complex | ✅ Simple | ✅ Simple |

**VERDICT: Use Railway for FastAPI** ⭐

---

## 🎉 Success Checklist

- [ ] Code pushed to GitHub
- [ ] Environment variables set in platform
- [ ] Deployment completed
- [ ] Health check working
- [ ] Landing page accessible
- [ ] Signup working
- [ ] Dashboard accessible
- [ ] Custom domain set (optional)

---

## 📚 Next Steps

1. **Vercel:** Monitor Vercel dashboard for errors
2. **Railway:** Use `railway logs` to check status
3. Set up monitoring/alerts
4. Configure custom domain
5. Share your live app!

---

## 💡 Pro Tips

- Set up error tracking (Sentry)
- Enable Vercel Analytics
- Set up database backups
- Monitor API usage
- Plan for scale

---

## 🎯 Final Recommendation

**For this FastAPI project, we recommend:**

```
Railway > Vercel > Heroku > Others
```

**Why?**
- Railway has native FastAPI support
- No cold start delays for your users
- Better database integration
- More cost-effective at scale
- Easier environment configuration

**Consider deploying to Railway instead!** See `DEPLOYMENT.md` Part 2 for step-by-step Railway instructions.

---

**Version:** 1.0.0  
**Last Updated:** June 30, 2024  
**Status:** Ready to Deploy ✅
