# Concurrent Upload Upgrade Guide

## Current Situation
- **Workers**: 1 synchronous worker
- **Concurrent uploads**: 1 at a time (others queue)
- **Suitable for**: 10-20 guests

## After Upgrade
- **Workers**: 2 async workers with gevent
- **Concurrent uploads**: ~100 simultaneous connections
- **Suitable for**: 50-100+ guests uploading at once

---

## How to Upgrade on Render

### Step 1: Update Code on GitHub

1. **Commit the new files** to your GitHub repo:
   - `gunicorn_config.py` (new)
   - `requirements.txt` (updated with gevent)

2. **Push to GitHub**:
   ```bash
   git add gunicorn_config.py requirements.txt
   git commit -m "Add concurrent upload support with gevent workers"
   git push
   ```

### Step 2: Update Render Build Command

1. Go to **Render Dashboard**
2. Select your app: **mike-and-sams-digital-photobook**
3. Click **Settings** tab
4. Find **"Start Command"**
5. Change it from:
   ```
   gunicorn app:app --bind 0.0.0.0:$PORT
   ```
   To:
   ```
   gunicorn app:app -c gunicorn_config.py
   ```
6. Click **Save Changes**
7. Render will automatically redeploy

### Step 3: Test

After redeployment:
- Have 3-5 people try uploading photos at the same time
- All uploads should proceed simultaneously
- No more waiting in queue

---

## Performance Comparison

### Before (Current):
```
Guest 1: Upload starts → 10 seconds → Complete
Guest 2: Waits → Upload starts → 10 seconds → Complete
Guest 3: Waits 20s → Upload starts → 10 seconds → Complete
Total time: 30 seconds
```

### After (With Upgrade):
```
Guest 1: Upload starts → 10 seconds → Complete
Guest 2: Upload starts → 10 seconds → Complete
Guest 3: Upload starts → 10 seconds → Complete
Total time: 10 seconds (all parallel)
```

---

## Alternative: Upgrade to Paid Tier

If you want even more capacity:

### Render Starter Plan ($7/month)
- More CPU and RAM
- Can run 4+ workers
- Handle 200+ concurrent uploads
- No cold starts (faster response)

**To upgrade:**
1. Render Dashboard → Billing
2. Upgrade to "Starter" plan
3. Update `gunicorn_config.py`:
   ```python
   workers = 4
   worker_connections = 100
   ```

---

## What Files Were Changed?

✅ **gunicorn_config.py** (NEW)
- Configures 2 gevent workers
- 50 connections per worker
- 5-minute timeout for large uploads

✅ **requirements.txt** (UPDATED)
- Added: `gevent==24.2.1`

---

## Do I Need to Do This?

**You're probably fine without it if:**
- Small/medium wedding (under 30 guests)
- Guests upload throughout the evening (not all at once)
- You're okay with occasional 30-60 second delays

**You should upgrade if:**
- Large wedding (50+ guests)
- Expecting lots of simultaneous uploads
- Want instant upload response for everyone
- Plan to reuse this for other events

---

## Questions?

The current setup works fine for most weddings. The upgrade is optional but recommended for larger events or if you notice upload delays during testing.
