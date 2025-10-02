/**
 * YouTube Downloader - Frontend Logic
 * Handles user interactions and API communication
 */

// ===== DOM Elements =====
const videoUrlInput = document.getElementById('videoUrl');
const fetchBtn = document.getElementById('fetchBtn');
const downloadBtn = document.getElementById('downloadBtn');
const cancelBtn = document.getElementById('cancelBtn');
const errorMessage = document.getElementById('errorMessage');
const loadingSpinner = document.getElementById('loadingSpinner');
const videoInfoSection = document.getElementById('videoInfo');
const downloadProgress = document.getElementById('downloadProgress');
const qualitySection = document.getElementById('qualitySection');
const filesizeValue = document.getElementById('filesizeValue');

// Video info elements
const videoThumbnail = document.getElementById('videoThumbnail');
const videoTitle = document.getElementById('videoTitle');
const videoChannel = document.getElementById('videoChannel');
const videoDuration = document.getElementById('videoDuration');
const videoViews = document.getElementById('videoViews');
const qualitySelect = document.getElementById('qualitySelect');

// Format radio buttons
const formatRadios = document.querySelectorAll('input[name="format"]');

// Store current video data
let currentVideoData = null;
let downloadAbortController = null; // For canceling downloads

// ===== Event Listeners =====

// Fetch video info when button is clicked
fetchBtn.addEventListener('click', fetchVideoInfo);

// Also fetch on Enter key press
videoUrlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        fetchVideoInfo();
    }
});

// Download video when button is clicked
downloadBtn.addEventListener('click', downloadVideo);

// Cancel download when cancel button is clicked
cancelBtn.addEventListener('click', cancelDownload);

// Toggle quality section based on format selection
formatRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'audio') {
            // Hide quality section for audio
            qualitySection.style.display = 'none';
        } else {
            // Show quality section for video
            qualitySection.style.display = 'block';
            updateFilesizeDisplay();
        }
    });
});

// Update filesize when quality changes
qualitySelect.addEventListener('change', updateFilesizeDisplay);

// ===== Helper Functions =====

/**
 * Show error message to user
 * @param {string} message - Error message to display
 */
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorMessage.classList.remove('show');
    }, 5000);
}

/**
 * Hide error message
 */
function hideError() {
    errorMessage.classList.remove('show');
}

/**
 * Format duration from seconds to MM:SS or HH:MM:SS
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration
 */
function formatDuration(seconds) {
    if (!seconds) return 'Unknown';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format view count with K, M suffixes
 * @param {number} views - Number of views
 * @returns {string} Formatted view count
 */
function formatViews(views) {
    if (!views) return 'Unknown views';
    
    if (views >= 1000000) {
        return `${(views / 1000000).toFixed(1)}M views`;
    } else if (views >= 1000) {
        return `${(views / 1000).toFixed(1)}K views`;
    }
    return `${views} views`;
}

/**
 * Format file size in human-readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
function formatFilesize(bytes) {
    if (!bytes || bytes === 0) return 'Unknown';
    
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    
    return `${size.toFixed(2)} ${units[unitIndex]}`;
}

/**
 * Update the filesize display based on selected quality
 */
function updateFilesizeDisplay() {
    if (!currentVideoData || !currentVideoData.formats) {
        filesizeValue.textContent = '--';
        return;
    }
    
    const selectedQuality = qualitySelect.value;
    const format = currentVideoData.formats.find(f => f.quality === selectedQuality);
    
    if (format && format.filesize > 0) {
        filesizeValue.textContent = formatFilesize(format.filesize);
    } else {
        filesizeValue.textContent = 'Unknown (will be calculated during download)';
    }
}

/**
 * Set button loading state
 * @param {HTMLButtonElement} button - Button element
 * @param {boolean} isLoading - Loading state
 */
function setButtonLoading(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.textContent = 'Loading...';
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText || button.textContent;
    }
}

/**
 * Cancel ongoing download
 */
function cancelDownload() {
    if (downloadAbortController) {
        downloadAbortController.abort();
        downloadAbortController = null;
        
        // Reset UI
        downloadProgress.classList.remove('show');
        cancelBtn.classList.remove('show');
        setButtonLoading(downloadBtn, false);
        document.querySelector('.progress-text').textContent = 'Preparing download...';
        
        showError('Download cancelled');
    }
}

// ===== Main Functions =====

/**
 * Fetch video information from the backend
 */
