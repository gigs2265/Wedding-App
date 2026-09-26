// Global variables
let currentStream = null;
let currentFacingMode = 'environment'; // Start with back camera
let nextPageToken = null;
let isLoadingMore = false;

// DOM Elements
const cameraBtn = document.getElementById('cameraBtn');
const fileInput = document.getElementById('fileInput');
const cameraModal = document.getElementById('cameraModal');
const closeCamera = document.getElementById('closeCamera');
const cameraStream = document.getElementById('cameraStream');
const captureBtn = document.getElementById('captureBtn');
const switchCameraBtn = document.getElementById('switchCamera');
const photoCanvas = document.getElementById('photoCanvas');
const uploadStatus = document.getElementById('uploadStatus');
const gallery = document.getElementById('gallery');
const refreshBtn = document.querySelector('.btn-refresh');
const loadMoreBtn = document.getElementById('loadMoreBtn');
const loadMoreContainer = document.getElementById('loadMoreContainer');

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadGallery(true);
    setupEventListeners();
});

// Setup Event Listeners
function setupEventListeners() {
    cameraBtn.addEventListener('click', openCamera);
    closeCamera.addEventListener('click', closeCameraModal);
    captureBtn.addEventListener('click', capturePhoto);
    switchCameraBtn.addEventListener('click', switchCamera);
    fileInput.addEventListener('change', handleFileSelect);
    refreshBtn.addEventListener('click', () => {
        nextPageToken = null;
        loadGallery(true);
    });
    loadMoreBtn.addEventListener('click', loadMorePhotos);

    // Close modal when clicking outside
    cameraModal.addEventListener('click', (e) => {
        if (e.target === cameraModal) {
            closeCameraModal();
        }
    });
}

// Open Camera
async function openCamera() {
    try {
        const constraints = {
            video: {
                facingMode: currentFacingMode,
                width: { ideal: 1920 },
                height: { ideal: 1080 }
            },
            audio: false
        };

        currentStream = await navigator.mediaDevices.getUserMedia(constraints);
        cameraStream.srcObject = currentStream;
        cameraModal.classList.add('active');
    } catch (error) {
        console.error('Error accessing camera:', error);
        showStatus('Error: Could not access camera. Please grant camera permissions.', 'error');
    }
}

// Close Camera Modal
function closeCameraModal() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
    cameraModal.classList.remove('active');
}

// Switch Camera (front/back)
async function switchCamera() {
    currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
    closeCameraModal();
    await openCamera();
}

// Capture Photo from Camera
function capturePhoto() {
    const context = photoCanvas.getContext('2d');
    photoCanvas.width = cameraStream.videoWidth;
    photoCanvas.height = cameraStream.videoHeight;
    context.drawImage(cameraStream, 0, 0);

    // Convert canvas to blob and upload
    photoCanvas.toBlob((blob) => {
        const file = new File([blob], `photo_${Date.now()}.jpg`, { type: 'image/jpeg' });
        uploadFile(file);
        closeCameraModal();
    }, 'image/jpeg', 0.95);
}

// Handle File Selection
function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length === 0) return;

    Array.from(files).forEach(file => {
        uploadFile(file);
    });

    // Reset input so same file can be selected again
    event.target.value = '';
}

// Check if a file is a video (some phones leave file.type empty for .mov)
function isVideoFile(file) {
    return file.type.startsWith('video/') || /\.(mp4|mov|avi|webm)$/i.test(file.name);
}

// Grab a frame from a video file to use as its gallery thumbnail.
// Resolves to a JPEG blob, or null if the browser can't decode the video.
function createVideoThumbnail(file) {
    return new Promise((resolve) => {
        const video = document.createElement('video');
        const url = URL.createObjectURL(file);
        let finished = false;

        const finish = (blob) => {
            if (finished) return;
            finished = true;
            clearTimeout(timer);
            video.removeAttribute('src');
            video.load();
            URL.revokeObjectURL(url);
            resolve(blob);
        };

        // Never hold up the upload for long
        const timer = setTimeout(() => finish(null), 8000);

        video.muted = true;
        video.playsInline = true;
        video.preload = 'auto';

        video.addEventListener('loadeddata', () => {
            // Skip the first instant, which is often a black frame
            const duration = isFinite(video.duration) ? video.duration : 0;
            video.currentTime = Math.min(0.5, duration / 2);
        });

        video.addEventListener('seeked', () => {
            try {
                const scale = Math.min(1, 640 / Math.max(video.videoWidth, video.videoHeight));
                const canvas = document.createElement('canvas');
                canvas.width = Math.round(video.videoWidth * scale);
                canvas.height = Math.round(video.videoHeight * scale);
                canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
                canvas.toBlob((blob) => finish(blob), 'image/jpeg', 0.8);
            } catch (error) {
                finish(null);
            }
        });

        video.addEventListener('error', () => finish(null));

        video.src = url;
        video.load();
    });
}

