from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file, Response
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from dotenv import load_dotenv
import json
from io import BytesIO

# Allow OAuth over HTTP for local development only
# In production (Render), this should be disabled as HTTPS is used
if os.getenv('FLASK_ENV') == 'development':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'webm', 'heic'}

# OAuth 2.0 configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

        # If credentials are invalid or don't exist, return None
        # User needs to authorize first via /authorize endpoint
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Try to refresh the token
                creds.refresh(Request())
                # Save the refreshed credentials (try both methods)
                token_json = creds.to_json()
                try:
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(token_json)
                except:
                    # File write failed (read-only filesystem on Render)
                    # Token will need to be set as environment variable
                    print(f"Could not write token file. Set this as OAUTH_TOKEN environment variable:")
                    print(token_json)
            else:
                print("Error: No valid credentials. User needs to authorize the app.")
                return None

        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error initializing Drive service: {e}")
        return None

def upload_to_drive(file_path, filename):
    """Upload file to Google Drive"""
    try:
        service = get_drive_service()
        if not service:
            return None

        # Get the folder ID from environment variable
        folder_id = os.getenv('DRIVE_FOLDER_ID', '')

        file_metadata = {
            'name': filename,
        }

        # Add to specific folder if folder_id is provided
        if folder_id and folder_id != 'your_folder_id_here':
            file_metadata['parents'] = [folder_id]

        # Determine MIME type based on file extension
        ext = filename.rsplit('.', 1)[1].lower()
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'heic': 'image/heic',
            'mp4': 'video/mp4',
            'mov': 'video/quicktime',
            'avi': 'video/x-msvideo',
            'webm': 'video/webm'
        }
        mime_type = mime_types.get(ext, 'application/octet-stream')

        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, webContentLink, thumbnailLink'
        ).execute()

        # Make file publicly accessible
        service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        # Use our proxy endpoint to serve thumbnails (avoids CORS issues)
        file_id = file.get('id')
        thumbnail_url = url_for('get_thumbnail', file_id=file_id, _external=True)

        return {
            'id': file_id,
            'link': file.get('webViewLink'),
            'thumbnail': thumbnail_url
        }
    except Exception as e:
        print(f"Error uploading to Drive: {e}")
        return None

@app.route('/authorize')
def authorize():
    """Start OAuth 2.0 authorization flow"""
    try:
        # Try to load credentials from environment variable first (for Render)
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        if credentials_json:
            print("DEBUG: Loading credentials from GOOGLE_CREDENTIALS env var")
            print(f"DEBUG: Length: {len(credentials_json)}")
            print(f"DEBUG: First 200 chars: {repr(credentials_json[:200])}")
            credentials_info = json.loads(credentials_json)
            flow = Flow.from_client_config(
                credentials_info,
                scopes=SCOPES,
                redirect_uri=url_for('oauth2callback', _external=True)
            )
        # Fall back to credentials file (for local development)
        elif os.path.exists(CREDENTIALS_FILE):
            print("DEBUG: Loading credentials from file")
            flow = Flow.from_client_secrets_file(
                CREDENTIALS_FILE,
                scopes=SCOPES,
                redirect_uri=url_for('oauth2callback', _external=True)
            )
        else:
            return "Error: credentials.json not found. Please download it from Google Cloud Console.", 400

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )

        session['state'] = state
        return redirect(authorization_url)
    except Exception as e:
        return f"Error during authorization: {e}", 500

