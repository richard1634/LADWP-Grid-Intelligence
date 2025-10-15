# 🚀 Deployment Guide - LADWP Grid Intelligence Dashboard

This guide will help you deploy your LADWP dashboard online using various platforms.

---

## 📋 Prerequisites

1. **GitHub Account** - Your code should be pushed to GitHub
2. **Deployment Platform Account** - Choose one:
   - Render (recommended for beginners)
   - Railway
   - Vercel (frontend) + Render (backend)

---

## 🎯 Recommended: Deploy on Render (Full Stack)

### Step 1: Deploy Backend (FastAPI)

1. **Go to [Render.com](https://render.com)** and sign up/login

2. **Click "New +" → "Web Service"**

3. **Connect Your GitHub Repository**
   - Repository: `richard1634/LADWP-Grid-Intelligence`
   - Branch: `main`

4. **Configure the Service:**
   ```
   Name: ladwp-api
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn api_server:app --host 0.0.0.0 --port $PORT
   ```

5. **Environment Variables** (click "Advanced"):
   ```
   PORT=10000
   PYTHON_VERSION=3.11.0
   ```
   
   Optional (if using OpenAI):
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

6. **Select Plan:**
   - Free tier is fine for testing
   - Paid tier ($7/month) for production

7. **Click "Create Web Service"**

8. **Wait for deployment** (~5-10 minutes)
   - You'll get a URL like: `https://ladwp-api.onrender.com`

### Step 2: Deploy Frontend (React)

1. **In Render, click "New +" → "Static Site"**

2. **Connect Same Repository**
   - Repository: `richard1634/LADWP-Grid-Intelligence`
   - Branch: `main`

3. **Configure:**
   ```
   Name: ladwp-dashboard
   Root Directory: frontend
   Build Command: npm install && npm run build
   Publish Directory: frontend/dist
   ```

4. **Environment Variables:**
   ```
   VITE_API_URL=https://ladwp-api.onrender.com
   ```
   ⚠️ **Important**: Use YOUR backend URL from Step 1!

5. **Click "Create Static Site"**

6. **Wait for deployment** (~3-5 minutes)
   - You'll get a URL like: `https://ladwp-dashboard.onrender.com`

### Step 3: Test Your Deployment

1. Visit your frontend URL
2. Check that data loads properly
3. Test both tabs (Demand & AI, Price Analysis)
4. Verify ML predictions appear

---

## 🌐 Alternative: Deploy on Railway

### Backend Deployment

1. **Go to [Railway.app](https://railway.app)** and login with GitHub

2. **Click "New Project" → "Deploy from GitHub repo"**

3. **Select `LADWP-Grid-Intelligence`**

4. **Configure:**
   - Click "Add Variables"
   - Add: `PORT=8000`
   - Add: `PYTHON_VERSION=3.11`
   - Optional: `OPENAI_API_KEY=your-key`

5. **Settings → Generate Domain**
   - You'll get: `https://your-app.up.railway.app`

### Frontend Deployment

1. **In Railway, click "New" → "GitHub Repo"**

2. **Select same repository**

3. **Settings:**
   - Root Directory: `/frontend`
   - Build Command: `npm install && npm run build`
   - Start Command: `npm run preview`

4. **Variables:**
   - `VITE_API_URL=https://your-backend.up.railway.app`

5. **Generate Domain**

---

## ⚡ Alternative: Vercel (Frontend) + Render (Backend)

### Backend on Render
Follow "Step 1" from Render section above

### Frontend on Vercel

1. **Go to [Vercel.com](https://vercel.com)** and login with GitHub

2. **Click "Add New" → "Project"**

3. **Import `LADWP-Grid-Intelligence`**

4. **Configure:**
   ```
   Framework Preset: Vite
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: dist
   ```

5. **Environment Variables:**
   ```
   VITE_API_URL=https://your-render-backend.onrender.com
   ```

6. **Click "Deploy"**

7. **You'll get**: `https://ladwp-dashboard.vercel.app`

---

## 🔧 Post-Deployment Configuration

### Update CORS Settings

After deployment, update `api_server.py` CORS origins:

```python
# In api_server.py, update:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://your-frontend-url.onrender.com",  # Add your actual URL
        "https://your-frontend-url.vercel.app",    # Or Vercel URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push changes:
```bash
git add api_server.py
git commit -m "Update CORS for production deployment"
git push origin main
```

### Set Up Custom Domain (Optional)

**Render:**
- Settings → Custom Domain → Add your domain
- Update DNS records as instructed

**Vercel:**
- Project Settings → Domains → Add domain
- Follow DNS configuration

---

## 📊 Monitoring & Maintenance

### Check Logs

**Render:**
- Dashboard → Your Service → Logs tab
- Real-time log streaming

**Railway:**
- Click on service → View Logs
- Real-time monitoring

**Vercel:**
- Project → Deployments → View Function Logs

### Auto-Deploy on Git Push

All platforms support automatic deployment:
- Push to `main` branch
- Platform automatically rebuilds and deploys
- Zero downtime deployments

---

## 🐛 Troubleshooting

### Backend Issues

**"Application failed to start"**
```bash
# Check requirements.txt is correct
# Verify Python version in runtime.txt
# Check logs for missing dependencies
```

**"Port binding failed"**
```python
# Use $PORT environment variable
uvicorn api_server:app --host 0.0.0.0 --port $PORT
```

### Frontend Issues

**"API calls failing"**
- Verify `VITE_API_URL` points to deployed backend
- Check CORS settings in backend
- Open browser console for errors

**"Build failed"**
```bash
# Check package.json scripts
# Verify all dependencies in package.json
# Check for TypeScript errors
```

### Database Issues

**"Cannot find ladwp_grid_data.db"**
- SQLite databases need to be committed to git
- Or use PostgreSQL for production (recommended)
- Consider using Render's PostgreSQL addon

---

## 🎯 Production Checklist

Before going live:

- [ ] Update CORS origins with production URLs
- [ ] Set environment variables on hosting platform
- [ ] Test all API endpoints
- [ ] Test both dashboard tabs
- [ ] Verify ML predictions load
- [ ] Check mobile responsiveness
- [ ] Set up error monitoring (optional: Sentry)
- [ ] Configure custom domain (optional)
- [ ] Set up SSL certificate (automatic on most platforms)
- [ ] Test with different browsers
- [ ] Create backup of database

---

## 💰 Cost Estimates

### Free Tier (Good for Portfolio/Demo)
- **Render Free**: $0/month (sleeps after inactivity)
- **Vercel Free**: $0/month (generous limits)
- **Railway Free**: $5 credit/month

### Production Tier
- **Render Starter**: $7/month per service ($14 total)
- **Vercel Pro**: $20/month
- **Railway Pro**: $5/month + usage

---

## 🚀 Quick Start Commands

After setting up on chosen platform:

```bash
# Update frontend API URL
cd frontend
echo "VITE_API_URL=https://your-backend-url.com" > .env

# Test build locally
npm install
npm run build
npm run preview

# Backend test
cd ..
pip install -r requirements.txt
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

---

## 📞 Support

If you encounter issues:

1. Check platform documentation:
   - [Render Docs](https://render.com/docs)
   - [Railway Docs](https://docs.railway.app)
   - [Vercel Docs](https://vercel.com/docs)

2. Check logs on your platform dashboard

3. Review this guide's troubleshooting section

---

## 🎉 You're Ready to Deploy!

Choose your preferred platform above and follow the step-by-step instructions. Your dashboard will be live in ~15 minutes!

**Recommended for beginners:** Start with Render (full stack) - it's the simplest option.