// Upload File
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const statusId = Date.now();
    showStatus(`Uploading ${file.name}...`, 'loading', statusId);

    if (isVideoFile(file)) {
        const thumbnail = await createVideoThumbnail(file);
        if (thumbnail) {
            formData.append('thumbnail', thumbnail, 'thumbnail.jpg');
        }
    }

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
            showStatus(`Successfully uploaded ${file.name}!`, 'success', statusId);
            // Reload gallery after short delay
            setTimeout(() => {
                nextPageToken = null;
                loadGallery(true);
            }, 1000);
        } else {
            showStatus(`Error: ${result.error || 'Upload failed'}`, 'error', statusId);
        }
    } catch (error) {
        console.error('Upload error:', error);
        showStatus(`Error uploading ${file.name}. Please try again.`, 'error', statusId);
    }
}

// Show Status Message
function showStatus(message, type, id = Date.now()) {
    const statusDiv = document.createElement('div');
    statusDiv.className = `status-message status-${type}`;
    statusDiv.textContent = message;
    statusDiv.id = `status-${id}`;

    // Remove old status with same ID if exists
    const oldStatus = document.getElementById(`status-${id}`);
    if (oldStatus) {
        oldStatus.remove();
    }

    uploadStatus.appendChild(statusDiv);

    // Auto-remove success/error messages after 5 seconds
    if (type !== 'loading') {
        setTimeout(() => {
            statusDiv.style.opacity = '0';
            setTimeout(() => statusDiv.remove(), 300);
        }, 5000);
    }
}

// Load Gallery
async function loadGallery(reset = false) {
    if (reset) {
        gallery.innerHTML = '<div class="loading">Loading gallery...</div>';
        nextPageToken = null;
    }

    try {
        const response = await fetch('/gallery');
        const data = await response.json();

        if (response.ok && data.files) {
            nextPageToken = data.nextPageToken;
            displayGallery(data.files, reset);
            updateLoadMoreButton(data.hasMore);
        } else {
            gallery.innerHTML = `<div class="empty-gallery">Error loading gallery: ${data.error || 'Unknown error'}</div>`;
            loadMoreContainer.style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading gallery:', error);
        gallery.innerHTML = '<div class="empty-gallery">Error loading gallery. Please check your connection.</div>';
        loadMoreContainer.style.display = 'none';
    }
}

// Load More Photos
async function loadMorePhotos() {
    if (!nextPageToken || isLoadingMore) return;

    isLoadingMore = true;
    loadMoreBtn.disabled = true;
    loadMoreBtn.textContent = 'Loading...';

    try {
        const response = await fetch(`/gallery?pageToken=${nextPageToken}`);
        const data = await response.json();

        if (response.ok && data.files) {
            nextPageToken = data.nextPageToken;
            displayGallery(data.files, false);
            updateLoadMoreButton(data.hasMore);
        }
    } catch (error) {
        console.error('Error loading more photos:', error);
        showStatus('Error loading more photos. Please try again.', 'error');
    } finally {
        isLoadingMore = false;
        loadMoreBtn.disabled = false;
        loadMoreBtn.textContent = 'Load More';
    }
}

// Update Load More Button
function updateLoadMoreButton(hasMore) {
    if (hasMore) {
        loadMoreContainer.style.display = 'block';
    } else {
        loadMoreContainer.style.display = 'none';
    }
}

// Display Gallery
function displayGallery(files, reset = true) {
    if (reset && files.length === 0) {
        gallery.innerHTML = `
            <div class="empty-gallery">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <circle cx="8.5" cy="8.5" r="1.5"></circle>
                    <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
                <p>No photos or videos yet. Be the first to share!</p>
            </div>
        `;
        loadMoreContainer.style.display = 'none';
        return;
    }

    if (reset) {
        gallery.innerHTML = '';
    }

    files.forEach(file => {
        const item = document.createElement('div');
        item.className = 'gallery-item';
        if (file.is_video) {
            item.classList.add('video');
        }

        const img = document.createElement('img');
        img.src = file.thumbnail;
        img.alt = file.name;
        img.loading = 'lazy';

        // Handle image load error
        img.onerror = () => {
            img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3Ctext x="50" y="50" text-anchor="middle" fill="%23999" font-size="14"%3EImage%3C/text%3E%3C/svg%3E';
        };

        // Open in Google Drive when clicked
        item.addEventListener('click', () => {
            window.open(file.link, '_blank');
        });

        item.appendChild(img);
        gallery.appendChild(item);
    });
}

// Check if browser supports required features
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    console.warn('Camera API not supported');
    cameraBtn.style.display = 'none';
}
