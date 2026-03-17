# Render Deployment Guide - Wedding Photo App

**Date Completed**: March 17, 2026
**Live URL**: https://mike-and-sams-digital-photobook.onrender.com
**GitHub Repo**: https://github.com/gigs2265/Wedding-App

---

## Table of Contents
1. [Overview](#overview)
2. [Pre-Deployment Setup](#pre-deployment-setup)
3. [Render Configuration](#render-configuration)
4. [OAuth Token Setup (CRITICAL)](#oauth-token-setup-critical)
5. [Environment Variables](#environment-variables)
6. [Troubleshooting](#troubleshooting)
7. [QR Code Generation](#qr-code-generation)

---

## Overview

This Flask wedding photo app was successfully deployed to Render.com. The main challenge was handling OAuth tokens on Render's ephemeral filesystem.

### Key Technologies
- **Backend**: Flask (Python)
- **Hosting**: Render.com (Free Tier)
- **Storage**: Google Drive API (OAuth 2.0)
- **Version Control**: GitHub

---

## Pre-Deployment Setup

### 1. Prepare Code for Production

**Added to `requirements.txt`:**
```
gunicorn==21.2.0
```

**Modified `app.py`** to disable insecure transport in production:
```python
# Allow OAuth over HTTP for local development only
if os.getenv('FLASK_ENV') == 'development':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
```

**Created `.env.example`:**
```
SECRET_KEY=your-secret-key-change-this-in-production
DRIVE_FOLDER_ID=your_folder_id_here
```

### 2. Push to GitHub

**Commands used:**
```bash
cd "C:\Users\Owner\Documents\VSCode Projects\weddingapp"
git init
git add .
git commit -m "Initial commit - wedding photo app"
git branch -M main
git remote add origin https://github.com/gigs2265/Wedding-App.git
git push -u origin main
```

**IMPORTANT**: `.gitignore` must include:
```
credentials.json
token.json
.env
venv/
uploads/
```

**Issue Encountered**: GitHub blocked push due to `credentials_OLD_SERVICE_ACCOUNT.json.backup` containing secrets.

**Solution**:
- Removed git history: `rm -rf .git`
- Added backup file to `.gitignore`
- Re-initialized and pushed clean repo

---

## Render Configuration

### 1. Create Render Account
- Signed up at https://render.com/
- Connected GitHub account

### 2. Create Web Service

**Settings:**
| Setting | Value |
|---------|-------|
| **Name** | `mike-and-sams-digital-photobook` |
| **Repository** | `gigs2265/Wedding-App` |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT` |
| **Instance Type** | `Free` |

### 3. Add Secret Files

**Secret File Added:**
- **Filename**: `credentials.json`
- **Contents**: Full OAuth 2.0 client credentials from Google Cloud Console

---

## OAuth Token Setup (CRITICAL)

### The Problem
Render's free tier uses **ephemeral filesystem** - files written at runtime don't persist. The app tried to save `token.json` to disk, but it would disappear, causing an infinite authorization loop.

### The Solution
Store OAuth token in **environment variable** instead of file.

### Code Changes Made

**Modified `get_drive_service()` function:**
```python
def get_drive_service():
    """Initialize Google Drive service with OAuth 2.0"""
    try:
        creds = None

        # Try to load from environment variable first (for Render)
        oauth_token = os.getenv('OAUTH_TOKEN')
        if oauth_token:
            creds = Credentials.from_authorized_user_info(json.loads(oauth_token), SCOPES)
        # Fall back to token file (for local development)
        elif os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        # ... rest of function
```

**Modified `oauth2callback()` to print token:**
```python
@app.route('/oauth2callback')
def oauth2callback():
    # ... existing code ...

    credentials = flow.credentials
    token_json = credentials.to_json()

    # ALWAYS print the token for Render setup
    print("=" * 80)
    print("OAUTH TOKEN GENERATED - COPY THIS TO RENDER ENVIRONMENT VARIABLES")
    print("=" * 80)
    print(token_json)
    print("=" * 80)
```

**Modified `index()` and `check_auth()` to check environment variable first**

### Steps to Get OAuth Token

1. **Update Google OAuth Redirect URIs**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Edit OAuth 2.0 Client
   - Add: `https://mike-and-sams-digital-photobook.onrender.com/oauth2callback`

2. **Revoke Previous Access** (Important!)
   - Go to: https://myaccount.google.com/permissions
   - Find "Wedding Photo Gallery"
   - Click "Remove Access"
   - This ensures fresh authorization includes `refresh_token`

3. **Delete Old OAUTH_TOKEN from Render** (if exists)
   - Render → Environment → Delete OAUTH_TOKEN
   - Save Changes
   - Wait for redeploy

4. **Authorize App**
   - Open app in incognito: https://mike-and-sams-digital-photobook.onrender.com
   - Click "Authorize with Google"
   - Complete authorization flow
   - Click "Advanced" → "Go to Wedding Photo Gallery (unsafe)"
   - Allow permissions

5. **Copy Token from Logs**
   - Render Dashboard → Logs tab
   - Look for section between `================` lines
   - Copy entire JSON object (must include `refresh_token`)

**Example token format:**
```json
{
  "token": "ya29.a0...",
  "refresh_token": "1//01...",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "...",
  "client_secret": "...",
  "scopes": ["https://www.googleapis.com/auth/drive.file"],
  "universe_domain": "googleapis.com",
  "expiry": "2026-03-17T18:18:58Z"
}
```

**CRITICAL**: Token MUST include `"refresh_token"` field. If missing, revoke access and re-authorize.

---

## Environment Variables

**Final Render Environment Variables (4 total):**

| Variable | Value | Notes |
|----------|-------|-------|
| `SECRET_KEY` | `sk_wedding_app_2026_9f8e7d6c5b4a3210fedcba9876543210` | Random string for Flask sessions |
| `DRIVE_FOLDER_ID` | `14y2-xr69hEol2o64rqdVtG6XKm0fS55X` | Google Drive folder ID |
| `FLASK_ENV` | `production` | Disables insecure transport |
| `OAUTH_TOKEN` | `{"token":"ya29...","refresh_token":"1//01..."}` | Full OAuth JSON (see above) |

### How to Add Environment Variables in Render
1. Render Dashboard → Your Service
2. Click "Environment" tab
3. Click "Add Environment Variable"
4. Enter Key and Value
5. Click "Save Changes"
6. Render auto-redeploys

---

## Troubleshooting

### Issue: Authorization Loop (Keeps Asking to Authorize)
**Symptoms**: After authorizing, redirects back to authorization page

**Cause**:
- Missing `OAUTH_TOKEN` environment variable
- Token missing `refresh_token` field
- Incorrect `SECRET_KEY` causing session issues

**Solution**:
1. Verify `SECRET_KEY` is set in Render
2. Revoke app access at https://myaccount.google.com/permissions
3. Delete `OAUTH_TOKEN` from Render
4. Re-authorize and get fresh token with `refresh_token`
5. Add new token to Render environment variables

### Issue: "credentials.json not found"
**Cause**: Secret file not uploaded to Render

**Solution**:
1. Render → Service → Settings
2. Scroll to "Secret Files"
3. Add file: `credentials.json`
4. Paste contents from local file
5. Save

### Issue: Browser Shows Authorize Page in Regular Mode but Works in Incognito
**Cause**: Cached session cookies from before SECRET_KEY was set

**Solution**:
- Clear browser cookies (Ctrl+Shift+Delete)
- Or just use incognito for testing
- Other users won't have this issue

### Issue: GitHub Push Blocked - Secrets Detected
**Cause**: Attempting to commit files containing credentials

**Solution**:
1. Add sensitive files to `.gitignore`
2. Remove git history: `rm -rf .git`
3. Re-initialize: `git init`
4. Commit and push clean repo

### Issue: Files Not Uploading to Google Drive
**Cause**:
- Drive folder not shared with OAuth account
- Invalid `DRIVE_FOLDER_ID`
- Missing Drive API permissions

**Solution**:
1. Verify `DRIVE_FOLDER_ID` is correct
2. Check Google Drive folder exists
3. Test by uploading file through app
4. Check Render logs for errors

---

## QR Code Generation

### Steps to Create QR Code

1. **Go to**: https://www.qr-code-generator.com/

2. **Enter URL**: `https://mike-and-sams-digital-photobook.onrender.com`

3. **Customize** (optional):
   - Add frame with text: "Scan to Share Photos"
   - Match wedding colors (black/silver theme)
   - Add wedding date or names

4. **Download**: High-resolution PNG or PDF

5. **Print**:
   - Print multiple copies
   - Place at different tables/locations
   - Add text: "Share your photos with us!"

---

## Guest Experience

### What Guests See
1. Scan QR code with phone camera
2. Opens wedding photo gallery in browser
3. Click "Upload Files" or "Take Photo"
4. Select/capture photo
5. Photo uploads automatically
6. Appears in gallery immediately

### Important Notes
- ✅ **No sign-in required** for guests
- ✅ All photos upload to YOUR Google Drive
- ✅ Guests can view all shared photos
- ✅ Works on any mobile device
- ⚠️ Anyone with URL can upload (keep URL private after wedding)

---

## Maintenance

### After the Wedding

**Optional - Take Down App:**
1. Render Dashboard → Service
2. Settings → Delete Service
3. Or: Suspend service to save resources

**Keep Photos:**
- All photos are in your Google Drive
- Download folder as backup
- Photos persist even if app is deleted

### Free Tier Limitations

**Render Free Tier:**
- ⚠️ Sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake up
- **Solution**: Visit URL 10-15 minutes before wedding starts

**Storage:**
- App uses YOUR Google Drive storage
- Check available space before wedding
- Free Google accounts: 15GB

---

## Final Checklist

Before wedding day:

- [ ] Test upload from mobile device
- [ ] Verify photos appear in Google Drive
- [ ] Generate and print QR codes
- [ ] Test QR code scanning
- [ ] Visit app URL to wake it up (15 min before wedding)
- [ ] Check Google Drive storage space
- [ ] Have backup plan (printed instructions if app has issues)

---

## Technical Architecture

```
Guest Device
    ↓ (scans QR code)
    ↓
Render.com (Flask App)
    ↓ (OAuth 2.0 from env var)
    ↓
Google Drive API
    ↓
Your Google Drive Folder
```

**Key Innovation**: OAuth token stored in environment variable instead of ephemeral filesystem.

---

## Deployment Summary

**Total Time**: ~3 hours (including troubleshooting)

**Main Challenges**:
1. GitHub blocking secrets in commit
2. Render ephemeral filesystem preventing token persistence
3. OAuth token missing refresh_token on re-authorization
4. Session issues from incorrect SECRET_KEY

**Final Result**: ✅ Fully functional wedding photo gallery accessible via QR code

---

## Contact & Support

**Repository**: https://github.com/gigs2265/Wedding-App
**Render Docs**: https://render.com/docs/web-services
**Google OAuth Docs**: https://developers.google.com/identity/protocols/oauth2

---

*Generated: March 17, 2026*
*App Status: Live and Working*
*Wedding: Mike & Sam* 💍
