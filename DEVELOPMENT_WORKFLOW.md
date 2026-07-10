# 🛠️ Development Workflow Guide

**For making changes to AutoApply locally and deploying to production**

---

## 📁 Project Location

All work is in this directory:
```
~/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/claude\ projects\ /Job-Application-Accelerator
```

**Shortcut to navigate:**
```bash
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/claude\ projects\ /Job-Application-Accelerator
```

---

## 🚀 Local Development Workflow

### 1️⃣ Start Local Development Server

```bash
# Navigate to project
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/claude\ projects\ /Job-Application-Accelerator

# Activate virtual environment
source venv/bin/activate

# Start the app
uvicorn app.main:app --host localhost --port 8787 --reload
```

**Access locally:**
- Landing: http://localhost:8787/
- Signup: http://localhost:8787/signup
- Dashboard: http://localhost:8787/dashboard (after login)

**The `--reload` flag means:**
- Changes auto-reload (no restart needed)
- Perfect for development
- Perfect for testing

### 2️⃣ Make Your Changes

Edit any files:
```bash
# Backend Python files
app/main.py
app/auth.py
app/database.py
app/config.py

# Frontend HTML/CSS/JS
templates/landing.html
templates/signup.html
templates/login.html
static/dashboard.html

# Configuration
requirements.txt
vercel.json
Procfile
```

**Changes apply instantly** (with auto-reload)

### 3️⃣ Test Locally

**Test in browser:**
```
http://localhost:8787/
```

**Test API with curl:**
```bash
# Health check
curl http://localhost:8787/health

# Signup
curl -X POST http://localhost:8787/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","password":"TestPass123"}'

# Login
curl -X POST http://localhost:8787/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"TestPass123"}'
```

### 4️⃣ Commit Changes to Git

```bash
# See what changed
git status

# Stage specific files
git add app/main.py templates/landing.html

# Or stage everything
git add -A

# Commit with message
git commit -m "feat: Add new feature description"

# Push to GitHub
git push origin main
```

### 5️⃣ Deploy to Production

**If using Railway:**
```bash
# Changes auto-deploy on git push!
# Just push and Railway detects changes
git push origin main
```

**If using Vercel:**
```bash
# Vercel auto-deploys on push to GitHub
git push origin main
# Vercel automatically deploys within 1 minute
```

---

## 📋 Common Development Tasks

### Add a New Page

```bash
# 1. Create HTML file
cat > templates/about.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>About AutoApply</title></head>
<body>
  <h1>About Us</h1>
</body>
</html>
EOF

# 2. Add route to app/main.py
# Add this to main.py:
# @app.get("/about", response_class=HTMLResponse)
# def about_page():
#     with open("templates/about.html", "r") as f:
#         return f.read()

# 3. Test locally
# Visit: http://localhost:8787/about

# 4. Commit and push
git add templates/about.html app/main.py
git commit -m "feat: Add about page"
git push origin main
```

### Modify Dashboard

```bash
# 1. Edit dashboard HTML
# File: static/dashboard.html
# (auto-reloads in browser)

# 2. Test locally
# http://localhost:8787/dashboard (after login)

# 3. Commit and push
git add static/dashboard.html
git commit -m "ui: Update dashboard layout"
git push origin main
```

### Add New API Endpoint

```bash
# 1. Edit app/main.py
# Add new endpoint:
# @app.post("/api/new-feature")
# async def new_feature(request: SomeModel):
#     return {"result": "success"}

# 2. Test with curl
curl -X POST http://localhost:8787/api/new-feature \
  -H "Content-Type: application/json" \
  -d '{"data":"value"}'

# 3. Commit and push
git add app/main.py
git commit -m "feat: Add new API endpoint"
git push origin main
```

### Update Dependencies

```bash
# 1. Add to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# 2. Install locally
pip install -r requirements.txt

# 3. Test the new package
python -c "import new_package; print('OK')"

# 4. Commit and push
git add requirements.txt
git commit -m "deps: Add new-package"
git push origin main
```

---

## 🔄 Git Workflow Cheat Sheet

### Daily Development
```bash
# Start work
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/claude\ projects\ /Job-Application-Accelerator
source venv/bin/activate
uvicorn app.main:app --host localhost --port 8787 --reload

# Make changes... (changes auto-reload)

# When ready to deploy
git status                    # See what changed
git add app/main.py          # Stage specific files
git commit -m "feat: description"
git push origin main

# Done! Auto-deploys to production
```

### Check Status
```bash
git status              # See unstaged changes
git log --oneline -10   # See recent commits
git diff                # See detailed changes
```

### Undo Changes
```bash
# Undo unstaged changes to a file
git checkout app/main.py

# Undo all unstaged changes
git checkout .

# Undo a commit (create new reverse commit)
git revert HEAD

# Undo last commit (keep changes)
git reset --soft HEAD~1
```

---

## 🗄️ Database Management

### Local Database
```bash
# Database is at: data/accelerator.db
# SQLite file - persists locally

# View schema
sqlite3 data/accelerator.db ".schema"

# Query data
sqlite3 data/accelerator.db "SELECT * FROM users;"
```

### Production Database (Railway/Vercel)

**Railway:**
```bash
# Access production database via Railway dashboard
railway logs   # See application logs
railway shell  # SSH into app environment
```

**Vercel:**
```bash
# If using managed Postgres
# Access via Vercel dashboard
# Or use CLI: vercel env ls
```

---

## 📱 Testing Your Changes

