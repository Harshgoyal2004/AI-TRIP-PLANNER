# 🚀 Quick Deployment Steps

## For Render (Backend)

**Start Command (what you asked for):**
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Step-by-Step:

### 1️⃣ Deploy Backend to Render

1. Go to [render.com](https://render.com) and sign in
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo: `AI_Trip_Planner`
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
5. Add Environment Variables (in Render dashboard):
   ```
   GROQ_API_KEY
   OPENWEATHERMAP_API_KEY
   EXCHANGE_RATE_API_KEY
   GPLACES_API_KEY
   TAVILY_API_KEY
   OPENAI_API_KEY (optional)
   ```
6. Click **"Create Web Service"**
7. **Copy your backend URL** (e.g., `https://ai-trip-planner-backend.onrender.com`)

### 2️⃣ Update Streamlit Frontend

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Find your app: `harsh-ai-trip-planner`
3. Go to **Settings** → **Secrets**
4. Add:
   ```toml
   BACKEND_URL = "https://your-backend-url.onrender.com"
   ```
   (Replace with your actual Render URL from step 1)
5. Save and wait for redeployment

### 3️⃣ Push Changes to GitHub

```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

### 4️⃣ Test

Visit: https://harsh-ai-trip-planner.streamlit.app

---

## That's it! 🎉

Your app should now be fully deployed and working.

**Note**: First request may take 30-60 seconds (cold start on free tier).

---

## Files Created:
- ✅ `Dockerfile` - For containerization
- ✅ `.dockerignore` - Excludes unnecessary files
- ✅ `render.yaml` - Render configuration
- ✅ `DEPLOYMENT.md` - Full deployment guide
- ✅ Updated `main.py` - Cloud-ready
- ✅ Updated `streamlit_app.py` - Environment variable support
- ✅ Updated `requirements.txt` - Production-ready
