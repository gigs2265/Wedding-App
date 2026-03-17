# Quick Start Guide

## What's Been Done ✅

Your project is fully set up with:
- All code files created
- Python virtual environment configured
- All dependencies installed
- Project structure ready

## What You Need to Do Next

### STEP 1: Set Up Google Drive API (15 minutes)

This is the most important step! Follow these instructions carefully:

1. **Open this link in your browser:**
   https://console.cloud.google.com/

2. **Create a new project:**
   - Click "Select a project" → "New Project"
   - Name: "Wedding Photos"
   - Click "Create"

3. **Enable Google Drive API:**
   - Make sure your project is selected (check top left)
   - Click "☰" menu → "APIs & Services" → "Library"
   - Search: "Google Drive API"
   - Click it → Click "Enable"

4. **Create Service Account:**
   - Go to "APIs & Services" → "Credentials"
   - Click "+ CREATE CREDENTIALS" → "Service Account"
   - Name: wedding-uploader
   - Click "CREATE AND CONTINUE"
   - Role: Select "Editor"
   - Click "CONTINUE" → "DONE"

5. **Download Credentials:**
   - Click on the service account you just created
   - Go to "KEYS" tab
   - Click "ADD KEY" → "Create new key"
   - Select "JSON"
   - Click "CREATE"
   - **A file will download!**

6. **Move the downloaded file:**
   - Find the downloaded JSON file (probably in Downloads folder)
   - **Rename it to:** `credentials.json`
   - **Move it to:** `C:\Users\Owner\Documents\VSCode Projects\weddingapp\`
   - It should be in the same folder as app.py

7. **Create Drive Folder & Share It:**
   - Go to drive.google.com
   - Create a new folder (name it "Wedding Photos")
   - Right-click the folder → "Share"
   - **IMPORTANT:** Open your `credentials.json` file
   - Find the "client_email" (looks like: xxxxx@xxxxx.iam.gserviceaccount.com)
   - Copy that email address
   - Paste it in the Share dialog
   - Give it "Editor" access
   - Click "Share"

8. **Get Folder ID:**
   - Open your "Wedding Photos" folder in Drive
   - Look at the URL in your browser
   - It looks like: `https://drive.google.com/drive/folders/LONG_ID_HERE`
   - Copy the LONG_ID_HERE part

9. **Update .env file:**
   - Open `.env` file in your project
   - Replace `your_folder_id_here` with the ID you copied
   - Save the file

### STEP 2: Test It Locally (5 minutes)

1. **Open VS Code:**
   - File → Open Folder
   - Select: `C:\Users\Owner\Documents\VSCode Projects\weddingapp`

2. **Open Terminal in VS Code:**
   - Press `Ctrl + `` (backtick key below Esc)

3. **Activate virtual environment:**
   ```bash
   venv\Scripts\activate
   ```

4. **Run the app:**
   ```bash
   python app.py
   ```

5. **Open in browser:**
   - Go to: http://localhost:5000
   - Try uploading a photo!
   - Check your Google Drive folder - it should appear there!

### STEP 3: Test on Your Phone (5 minutes)

1. **Get your computer's IP:**
   - In the same terminal, run:
   ```bash
   ipconfig
   ```
   - Find "IPv4 Address" (looks like: 192.168.x.x)

2. **Open on your phone:**
   - Connect phone to same WiFi as computer
   - Open browser on phone
   - Go to: `http://YOUR_IP:5000`
   - Example: `http://192.168.1.100:5000`
   - Try taking a photo!

## Troubleshooting

**"credentials.json not found"**
- Did you rename the file exactly to `credentials.json`?
- Is it in the right folder?

**"Failed to upload to Google Drive"**
- Did you share the Drive folder with the service account email?
- Is the folder ID correct in `.env`?

**Can't access from phone**
- Are phone and computer on the same WiFi?
- Did you use your computer's IP address (not localhost)?

## Need to Deploy for Wedding?

Once everything works locally, check the README.md file for deployment instructions to make it accessible via QR code!

## Questions?

Re-read the README.md file for detailed explanations of each step.

Good luck with your wedding! 🎉💍
