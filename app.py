"""
YouTube Downloader Flask Application
A web application to download YouTube videos and audio in various formats
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import re
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for API requests

# Configuration
DOWNLOAD_FOLDER = 'downloads'
# Create downloads folder if it doesn't exist
Path(DOWNLOAD_FOLDER).mkdir(exist_ok=True)


def validate_youtube_url(url):
    """
    Validate if the provided URL is a valid YouTube URL
    
    Args:
        url (str): The URL to validate
        
    Returns:
        bool: True if valid YouTube URL, False otherwise
    """
    youtube_regex = r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$'
    return re.match(youtube_regex, url) is not None


def sanitize_filename(filename):
    """
    Remove invalid characters from filename
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename safe for file system
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Limit length to 200 characters
    return filename[:200]


@app.route('/')
def index():
    """
    Render the main page
    
    Returns:
        HTML template for the home page
    """
    return render_template('index.html')


@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    """
    Fetch video information from YouTube URL
    
    Expected JSON input:
        {
            "url": "https://youtube.com/watch?v=..."
        }
        
    Returns:
        JSON with video information or error message
    """
    try:
        # Get URL from request
        data = request.get_json()
        url = data.get('url', '').strip()
        
        # Validate URL
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        if not validate_youtube_url(url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        # Configure yt-dlp options for fetching info only
        # Try multiple strategies to get maximum format availability
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            # Add headers to mimic a real browser
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Try web and mobile web clients which often have better format access
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'ios', 'android', 'mweb'],
                    'player_skip': ['webpage'],
                    'skip': ['hls', 'dash'],  # Skip adaptive formats for now
                }
            },
            # Additional options
            'nocheckcertificate': True,
            'age_limit': None,
            'format': 'all',  # Request all available formats
        }
        
        # Extract video information
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Debug: Print ALL formats returned by yt-dlp
            all_formats = info.get('formats', [])
            print(f"\n🟢 yt-dlp returned {len(all_formats)} formats:")
            for f in all_formats[:10]:  # Print first 10
                print(f"  - id: {f.get('format_id')}, ext: {f.get('ext')}, height: {f.get('height')}, "
                      f"vcodec: {f.get('vcodec')}, acodec: {f.get('acodec')}, filesize: {f.get('filesize')}")
            
            # Get available formats - be more inclusive to see ALL qualities
            formats = []
            # Get all available formats from YouTube
            for f in info.get('formats', []):
                vcodec = f.get('vcodec', 'none')
                height = f.get('height')
                # Skip formats without video or without height (storyboards, audio-only, etc.)
                if vcodec == 'none' or not height or height < 144:
                    continue
                quality = f"{height}p"
                ext = f.get('ext', 'mp4')
                filesize = f.get('filesize') or f.get('filesize_approx') or 0
                has_audio = f.get('acodec') != 'none'
                format_id = f.get('format_id')
                formats.append({
                    'format_id': format_id,
                    'quality': quality,
                    'ext': ext,
                    'filesize': filesize,
                    'filesize_mb': round(filesize / (1024 * 1024), 2) if filesize else 0,
                    'has_audio': has_audio,
                    'height': height
                })
            # Sort by height descending
            formats.sort(key=lambda x: x['height'], reverse=True)
            
            print(f"\n📊 Filtered formats for frontend: {len(formats)}")
            for fmt in formats:
                print(f"   - {fmt['quality']} ({fmt['ext']}) - Audio: {fmt['has_audio']} - Height: {fmt['height']}")

            # Prepare response data
            video_info = {
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'channel': info.get('uploader', 'Unknown Channel'),
                'view_count': info.get('view_count', 0),
                'formats': formats,  # Send all available formats
            }

            return jsonify(video_info), 200
            
    except Exception as e:
        return jsonify({'error': f'Failed to fetch video info: {str(e)}'}), 500


@app.route('/api/download', methods=['POST'])
def download_video():
    """
    Download video or audio from YouTube
    
    Expected JSON input:
        {
            "url": "https://youtube.com/watch?v=...",
            "format": "video",  // or "audio"
            "quality": "720p"   // for video only
        }
        
    Returns:
        File download or error message
    """
    try:
        # Get request data
        data = request.get_json()
        url = data.get('url', '').strip()
        download_format = data.get('format', 'video')  # 'video' or 'audio'
        quality = data.get('quality', '720p')
        
        print(f"\n{'='*50}")
        print(f"Download Request:")
        print(f"URL: {url}")
        print(f"Format: {download_format}")
        print(f"Quality: {quality}")
        print(f"{'='*50}\n")
        
        # Validate URL
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        if not validate_youtube_url(url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        # Configure download options based on format
        if download_format == 'audio':
            # Audio-only download (MP3)
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'quiet': False,
                # Add headers and extractor args to avoid 403 errors
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios', 'android'],
                        'player_skip': ['configs'],
                    }
                },
                'nocheckcertificate': True,
                'age_limit': None,
            }
        else:
            # Video download with specified quality
            # Extract quality number (e.g., "720p" -> "720")
            quality_num = quality.replace('p', '')
            
            ydl_opts = {
                # Download best video at selected quality + best audio, then merge
                # This handles video-only formats by automatically merging with audio
                'format': (
                    f'bestvideo[height<={quality_num}]+bestaudio/best[height<={quality_num}]'
                ),
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',  # Merge to MP4
                'quiet': False,
                'verbose': True,
                # Add headers and extractor args
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web', 'ios', 'android', 'mweb'],
                        'player_skip': ['webpage'],
                        'skip': ['hls', 'dash'],
                    }
                },
                'nocheckcertificate': True,
                'age_limit': None,
                # Ensure FFmpeg is used for merging
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            }
        
        # Download the video/audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info to get the final filename
            info = ydl.extract_info(url, download=True)
            
            # Construct the filename
            if download_format == 'audio':
                filename = sanitize_filename(info['title']) + '.mp3'
            else:
                filename = sanitize_filename(info['title']) + '.mp4'
            
            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            
            # Check if file exists
            if not os.path.exists(filepath):
                # Sometimes yt-dlp names files differently, try to find it
                possible_files = [f for f in os.listdir(DOWNLOAD_FOLDER) 
                                 if f.startswith(sanitize_filename(info['title']))]
                if possible_files:
                    filepath = os.path.join(DOWNLOAD_FOLDER, possible_files[0])
                    filename = possible_files[0]
                else:
                    return jsonify({'error': 'Download completed but file not found'}), 500
            
            # Send file to user
            response = send_file(
                filepath,
                as_attachment=True,
                download_name=filename
            )
            
            # Delete file after sending (cleanup)
            @response.call_on_close
            def cleanup():
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except Exception as e:
                    print(f"Error cleaning up file: {e}")
            
            return response
            
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


# Run the Flask app
if __name__ == '__main__':
    print("🚀 Starting YouTube Downloader Server...")
    print("📍 Open your browser and go to: http://localhost:5000")
    print("⏹️  Press CTRL+C to stop the server\n")
    app.run(debug=True, port=5000)