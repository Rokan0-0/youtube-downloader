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
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'nocheckcertificate': True,
            'age_limit': None,
            'format': 'all',
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
            for f in info.get('formats', []):
                # Only include formats with a valid URL and ext mp4/webm and filesize
                if not f.get('url'):
                    continue
                ext = f.get('ext', 'mp4')
                if ext not in ['mp4', 'webm']:
                    continue
                filesize = f.get('filesize') or f.get('filesize_approx')
                if not filesize:
                    continue
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                height = f.get('height')
                format_id = f.get('format_id')
                # Video formats (has video, height >= 144)
                if vcodec != 'none' and height and height >= 144:
                    quality = f"{height}p"
                    has_audio = acodec != 'none'
                    formats.append({
                        'format_id': format_id,
                        'quality': quality,
                        'ext': ext,
                        'filesize': filesize,
                        'filesize_mb': round(filesize / (1024 * 1024), 2),
                        'has_audio': has_audio,
                        'height': height
                    })
                # Audio-only formats (no video, has audio)
                elif vcodec == 'none' and acodec != 'none':
                    formats.append({
                        'format_id': format_id,
                        'quality': 'audio',
                        'ext': ext,
                        'filesize': filesize,
                        'filesize_mb': round(filesize / (1024 * 1024), 2),
                        'has_audio': True,
                        'height': None
                    })
            # Sort: video by height desc, audio by filesize desc
            formats.sort(key=lambda x: (x['height'] or 0), reverse=True)

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
        format_id = data.get('format_id')

        print(f"\n{'='*50}")
        print(f"Download Request:")
        print(f"URL: {url}")
        print(f"Format: {download_format}")
        print(f"Format ID: {format_id}")
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
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'nocheckcertificate': True,
                'age_limit': None,
            }
        else:
            # Video download with selected format_id
            ydl_opts = {
                'format': format_id,
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'quiet': False,
                'verbose': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'nocheckcertificate': True,
                'age_limit': None,
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
                ext = '.mp3'
            else:
                # Get extension from info or fallback to .mp4
                ext = '.' + (info.get('ext') or 'mp4')
            base_name = sanitize_filename(info['title'])
            # Find the correct file (yt-dlp may append extra info)
            # Find all files that start with base_name and end with ext (no trailing underscores or .part)
            possible_files = [f for f in os.listdir(DOWNLOAD_FOLDER)
                             if f.startswith(base_name) and f.endswith(ext) and not f.endswith(ext + '_') and not f.endswith('.part')]
            if possible_files:
                # Pick the shortest filename (most likely correct)
                filename = min(possible_files, key=len)
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            else:
                # Fallback to original logic
                filename = base_name + ext
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                if not os.path.exists(filepath):
                    return jsonify({'error': 'Download completed but file not found'}), 500

            # If filename ends with .mp4_ or .webm_, rename to .mp4 or .webm
            if filename.endswith('.mp4_'):
                new_filename = filename[:-1]
                new_filepath = os.path.join(DOWNLOAD_FOLDER, new_filename)
                os.rename(filepath, new_filepath)
                filename = new_filename
                filepath = new_filepath
            elif filename.endswith('.webm_'):
                new_filename = filename[:-1]
                new_filepath = os.path.join(DOWNLOAD_FOLDER, new_filename)
                os.rename(filepath, new_filepath)
                filename = new_filename
                filepath = new_filepath

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
        print(f"Format ID: {format_id}")
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
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'nocheckcertificate': True,
                'age_limit': None,
            }
        else:
            # Video download with selected format_id
            ydl_opts = {
                'format': format_id,
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'quiet': False,
                'verbose': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'nocheckcertificate': True,
                'age_limit': None,
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
                ext = '.mp3'
            else:
                # Get extension from info or fallback to .mp4
                ext = '.' + (info.get('ext') or 'mp4')
            base_name = sanitize_filename(info['title'])
            # Find the correct file (yt-dlp may append extra info)
            # Find all files that start with base_name and end with ext (no trailing underscores or .part)
            possible_files = [f for f in os.listdir(DOWNLOAD_FOLDER)
                             if f.startswith(base_name) and f.endswith(ext) and not f.endswith(ext + '_') and not f.endswith('.part')]
            if possible_files:
                # Pick the shortest filename (most likely correct)
                filename = min(possible_files, key=len)
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            else:
                # Fallback to original logic
                filename = base_name + ext
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                if not os.path.exists(filepath):
                    return jsonify({'error': 'Download completed but file not found'}), 500

            # If filename ends with .mp4_ or .webm_, rename to .mp4 or .webm
            if filename.endswith('.mp4_'):
                new_filename = filename[:-1]
                new_filepath = os.path.join(DOWNLOAD_FOLDER, new_filename)
                os.rename(filepath, new_filepath)
                filename = new_filename
                filepath = new_filepath
            elif filename.endswith('.webm_'):
                new_filename = filename[:-1]
                new_filepath = os.path.join(DOWNLOAD_FOLDER, new_filename)
                os.rename(filepath, new_filepath)
                filename = new_filename
                filepath = new_filepath

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