# 🚀 Render Deployment Guide - Quick Start

## ✅ Prerequisites Checklist

Your repository is now ready to deploy! Here's what's configured:

- ✅ `render.yaml` - Blueprint for automatic deployment
- ✅ `runtime.txt` - Python 3.11.9 specified
- ✅ `requirements.txt` - All dependencies listed
- ✅ `build.sh` - Build script for backend
- ✅ `frontend/.env.production` - Frontend environment config
- ✅ CORS configured in `api_server.py`

---

## 🎯 Deploy to Render (Step-by-Step)

### Step 1: Push to GitHub

Make sure all changes are committed and pushed:

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended)

### Step 3: Deploy Backend API

1. **In Render Dashboard:**
   - Click "New +" → "Web Service"

2. **Connect Repository:**
   - Select `richard1634/LADWP-Grid-Intelligence`
   - Click "Connect"

3. **Configure Service:**
   ```
   Name: ladwp-api
   Region: Oregon (US West) or closest to you
   Branch: main
   Runtime: Python 3
   Build Command: ./build.sh
   Start Command: uvicorn api_server:app --host 0.0.0.0 --port $PORT
   ```

4. **Environment Variables:**
   - Click "Advanced" → "Add Environment Variable"
   - Add these:
     ```
     PYTHON_VERSION = 3.11.9
     PORT = 10000
     ```
   
   - **Optional** (if using AI features):
     ```
     OPENAI_API_KEY = your-key-here
     ```

5. **Select Plan:**
   - Choose "Free" for testing (sleeps after 15 min inactivity)
   - Choose "Starter" ($7/mo) for production (always on)

6. **Click "Create Web Service"**

7. **Wait for Build** (5-10 minutes)
   - Watch the logs
   - You'll get a URL like: `https://ladwp-api.onrender.com`
   - **SAVE THIS URL!** You need it for the frontend

8. **Test Backend:**
   - Visit: `https://your-backend-url.onrender.com/`
   - Should see: `{"message": "LADWP Grid Intelligence API is running"}`
   - Test API: `https://your-backend-url.onrender.com/api/dashboard`

### Step 4: Deploy Frontend

1. **In Render Dashboard:**
   - Click "New +" → "Static Site"

2. **Connect Same Repository:**
   - Select `richard1634/LADWP-Grid-Intelligence`

3. **Configure:**
   ```
   Name: ladwp-dashboard
   Branch: main
   Root Directory: frontend
   Build Command: npm install && npm run build
   Publish Directory: dist
   ```

4. **Environment Variables:**
   ```
   VITE_API_URL = https://ladwp-api.onrender.com
   ```
   ⚠️ **Replace with YOUR actual backend URL from Step 3!**

5. **Click "Create Static Site"**

6. **Wait for Build** (3-5 minutes)
   - You'll get: `https://ladwp-dashboard.onrender.com`

### Step 5: Update CORS (Important!)

After getting your frontend URL, update the backend CORS:

1. Edit `api_server.py` line 36:
   ```python
   allow_origins=[
       "http://localhost:3000", 
       "http://localhost:5173", 
       "https://ladwp-dashboard.onrender.com",  # Add your actual URL
       "https://*.onrender.com",
       "https://*.vercel.app"
   ],
   ```

2. Commit and push:
   ```bash
   git add api_server.py
   git commit -m "Update CORS with production URL"
   git push origin main
   ```

3. Render will auto-redeploy backend (~2 minutes)

### Step 6: Test Your Live App! 🎉

1. Visit your frontend URL: `https://ladwp-dashboard.onrender.com`
2. Check both tabs load data
3. Verify charts and predictions appear
4. Test on mobile devices

---

## 🔧 One-Click Deploy (Alternative Method)

If using `render.yaml`:

1. Go to [render.com/dashboard](https://render.com/dashboard)
2. Click "New +" → "Blueprint"
3. Connect your GitHub repo
4. Render will automatically detect `render.yaml`
5. Click "Apply" - both services deploy together!

---

## 📊 Post-Deployment

### Monitor Your Services

**Backend Logs:**
- Dashboard → ladwp-api → Logs tab
- Real-time error tracking

**Frontend Logs:**
- Dashboard → ladwp-dashboard → Logs tab

### Auto-Deploy on Git Push

Render automatically deploys when you push to `main`:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

Wait 2-5 minutes for redeployment.

### Free Tier Limitations

- **Backend sleeps after 15 min inactivity**
  - First request after sleep takes ~30 seconds
  - Upgrade to Starter ($7/mo) for always-on

- **Monthly limits:**
  - 750 hours/month free
  - 100 GB bandwidth

---

## 🐛 Troubleshooting

### Backend won't start

**Check logs for:**
```
ModuleNotFoundError
```
**Fix:** Add missing package to `requirements.txt`

**Check for:**
```
Port binding error
```
**Fix:** Make sure using `$PORT` variable in start command

### Frontend can't connect to backend

**Check:**
1. Backend is running (visit backend URL directly)
2. `VITE_API_URL` points to correct backend URL
3. CORS includes your frontend URL
4. No typos in URLs

**Browser Console shows CORS error:**
- Update `api_server.py` CORS settings
- Push changes to trigger redeploy

### Data not loading

**Check backend logs:**
- Look for 404 or 500 errors
- Verify database files exist
- Check `data/` directory is committed to git

---

## 💰 Cost Summary

### Free Tier (Good for Portfolio)
- Both services: **$0/month**
- Backend sleeps after 15 min
- Limited bandwidth

### Production Tier
- Backend Starter: **$7/month** (always on)
- Frontend: **Free** (static sites are free)
- Total: **$7/month**

### Upgrade Later
Start free, upgrade backend to Starter when needed:
- Dashboard → ladwp-api → Settings → Plan
- Change to "Starter"

---

## 🎯 Quick Commands Reference

```bash
# Push changes
git add .
git commit -m "Your message"
git push origin main

# Test backend locally
uvicorn api_server:app --reload

# Test frontend locally
cd frontend
npm run dev

# Build frontend locally
cd frontend
npm run build
npm run preview
```

---

## ✅ Final Checklist

Before sharing your live app:

- [ ] Backend deploys successfully
- [ ] Frontend deploys successfully
- [ ] Both services communicate correctly
- [ ] All tabs load data
- [ ] Charts render properly
- [ ] Mobile view works
- [ ] CORS configured correctly
- [ ] Error tracking in logs
- [ ] Tested on different browsers

---

## 🎉 You're Live!

Your URLs:
- **Frontend:** `https://ladwp-dashboard.onrender.com`
- **API:** `https://ladwp-api.onrender.com`

Share your dashboard and update your resume! 🚀

---

## 📞 Need Help?

- [Render Documentation](https://render.com/docs)
- [Render Community Forum](https://community.render.com)
- Check logs in Render dashboard
- Review error messages carefully

---

**Deployment Time:** ~15 minutes total
**Cost:** Free to start
**Maintenance:** Auto-deploy on git push
