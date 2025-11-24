# 🚀 Deployment Guide

## Backend Deployment (Render)

### Option 1: Using Render Dashboard (Recommended)

1. **Create a Render Account**
   - Go to [render.com](https://render.com) and sign up

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `AI_Trip_Planner` repository

3. **Configure the Service**
   - **Name**: `ai-trip-planner-backend`
   - **Region**: Oregon (or closest to you)
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

4. **Add Environment Variables**
   Go to "Environment" tab and add:
   ```
   GROQ_API_KEY=your_groq_api_key
   OPENWEATHERMAP_API_KEY=your_weather_api_key
   EXCHANGE_RATE_API_KEY=your_exchange_rate_key
   GPLACES_API_KEY=your_google_places_key
   TAVILY_API_KEY=your_tavily_key
   OPENAI_API_KEY=your_openai_key (optional)
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Copy your backend URL (e.g., `https://ai-trip-planner-backend.onrender.com`)

### Option 2: Using render.yaml (Blueprint)

1. Push the `render.yaml` file to your repository
2. Go to Render Dashboard → "Blueprints" → "New Blueprint Instance"
3. Connect your repository
4. Add environment variables manually
5. Deploy

---

## Frontend Deployment (Streamlit Cloud)

### Update Streamlit App Configuration

1. **Go to Streamlit Cloud Dashboard**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Find your app: `harsh-ai-trip-planner`

2. **Add Environment Variable**
   - Click on your app → Settings → Secrets
   - Add the following in the secrets.toml format:
   ```toml
   BACKEND_URL = "https://your-backend-url.onrender.com"
   ```
   Replace with your actual Render backend URL

3. **Update Code** (Already done)
   - The `streamlit_app.py` now reads from `BACKEND_URL` environment variable
   - Commit and push changes to trigger redeployment

4. **Verify Deployment**
   - Visit https://harsh-ai-trip-planner.streamlit.app
   - Test with a query like "Plan a 3-day trip to Paris"

---

## Alternative Deployment Platforms

### Railway
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Fly.io
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly deploy
```

### Heroku
```bash
# Create Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create ai-trip-planner-backend
git push heroku main
```

---

## Local Testing

Before deploying, test locally:

```bash
# Terminal 1: Start backend
python main.py

# Terminal 2: Start frontend
streamlit run streamlit_app.py
```

---

## Troubleshooting

### Backend Issues
- **Port binding error**: Ensure `--host 0.0.0.0` is used
- **Module not found**: Check `requirements.txt` has all dependencies
- **API key errors**: Verify all environment variables are set

### Frontend Issues
- **Connection refused**: Check `BACKEND_URL` is correct
- **CORS errors**: Ensure backend allows frontend origin in CORS settings

### Performance
- **Slow responses**: Free tier has cold starts (30s-1min)
- **Rate limits**: Add caching for API calls

---

## Production Checklist

- [ ] All API keys added to environment variables
- [ ] CORS configured for production frontend URL
- [ ] Backend URL updated in Streamlit secrets
- [ ] Test end-to-end flow
- [ ] Monitor logs for errors
- [ ] Set up custom domain (optional)

---

## Monitoring

### Render
- View logs: Dashboard → Your Service → Logs
- Monitor metrics: Dashboard → Metrics

### Streamlit
- View logs: Streamlit Cloud → App → Logs
- Check analytics: Streamlit Cloud → Analytics

---

## Cost Optimization

**Free Tier Limits:**
- Render: 750 hours/month, sleeps after 15min inactivity
- Streamlit: Unlimited public apps

**Tips:**
- Use caching for API responses
- Implement rate limiting
- Consider upgrading for production use