async function fetchVideoInfo() {
    const url = videoUrlInput.value.trim();
    
    // Validate URL input
    if (!url) {
        showError('Please enter a YouTube URL');
        return;
    }
    
    // Basic YouTube URL validation
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$/;
    
    if (!youtubeRegex.test(url)) {
        showError('Please enter a valid YouTube URL');
        return;
    }
    
    // Reset UI
    hideError();
    videoInfoSection.classList.remove('show');
    loadingSpinner.classList.add('show');
    setButtonLoading(fetchBtn, true);
    
    try {
        // Make API request to backend
        const response = await fetch('/api/video-info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch video info');
        }
        
        // Store video data for later use
        currentVideoData = data;
        
        // Display video information
        displayVideoInfo(data);
        
    } catch (error) {
        showError(error.message);
        console.error('Error fetching video info:', error);
    } finally {
        // Hide loading spinner and re-enable button
        loadingSpinner.classList.remove('show');
        setButtonLoading(fetchBtn, false);
    }
}

/**
 * Display video information in the UI
 * @param {Object} data - Video data from API
 */
function displayVideoInfo(data) {
    // Set video thumbnail
    videoThumbnail.src = data.thumbnail;
    videoThumbnail.alt = data.title;
    
    // Set video details
    videoTitle.textContent = data.title;
    videoChannel.textContent = `📺 ${data.channel}`;
    videoDuration.textContent = `⏱️ ${formatDuration(data.duration)}`;
    videoViews.textContent = `👁️ ${formatViews(data.view_count)}`;
    
    // Populate quality options
    qualitySelect.innerHTML = '';
    
    if (data.formats && data.formats.length > 0) {
        data.formats.forEach(format => {
            const option = document.createElement('option');
            option.value = format.quality;
            const sizeText = format.filesize > 0 ? ` - ${formatFilesize(format.filesize)}` : '';
            option.textContent = `${format.quality} (${format.ext.toUpperCase()})${sizeText}`;
            qualitySelect.appendChild(option);
        });
    } else {
        // Fallback if no formats found
        const option = document.createElement('option');
        option.value = '360p';
        option.textContent = '360p (MP4) - Default';
        qualitySelect.appendChild(option);
    }
    
    // Show video info section
    videoInfoSection.classList.add('show');
    
    // Make sure quality section is visible (user might have hidden it for audio)
    qualitySection.style.display = 'block';
    
    // Reset format selection to video
    document.querySelector('input[name="format"][value="video"]').checked = true;
    
    // Update filesize display for first option
    updateFilesizeDisplay();
}

/**
 * Download video or audio based on user selection
 */
async function downloadVideo() {
    if (!currentVideoData) {
        showError('Please fetch video info first');
        return;
    }
    
    const url = videoUrlInput.value.trim();
    
    // Get selected format (video or audio)
    const selectedFormat = document.querySelector('input[name="format"]:checked').value;
    
    // Get selected quality (only for video)
    const selectedQuality = qualitySelect.value;
    
    // Show download progress
    downloadProgress.classList.add('show');
    cancelBtn.classList.add('show');
    setButtonLoading(downloadBtn, true);
    
    // Create abort controller for cancellation
    downloadAbortController = new AbortController();
    
    try {
        // Make download request
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                format: selectedFormat,
                quality: selectedQuality
            }),
            signal: downloadAbortController.signal  // Enable cancellation
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Download failed');
        }
        
        // Get the blob from response
        const blob = await response.blob();
        
        // Get filename from Content-Disposition header or generate one
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'download';
        
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        } else {
            // Generate filename based on title and format
            const ext = selectedFormat === 'audio' ? 'mp3' : 'mp4';
            filename = `${currentVideoData.title.substring(0, 50)}.${ext}`;
        }
        
        // Create download link and trigger download
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);
        
        // Update progress text
        document.querySelector('.progress-text').textContent = '✅ Download complete!';
        
        // Hide progress and cancel button after 3 seconds
        setTimeout(() => {
            downloadProgress.classList.remove('show');
            cancelBtn.classList.remove('show');
            document.querySelector('.progress-text').textContent = 'Preparing download...';
        }, 3000);
        
    } catch (error) {
        // Check if error is from cancellation
        if (error.name === 'AbortError') {
            console.log('Download was cancelled by user');
        } else {
            showError(error.message);
            console.error('Error downloading video:', error);
        }
        downloadProgress.classList.remove('show');
        cancelBtn.classList.remove('show');
    } finally {
        setButtonLoading(downloadBtn, false);
        downloadAbortController = null;
    }
}

// ===== Initialize =====

/**
 * Initialize the application
 */
function init() {
    console.log('YouTube Downloader initialized');
    
    // Hide video info section initially
    videoInfoSection.classList.remove('show');
    loadingSpinner.classList.remove('show');
    downloadProgress.classList.remove('show');
    cancelBtn.classList.remove('show');
}

// Run initialization when DOM is loaded
document.addEventListener('DOMContentLoaded', init);