from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file, Response
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from google.auth.transport.requests import Request, AuthorizedSession
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
from dotenv import load_dotenv
import json
import re
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

# Drive folder (created by the app) that stores video preview frames
THUMBNAIL_FOLDER_NAME = 'Wedding App Thumbnails'

# Shown for videos until Google Drive finishes generating their thumbnail
VIDEO_PLACEHOLDER_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#1a1a1a"/><stop offset="1" stop-color="#3a3a3a"/></linearGradient></defs>
<rect width="400" height="400" fill="url(#g)"/>
<text x="200" y="300" text-anchor="middle" fill="#C0C0C0" font-family="Montserrat, sans-serif"
 font-size="22" letter-spacing="3">VIDEO</text>
</svg>'''

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_credentials():
    """Load (and refresh if needed) the OAuth 2.0 credentials"""
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

        return creds
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

def get_drive_service():
    """Initialize Google Drive service with OAuth 2.0"""
    try:
        creds = get_credentials()
        if not creds:
            return None

        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error initializing Drive service: {e}")
        return None

thumbnail_folder_id = None

def get_thumbnail_folder_id(service):
    """Find or create the Drive folder that holds video preview frames.
    Kept outside the wedding folder so the thumbnails don't show up in the gallery."""
    global thumbnail_folder_id
    if thumbnail_folder_id:
        return thumbnail_folder_id

    folder_mime = 'application/vnd.google-apps.folder'
    results = service.files().list(
        q=f"name='{THUMBNAIL_FOLDER_NAME}' and mimeType='{folder_mime}' and trashed=false",
        fields='files(id)'
    ).execute()
    folders = results.get('files', [])
    if folders:
        thumbnail_folder_id = folders[0]['id']
    else:
        folder = service.files().create(
            body={'name': THUMBNAIL_FOLDER_NAME, 'mimeType': folder_mime},
            fields='id'
        ).execute()
        thumbnail_folder_id = folder['id']
    return thumbnail_folder_id

def upload_to_drive(file_path, filename, thumbnail_bytes=None):
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

        # Save the browser-generated preview frame (videos) as its own small file.
        # Drive ignores custom thumbnails for videos and its own can take a long time,
        # so /thumbnail serves this one until Drive's is ready.
        if thumbnail_bytes:
            try:
                thumb = service.files().create(
                    body={'name': f"thumb_{filename}.jpg", 'parents': [get_thumbnail_folder_id(service)]},
                    media_body=MediaIoBaseUpload(BytesIO(thumbnail_bytes), mimetype='image/jpeg'),
                    fields='id'
                ).execute()
                file_metadata['appProperties'] = {'thumbnail_id': thumb['id']}
            except Exception as e:
                print(f"Error saving video thumbnail: {e}")

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
            include_granted_scopes='true',
            prompt='consent'
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

        # Optional preview frame sent by the browser for videos (Drive allows up to 2MB)
        thumbnail_bytes = None
        thumbnail_file = request.files.get('thumbnail')
        if thumbnail_file:
            thumbnail_bytes = thumbnail_file.read()
            if len(thumbnail_bytes) > 2 * 1024 * 1024:
                thumbnail_bytes = None

        # Upload to Google Drive
        drive_result = upload_to_drive(filepath, filename, thumbnail_bytes)

        if drive_result:
            # Delete the local copy once it's safely in Drive, so large videos
            # don't fill up the server's disk
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Could not delete local copy {filepath}: {e}")

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
        creds = get_credentials()
        if not creds:
            return "Drive service not available", 500
        service = build('drive', 'v3', credentials=creds)

        # Get file metadata to determine mime type and Drive's generated thumbnail
        file_metadata = service.files().get(fileId=file_id, fields='mimeType, thumbnailLink, appProperties').execute()
        mime_type = file_metadata.get('mimeType', 'image/jpeg')
        thumbnail_link = file_metadata.get('thumbnailLink')
        saved_thumbnail_id = (file_metadata.get('appProperties') or {}).get('thumbnail_id')

        # Use Drive's thumbnail when available (works for videos and HEIC, and is
        # much smaller than the original file). Request a 400px version.
        if thumbnail_link:
            thumbnail_link = re.sub(r'=s\d+$', '=s400', thumbnail_link)
            thumb_response = AuthorizedSession(creds).get(thumbnail_link, timeout=30)
            if thumb_response.ok:
                response = Response(thumb_response.content,
                                    mimetype=thumb_response.headers.get('Content-Type', 'image/jpeg'))
                response.headers['Cache-Control'] = 'public, max-age=86400'
                return response

        # Preview frame the guest's browser captured when the video was uploaded
        if saved_thumbnail_id:
            thumb_bytes = service.files().get_media(fileId=saved_thumbnail_id).execute()
            response = Response(thumb_bytes, mimetype='image/jpeg')
            response.headers['Cache-Control'] = 'public, max-age=86400'
            return response

        # Drive hasn't made a thumbnail yet (videos can take a long time to process)
        if mime_type.startswith('video/'):
            response = Response(VIDEO_PLACEHOLDER_SVG, mimetype='image/svg+xml')
            response.headers['Cache-Control'] = 'no-store'
            return response

        # Fall back to downloading the original image from Google Drive
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

@app.route('/debug-auth')
def debug_auth():
    """Debug endpoint to check authentication status"""
    oauth_token = os.getenv('OAUTH_TOKEN')
    has_env_var = bool(oauth_token)
    has_token_file = os.path.exists(TOKEN_FILE)

    debug_info = {
        'has_oauth_token_env': has_env_var,
        'has_token_file': has_token_file,
        'oauth_token_length': len(oauth_token) if oauth_token else 0,
        'flask_env': os.getenv('FLASK_ENV', 'not set'),
        'secret_key_set': bool(os.getenv('SECRET_KEY')),
        'drive_folder_id': os.getenv('DRIVE_FOLDER_ID', 'not set')
    }

    if has_env_var:
        try:
            token_data = json.loads(oauth_token)
            debug_info['token_has_refresh'] = 'refresh_token' in token_data
            debug_info['token_fields'] = list(token_data.keys())
        except Exception as e:
            debug_info['token_parse_error'] = str(e)

    return jsonify(debug_info)

if __name__ == '__main__':
    # Run the app on all network interfaces so it's accessible from mobile devices
    app.run(debug=True, host='0.0.0.0', port=5000)