### Unit Testing
```bash
# Run existing tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

### Manual Testing Checklist
- [ ] Landing page loads
- [ ] Signup works
- [ ] Login works
- [ ] Dashboard accessible
- [ ] Can submit jobs
- [ ] Logout works
- [ ] API endpoints respond
- [ ] No console errors

### Performance Testing
```bash
# Check response time
time curl http://localhost:8787/health

# Should be < 100ms locally
```

---

## 🔐 Environment Variables

### Local Development
Create a `.env` file (NOT committed to git):
```bash
# .env (local only - never commit this!)
ANTHROPIC_API_KEY=sk-ant-your-key-here
JWT_SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./data/accelerator.db
LOG_LEVEL=DEBUG
```

### Production (Railway/Vercel)
Set in your platform's dashboard:
- Railway: `railway variables set KEY=VALUE`
- Vercel: Dashboard → Project Settings → Environment Variables

**Never commit `.env` to git!**

---

## 📊 File Structure for Reference

```
Job-Application-Accelerator/
├── app/
│   ├── main.py              # Main FastAPI app
│   ├── auth.py              # Authentication logic
│   ├── database.py          # Database operations
│   ├── config.py            # Configuration
│   └── ...other modules
├── templates/
│   ├── landing.html         # Landing page
│   ├── signup.html          # Signup form
│   ├── login.html           # Login form
│   ├── privacy.html         # Privacy policy
│   └── terms.html           # Terms of service
├── static/
│   ├── dashboard.html       # Main dashboard (protected)
│   └── manifest.json        # PWA config
├── data/
│   └── accelerator.db       # Local SQLite database
├── requirements.txt         # Python dependencies
├── vercel.json             # Vercel config
├── Procfile                # Railway/Heroku config
├── Dockerfile              # Docker config
├── DEPLOYMENT.md           # Deployment guide
├── DEVELOP_WORKFLOW.md     # This file
└── .gitignore              # Git ignore rules
```

---

## 🚨 Common Issues & Fixes

### App Won't Start
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Try running with full output
uvicorn app.main:app --host localhost --port 8787 --reload --log-level debug
```

### Port Already in Use
```bash
# Find process using port 8787
lsof -i :8787

# Kill it
kill -9 <PID>

# Or use different port
uvicorn app.main:app --host localhost --port 8788
```

### Changes Not Showing
```bash
# Hard refresh browser
Cmd+Shift+R (Mac)
Ctrl+Shift+R (Windows/Linux)

# Clear cache
# Browser → Settings → Clear browsing data
```

### Git Push Failed
```bash
# Pull latest changes first
git pull origin main

# If conflicts, resolve them
# Then push
git push origin main
```

### Database Issues
```bash
# Backup current database
cp data/accelerator.db data/accelerator.db.backup

# Delete and recreate
rm data/accelerator.db

# Restart app (creates fresh database)
```

---

## 🎯 Production Update Workflow

### For Small Changes
```bash
# 1. Make change locally
# 2. Test in browser
# 3. git add/commit/push
# 4. Auto-deploys (1-5 minutes)
```

### For Database Changes
```bash
# 1. Update database.py schema
# 2. The migration runs automatically on startup
# 3. Push to git
# 4. Production auto-updates
```

### For Breaking Changes
```bash
# 1. Test thoroughly locally
# 2. Consider data migration steps
# 3. Document changes in commit message
# 4. Monitor production after deployment
```

---

## 📈 Monitoring Production

### Check Deployment Status

**Railway:**
```bash
railway status        # Check deployment status
railway logs         # View live logs
railway env list     # See environment variables
```

**Vercel:**
```bash
# Use Vercel dashboard:
# vercel.com → Your Project → Deployments

# Or CLI:
vercel ls            # List deployments
vercel logs          # View logs
```

### Check Application Health
```bash
# Production health check
curl https://your-app-url/health

# Should return:
# {"status": "healthy", "version": "0.1.0", ...}
```

---

## 💾 Backup & Recovery

### Backup Local Database
```bash
# Before making risky changes
cp data/accelerator.db data/accelerator.db.$(date +%Y%m%d_%H%M%S).backup

# Keep backups
ls -la data/*.backup
```

### Backup Production Database
**Railway:**
```bash
# Via Railway CLI
railway shell
# Then use psql to dump data
```

**Vercel with Postgres:**
```bash
# Use managed Postgres backups
# Check Vercel dashboard for backup options
```

---

## 🎓 Quick Reference

| Task | Command |
|------|---------|
| Start dev server | `uvicorn app.main:app --host localhost --port 8787 --reload` |
| Make changes | Edit files (auto-reload with --reload flag) |
| Commit | `git add . && git commit -m "message"` |
| Deploy | `git push origin main` |
| Check status | `git status` |
| View history | `git log --oneline` |
| Undo changes | `git checkout .` |
| See what changed | `git diff` |

---

## 🚀 Ready to Make Changes?

**Your development environment is all set up!**

Next time you want to make changes:

```bash
# 1. Navigate to project
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/claude\ projects\ /Job-Application-Accelerator

# 2. Activate virtual environment
source venv/bin/activate

# 3. Start dev server
uvicorn app.main:app --host localhost --port 8787 --reload

# 4. Open browser
open http://localhost:8787

# 5. Make changes (they auto-reload!)

# 6. When done
git add .
git commit -m "your message"
git push origin main

# 7. Auto-deploys to production!
```

That's it! Easy peasy! 🎉

---

**Version:** 1.0.0  
**Last Updated:** June 30, 2024  
**Status:** Ready for Development ✅
