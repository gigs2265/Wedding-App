# OAuth 2.0 Setup Guide

Your app has been updated to use **OAuth 2.0** authentication instead of service accounts. This means it will use YOUR personal Google account to upload files to YOUR Google Drive!

## Why This Works Better

✅ Works with personal Gmail accounts (no Workspace needed)
✅ Uses your own Drive storage
✅ No complicated sharing/permissions
✅ One-time authorization process
✅ More secure and straightforward

---

## Step 1: Delete Old Service Account Credentials

The old `credentials.json` file is for service accounts and won't work anymore. You need to replace it with OAuth credentials.

**In VS Code, delete the file:**
- Right-click `credentials.json` → Delete

Or in terminal:
```bash
del credentials.json
```

---

## Step 2: Set Up OAuth 2.0 Credentials in Google Cloud

### A. Go to Google Cloud Console
1. Visit: https://console.cloud.google.com/
2. Make sure your project is selected (should be "gen-lang-client-0476379631" or your project name)

### B. Configure OAuth Consent Screen
1. Click **☰** menu → **APIs & Services** → **OAuth consent screen**
2. Select **External** (for personal Gmail)
3. Click **Create**

4. Fill in the form:
   - **App name:** Wedding Photo Gallery
   - **User support email:** Your email address
   - **Developer contact:** Your email address
   - Leave everything else blank
5. Click **Save and Continue**

6. **Scopes page:** Click **Save and Continue** (skip this)

7. **Test users page:**
   - Click **+ ADD USERS**
   - Add your own Gmail address (the one you'll use)
   - Click **Save and Continue**

8. Click **Back to Dashboard**

### C. Create OAuth 2.0 Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Application type: **Web application**
4. Name: **Wedding App**

5. **Authorized redirect URIs** - Click **+ ADD URI** and add:
   ```
   http://localhost:5000/oauth2callback
   ```

   **IMPORTANT:** If you plan to deploy to a live server, also add:
   ```
   https://your-app-domain.com/oauth2callback
   ```
   (Replace with your actual domain when you deploy)

6. Click **Create**

7. A popup will show your Client ID and Client Secret:
   - Click **DOWNLOAD JSON**
   - This downloads a file like `client_secret_xxx.json`

8. **Rename the downloaded file to `credentials.json`**

9. **Move it to your project folder:**
   ```
   C:\Users\Owner\Documents\VSCode Projects\weddingapp\
   ```

---

## Step 3: Test the App Locally

Now you're ready to test!

### A. Start the App
1. Open terminal in VS Code (`` Ctrl + ` ``)
2. Make sure virtual environment is activated:
   ```bash
   venv\Scripts\activate
   ```
3. Run the app:
   ```bash
   python app.py
   ```

### B. Authorize the App
1. Open browser and go to: http://localhost:5000
2. You'll see an "Authorization Required" page
3. Click **"Authorize with Google"**
4. You'll be redirected to Google
5. **Sign in** with your Google account
6. Google will show a warning: "Google hasn't verified this app"
   - Click **"Advanced"**
   - Click **"Go to Wedding Photo Gallery (unsafe)"** (it's safe, it's your own app!)
7. Click **"Allow"** to grant permissions
8. You'll be redirected back to your app
9. **The wedding photo gallery should now load!**

### C. Test Upload
1. Click **"Upload Files"** or **"Take Photo"**
2. Upload a test photo
3. Check your **Google Drive** - the photo should appear there!
4. The gallery should display the uploaded photo

---

## Step 4: Understanding What Happened

After authorization:
- A `token.json` file was created in your project folder
- This file stores your access credentials
- The app will use this token automatically from now on
- **You don't need to authorize again** (unless you delete token.json)

---

## Troubleshooting

### "credentials.json not found"
- Did you download the OAuth credentials from Google Cloud?
- Did you rename it to exactly `credentials.json`?
- Is it in the project folder?

### "Redirect URI mismatch" error
- Go back to Google Cloud Console → Credentials
- Edit your OAuth client
- Make sure `http://localhost:5000/oauth2callback` is in the Authorized redirect URIs list
- Click Save
- Try again

### "Access blocked: This app's request is invalid"
- Make sure you added yourself as a test user in the OAuth consent screen
- Go to OAuth consent screen → Test users → Add your email

### Google says "This app isn't verified"
- This is normal for personal projects
- Click "Advanced" → "Go to Wedding Photo Gallery (unsafe)"
- This is safe because it's YOUR app

### Files not appearing in specific folder
- The DRIVE_FOLDER_ID in .env is optional
- If set, files upload to that folder
- If blank, files upload to your Drive root
- You can change this anytime

---

## Next Steps

✅ **Local testing works?** Great!

Now you can:
1. **Test on mobile** (same WiFi):
   - Get your computer's IP: `ipconfig`
   - Open `http://YOUR_IP:5000` on phone
   - Should work without re-authorizing!

2. **Deploy for wedding:**
   - See deployment section in README.md
   - **IMPORTANT:** When deploying, you need to:
     - Add your live domain to OAuth redirect URIs
     - Upload `token.json` to the server (or authorize again on server)

---

## Security Notes

- **token.json** contains your access token - keep it secret!
- It's already in `.gitignore` so it won't be committed to git
- If you ever feel the token is compromised, just delete it and authorize again
- For production, change the SECRET_KEY in `.env` to something random

---

## Summary

The OAuth flow only happens **once**:
1. First time: You authorize with Google
2. `token.json` is created
3. All future visits: App uses the token automatically
4. No more authorization needed!

**Ready to test? Follow Step 3 above!**
