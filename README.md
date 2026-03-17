# Wedding Photo Gallery Web App

A beautiful, mobile-responsive web application that allows wedding guests to upload photos and videos directly to your Google Drive through a QR code.

## Features

- **Camera Access**: Take photos directly from mobile devices
- **File Upload**: Upload existing photos and videos
- **Google Drive Integration**: All media automatically saved to your Drive
- **Live Gallery**: View all uploaded photos and videos in real-time
- **Mobile Responsive**: Optimized for all devices
- **QR Code Ready**: Easy access for wedding guests

## Project Structure

```
weddingapp/
├── app.py                  # Flask backend
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (YOU NEED TO CONFIGURE THIS)
├── .gitignore             # Git ignore file
├── credentials.json        # Google API credentials (YOU NEED TO ADD THIS)
├── templates/
│   └── index.html         # Main webpage
├── static/
│   ├── css/
│   │   └── style.css      # Styling
│   └── js/
│       └── main.js        # Frontend logic
└── venv/                  # Virtual environment
```

## Setup Instructions

### Phase 1: ✅ COMPLETED
- [x] Project structure created
- [x] All code files created
- [x] Virtual environment set up
- [x] Dependencies installed

### Phase 2: Google Drive API Setup (YOU NEED TO DO THIS)

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create a New Project**
   - Click "Select a project" at the top
   - Click "New Project"
   - Name it "Wedding Photos" (or any name you like)
   - Click "Create"

3. **Enable Google Drive API**
   - Make sure your new project is selected
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click on it and click "Enable"

4. **Create Service Account**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Service account name: "wedding-uploader" (or any name)
   - Click "Create and Continue"
   - Select role: "Editor"
   - Click "Continue" then "Done"

5. **Generate JSON Key**
   - Click on the service account you just created
   - Go to the "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Choose "JSON"
   - Click "Create"
   - A file will be downloaded - **RENAME IT TO `credentials.json`**
   - **MOVE IT TO YOUR PROJECT FOLDER** (C:\Users\Owner\Documents\VSCode Projects\weddingapp)

6. **Create Google Drive Folder**
   - Go to your Google Drive (drive.google.com)
   - Create a new folder (e.g., "Wedding Photos")
   - Right-click the folder > Click "Share"
   - **IMPORTANT**: Add the service account email (found in credentials.json - looks like: xxx@xxx.iam.gserviceaccount.com)
   - Give it "Editor" permission
   - Click "Share"
   - Open the folder and look at the URL
   - Copy the folder ID (the long string after /folders/ in the URL)
   - Example: https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE

7. **Update .env File**
   - Open the `.env` file in your project
   - Replace `your_folder_id_here` with your actual folder ID
   - Save the file

### Phase 3: Running the Application

1. **Open VS Code**
   - Open the project folder: `File` > `Open Folder`
   - Select: `C:\Users\Owner\Documents\VSCode Projects\weddingapp`

2. **Open Terminal in VS Code**
   - Press `Ctrl + `` (backtick key)
   - Or go to `Terminal` > `New Terminal`

3. **Activate Virtual Environment**
   ```bash
   venv\Scripts\activate
   ```
   You should see `(venv)` appear in your terminal.

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Open in Browser**
   - Open your browser
   - Go to: `http://localhost:5000`
   - You should see your wedding photo gallery!

### Phase 4: Testing on Mobile (Same WiFi)

1. **Find Your Computer's IP Address**
   - In terminal, run:
   ```bash
   ipconfig
   ```
   - Look for "IPv4 Address" (usually looks like: 192.168.x.x)

2. **Access from Phone**
   - Make sure your phone is on the same WiFi network
   - Open browser on phone
   - Go to: `http://YOUR_IP_ADDRESS:5000`
   - Example: `http://192.168.1.100:5000`

### Phase 5: Deployment for Wedding Day

For your wedding, you'll need the app accessible over the internet. Here are your options:

**Option 1: PythonAnywhere (Free, Easiest)**
- Go to: https://www.pythonanywhere.com/
- Create free account
- Upload your files
- Configure web app
- Get a permanent URL like: `yourname.pythonanywhere.com`

**Option 2: Render (Modern, Free Tier)**
- Go to: https://render.com/
- Connect your GitHub repo
- Deploy as Web Service
- Get URL like: `yourapp.onrender.com`

**Option 3: Railway**
- Go to: https://railway.app/
- Similar to Render
- Easy deployment

### Phase 6: Create QR Code

1. **Get Your Deployment URL**
   - From PythonAnywhere, Render, or Railway

2. **Generate QR Code**
   - Go to: https://www.qr-code-generator.com/
   - Enter your URL
   - Download the QR code image

3. **Print and Display**
   - Print the QR code
   - Place it at your wedding venue
   - Guests scan and upload photos!

## Testing Before Wedding

Before the big day, test everything:

1. ✅ Upload a photo from your computer
2. ✅ Take a photo using camera button
3. ✅ Check that files appear in Google Drive
4. ✅ Verify gallery displays uploaded media
5. ✅ Test from mobile phone
6. ✅ Share with friend to test QR code

## Troubleshooting

**Error: "credentials.json not found"**
- Make sure you downloaded and renamed the JSON key file
- Place it in the project root folder

**Error: "Failed to upload to Google Drive"**
- Check that you shared the Drive folder with the service account email
- Verify the folder ID in `.env` is correct

**Can't access from mobile**
- Ensure phone and computer are on same WiFi
- Check Windows Firewall isn't blocking port 5000

**Camera not working**
- Browser must be HTTPS for camera access (works on localhost)
- For deployment, ensure site uses HTTPS

## File Size Limits

- Maximum file size: 100MB per upload
- Supported formats:
  - Images: JPG, PNG, GIF, HEIC
  - Videos: MP4, MOV, AVI, WEBM

## Security Notes

- **NEVER** commit `credentials.json` to GitHub (already in .gitignore)
- **NEVER** share your credentials file publicly
- Keep your `.env` file secret

## Need Help?

If you run into issues, check:
1. Did you complete all Phase 2 steps?
2. Is the service account email added to your Drive folder?
3. Is the folder ID correct in `.env`?
4. Did you activate the virtual environment?

## Next Steps

1. Complete Google Drive API setup (Phase 2)
2. Test the app locally
3. Choose a deployment platform
4. Deploy before your wedding
5. Generate and print QR code
6. Enjoy your special day!

---

**Congratulations on your wedding! 🎉**
