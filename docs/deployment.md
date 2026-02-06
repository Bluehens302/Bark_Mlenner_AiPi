# Deployment Guide

This guide covers deploying the Molecular Biology Tools API to various platforms.

## Prerequisites

- GitHub account
- API code in a GitHub repository
- Python 3.9+ installed locally for testing

## Option 1: Render (Recommended - Free Tier Available)

Render offers a free tier perfect for this API.

### Steps:

1. **Push code to GitHub**
   ```bash
   cd /home/hris/Bark_Mlenner_AiPi
   git add .
   git commit -m "Add API and Google Apps Script"
   git push origin main
   ```

2. **Create Render account**
   - Go to https://render.com
   - Sign up with GitHub

3. **Create new Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `Bluehens302/Bark_Mlenner_AiPi`
   - Configure:
     - **Name**: `molbio-tools-api`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `cd api && uvicorn main:app --host 0.0.0.0 --port $PORT`
     - **Instance Type**: Free

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Copy your URL: `https://molbio-tools-api.onrender.com`

5. **Verify deployment**
   ```bash
   curl https://molbio-tools-api.onrender.com/
   ```

### Notes:
- Free tier spins down after inactivity (may have cold start delays)
- Upgrade to paid tier ($7/month) for always-on service

## Option 2: Google Cloud Run

Serverless, auto-scaling deployment.

### Steps:

1. **Install Google Cloud SDK**
   ```bash
   curl https://sdk.cloud.google.com | bash
   gcloud init
   ```

2. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   EXPOSE 8080

   CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
   ```

3. **Build and deploy**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/molbio-api
   gcloud run deploy molbio-api \
     --image gcr.io/YOUR_PROJECT_ID/molbio-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

4. **Get URL**
   ```bash
   gcloud run services describe molbio-api --region us-central1 --format 'value(status.url)'
   ```

### Pricing:
- Free tier: 2 million requests/month
- Pay only for actual usage

## Option 3: Railway

Simple deployment with generous free tier.

### Steps:

1. **Create Railway account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create new project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `Bark_Mlenner_AiPi`

3. **Configure**
   Railway auto-detects Python and requirements.txt

   Add environment variable if needed:
   - Click "Variables"
   - Add: `PORT=8000`

4. **Deploy**
   - Automatic deployment on push
   - Copy your URL from dashboard

## Option 4: Local Deployment (Development Only)

For testing purposes only.

### Steps:

1. **Install dependencies**
   ```bash
   cd /home/hris/Bark_Mlenner_AiPi
   pip install -r requirements.txt
   ```

2. **Run API**
   ```bash
   cd api
   python main.py
   ```

3. **Access API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

### Limitations:
- Not accessible from Google Apps Script (unless using ngrok)
- Only available while your computer is on

### Using ngrok for testing:
```bash
# Install ngrok: https://ngrok.com/
ngrok http 8000

# Copy the HTTPS URL and use in Google Apps Script
```

## Post-Deployment Setup

### 1. Update Google Apps Script

Edit `api/google_apps_script.js`:

```javascript
const CONFIG = {
  API_BASE_URL: 'https://your-deployed-url.com',  // ← UPDATE THIS
  ...
};
```

### 2. Test API Endpoints

```bash
# Test root endpoint
curl https://your-deployed-url.com/

# Test PCR calculation
curl -X POST https://your-deployed-url.com/pcr/annealing-temp \
  -H "Content-Type: application/json" \
  -d '{
    "forward_primer": "ATCGATCGATCGATCGATCG",
    "reverse_primer": "GCTAGCTAGCTAGCTAGCTA",
    "pcr_type": "OneTaq"
  }'
```

### 3. Test from Google Apps Script

1. Open your Google Doc
2. Reload to load the menu
3. Try running a calculation
4. Check Apps Script logs if errors occur:
   - Extensions → Apps Script
   - View → Logs

## Monitoring & Maintenance

### Check API Health
```bash
curl https://your-deployed-url.com/
```

### View Logs
- **Render**: Dashboard → Logs tab
- **Cloud Run**: Cloud Console → Cloud Run → Logs
- **Railway**: Dashboard → Deploy logs

### Update Deployment

When you push changes to GitHub:
- **Render**: Auto-deploys on push (if enabled)
- **Cloud Run**: Run deploy command again
- **Railway**: Auto-deploys on push

## Troubleshooting

### API not responding
1. Check deployment logs
2. Verify PORT environment variable
3. Check CORS settings in `api/main.py`

### Google Apps Script can't reach API
1. Verify API URL is correct
2. Check API is publicly accessible
3. Test with curl first
4. Check Apps Script logs for errors

### Import errors
1. Verify all dependencies in requirements.txt
2. Check Python version compatibility
3. Review deployment logs for install errors

### CORS errors
The API is configured to allow all origins. If you encounter CORS issues:
1. Check browser console for error details
2. Verify API is returning proper headers
3. In production, restrict to specific domains

## Security Considerations

### Production Recommendations:
1. **Restrict CORS** - Update `allow_origins` in `api/main.py` to specific domains
2. **Add authentication** - Implement API keys or OAuth
3. **Rate limiting** - Add rate limiting to prevent abuse
4. **HTTPS only** - All deployment options provide HTTPS by default
5. **Input validation** - Already implemented via Pydantic models
6. **Logging** - Add logging for monitoring and debugging

### Example: Adding API Key Authentication

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header()):
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.post("/pcr/annealing-temp", dependencies=[Depends(verify_api_key)])
async def calculate_annealing_temp(primer_pair: PrimerPair):
    # ... existing code
```

## Costs

| Platform | Free Tier | Paid Tier |
|----------|-----------|-----------|
| Render | ✅ Yes (sleeps after inactivity) | $7/month (always on) |
| Google Cloud Run | ✅ 2M requests/month | Pay per use |
| Railway | ✅ $5 credit/month | Pay per use |
| Heroku | ❌ No free tier | $7/month minimum |

## Support

For deployment issues:
- Check platform documentation
- Review deployment logs
- Test locally first
- Check GitHub Issues for this project