@app.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth 2.0 callback"""
    try:
        state = session.get('state')

        # Try to load credentials from environment variable first (for Render)
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        if credentials_json:
            credentials_info = json.loads(credentials_json)
            flow = Flow.from_client_config(
                credentials_info,
                scopes=SCOPES,
                state=state,
                redirect_uri=url_for('oauth2callback', _external=True)
            )
        # Fall back to credentials file (for local development)
        elif os.path.exists(CREDENTIALS_FILE):
            flow = Flow.from_client_secrets_file(
                CREDENTIALS_FILE,
                scopes=SCOPES,
                state=state,
                redirect_uri=url_for('oauth2callback', _external=True)
            )
        else:
            return "Error: credentials.json not found.", 400

        flow.fetch_token(authorization_response=request.url)

        credentials = flow.credentials
        token_json = credentials.to_json()

        # ALWAYS print the token for Render setup
        print("=" * 80)
        print("OAUTH TOKEN GENERATED - COPY THIS TO RENDER ENVIRONMENT VARIABLES")
        print("=" * 80)
        print(token_json)
        print("=" * 80)
        print("Set this as OAUTH_TOKEN environment variable in Render dashboard")
        print("=" * 80)

        # Try to save credentials to token.json (for local development)
        try:
            with open(TOKEN_FILE, 'w') as token:
                token.write(token_json)
            print("Token also saved to token.json")
        except Exception as file_error:
            print(f"Could not save token to file: {file_error}")

        return redirect('/')
    except Exception as e:
        return f"Error during OAuth callback: {e}", 500

@app.route('/check-auth')
def check_auth():
    """Check if user is authenticated"""
    # Check environment variable first
    oauth_token = os.getenv('OAUTH_TOKEN')
    if oauth_token:
        try:
            creds = Credentials.from_authorized_user_info(json.loads(oauth_token), SCOPES)
            if creds and creds.valid:
                return jsonify({'authenticated': True})
            elif creds and creds.expired and creds.refresh_token:
                return jsonify({'authenticated': True, 'needs_refresh': True})
        except:
            pass

    # Fall back to token file
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            if creds and creds.valid:
                return jsonify({'authenticated': True})
            elif creds and creds.expired and creds.refresh_token:
                return jsonify({'authenticated': True, 'needs_refresh': True})
        except:
            pass
    return jsonify({'authenticated': False})

@app.route('/')
def index():
    """Render main page"""
    # Check environment variable first
    oauth_token = os.getenv('OAUTH_TOKEN')
    if oauth_token:
        try:
            creds = Credentials.from_authorized_user_info(json.loads(oauth_token), SCOPES)
            if creds and creds.valid:
                return render_template('index.html')
            elif creds and creds.expired and creds.refresh_token:
                return render_template('index.html')
        except:
            pass

    # Check if token file exists
    if not os.path.exists(TOKEN_FILE):
        return render_template('authorize.html')

    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if not creds or not creds.valid:
            if not (creds and creds.expired and creds.refresh_token):
                return render_template('authorize.html')
    except:
        return render_template('authorize.html')

    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = secure_filename(file.filename)
        filename = f"{timestamp}_{original_filename}"

        # Save file locally first
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Upload to Google Drive
        drive_result = upload_to_drive(filepath, filename)

        if drive_result:
            # Optionally delete local file after successful upload to save space
            # Uncomment the line below if you want to delete local copies
            # os.remove(filepath)

            is_video = filename.rsplit('.', 1)[1].lower() in {'mp4', 'mov', 'avi', 'webm'}

            return jsonify({
                'success': True,
                'filename': filename,
                'drive_id': drive_result['id'],
                'thumbnail': drive_result['thumbnail'],
                'link': drive_result['link'],
                'is_video': is_video
            })
        else:
            return jsonify({'error': 'Failed to upload to Google Drive. Check credentials.json and folder permissions.'}), 500

    return jsonify({'error': 'Invalid file type. Allowed: images (jpg, png, gif) and videos (mp4, mov, avi, webm)'}), 400

@app.route('/gallery')
def get_gallery():
    """Get all uploaded files from Google Drive with pagination"""
    try:
        service = get_drive_service()
        if not service:
            return jsonify({'error': 'Drive service not available'}), 500

        folder_id = os.getenv('DRIVE_FOLDER_ID', '')
        page_token = request.args.get('pageToken', None)

        # Build query based on whether folder_id is set
        if folder_id and folder_id != 'your_folder_id_here':
            query = f"'{folder_id}' in parents and trashed=false"
        else:
            query = "trashed=false"

        # Request with pagination
        request_params = {
            'q': query,
            'pageSize': 30,  # Load 30 photos at a time
            'fields': "nextPageToken, files(id, name, mimeType, createdTime, webViewLink, thumbnailLink)",
            'orderBy': "createdTime desc"
        }

        if page_token:
            request_params['pageToken'] = page_token

        results = service.files().list(**request_params).execute()

        files = results.get('files', [])
        next_page_token = results.get('nextPageToken', None)

        gallery_items = []
        for file in files:
            mime_type = file.get('mimeType', '')
            is_video = mime_type.startswith('video/')
            file_id = file.get('id')

            # Use our proxy endpoint to serve thumbnails (avoids CORS issues)
            thumbnail_url = url_for('get_thumbnail', file_id=file_id, _external=True)

            gallery_items.append({
                'id': file_id,
                'name': file.get('name'),
                'thumbnail': thumbnail_url,
                'link': file.get('webViewLink'),
                'is_video': is_video,
                'created': file.get('createdTime')
            })

        return jsonify({
            'files': gallery_items,
            'nextPageToken': next_page_token,
            'hasMore': next_page_token is not None
        })
    except Exception as e:
        print(f"Error fetching gallery: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/thumbnail/<file_id>')
def get_thumbnail(file_id):
    """Proxy endpoint to serve Google Drive thumbnails"""
    try:
        service = get_drive_service()
        if not service:
            return "Drive service not available", 500

        # Get file metadata to determine mime type
        file_metadata = service.files().get(fileId=file_id, fields='mimeType').execute()
        mime_type = file_metadata.get('mimeType', 'image/jpeg')

        # Download the file from Google Drive
        request_file = service.files().get_media(fileId=file_id)
        file_buffer = BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request_file)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        file_buffer.seek(0)

        # Return the file as a response
        return send_file(
            file_buffer,
            mimetype=mime_type,
            as_attachment=False,
            download_name=f"{file_id}.jpg"
        )
    except Exception as e:
        print(f"Error fetching thumbnail: {e}")
        # Return a placeholder grey image on error
        return "", 404

if __name__ == '__main__':
    # Run the app on all network interfaces so it's accessible from mobile devices
    app.run(debug=True, host='0.0.0.0', port=5000)
