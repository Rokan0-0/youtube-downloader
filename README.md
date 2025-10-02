# 🎬 YouTube Downloader

A clean, modern web application to download YouTube videos and audio in various formats. Built with Flask and yt-dlp for reliable downloads.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- 📹 **Video Downloads** - Download videos in multiple quality options (720p, 1080p, etc.)
- 🎵 **Audio Extraction** - Extract and download audio as MP3
- 🖼️ **Video Preview** - View video information, thumbnail, and metadata before downloading
- 🎨 **Modern UI** - Clean, responsive interface that works on all devices
- ⚡ **Fast & Reliable** - Powered by yt-dlp for stable downloads
- 🔒 **Local & Private** - Runs on your machine, no data sent to external servers

## 📸 Screenshots

<!-- Add screenshots here once you have the app running -->
*Coming soon - Add screenshots of your app in action!*

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- FFmpeg (required for audio extraction)

#### Installing FFmpeg:

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/youtube-downloader.git
   cd youtube-downloader
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Activate it:
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   - Navigate to `http://localhost:5000`
   - Paste a YouTube URL and start downloading!

## 💻 Usage

1. **Paste YouTube URL** - Copy any YouTube video URL and paste it into the input field
2. **Get Video Info** - Click the button to fetch video details
3. **Choose Format** - Select either Video or Audio (MP3)
4. **Select Quality** - Choose your preferred quality (for video downloads)
5. **Download** - Click download and the file will be saved to your browser's download folder

## 🛠️ Technology Stack

- **Backend:** Flask (Python web framework)
- **Download Engine:** yt-dlp (YouTube download library)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Audio Processing:** FFmpeg

## 📁 Project Structure

```
youtube-downloader/
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Frontend HTML
├── static/
│   ├── style.css         # Styling
│   └── script.js         # Frontend logic
├── downloads/            # Temporary download folder (auto-cleaned)
├── .gitignore           # Git ignore rules
└── README.md            # Project documentation
```

## 🔧 Configuration

You can customize the application by modifying these variables in `app.py`:

```python
DOWNLOAD_FOLDER = 'downloads'  # Change download directory
app.run(debug=True, port=5000) # Change port number
```

## ⚠️ Important Notes

### Legal Disclaimer
This tool is for **personal use only**. Please respect:
- YouTube's Terms of Service
- Copyright laws and content creator rights
- Fair use guidelines

**Do not use this tool to:**
- Download copyrighted content without permission
- Redistribute downloaded content
- Violate any applicable laws or regulations

### Limitations
- Some videos may not be downloadable due to restrictions
- Very long videos may take time to process
- Age-restricted content may not be accessible

## 🐛 Troubleshooting

### "yt-dlp not found" error
```bash
pip install --upgrade yt-dlp
```

### "FFmpeg not found" error
Make sure FFmpeg is installed and added to your system PATH.

### Download fails
- Check your internet connection
- Verify the YouTube URL is valid and accessible
- Try updating yt-dlp: `pip install --upgrade yt-dlp`

### Port already in use
Change the port in `app.py`:
```python
app.run(debug=True, port=5001)  # Use different port
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature/improvement`)
6. Create a Pull Request

## 📝 Future Enhancements

- [ ] Playlist download support
- [ ] Subtitle/caption download
- [ ] Download history tracking
- [ ] Batch URL processing
- [ ] Custom output directory selection
- [ ] Dark mode toggle

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Your Name**
- GitHub: [@YOUR_USERNAME](https://github.com/Rokan0-0)

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Amazing YouTube download library
- [Flask](https://flask.palletsprojects.com/) - Lightweight Python web framework
- [FFmpeg](https://ffmpeg.org/) - Multimedia processing

---

⭐ If you find this project useful, please consider giving it a star!

**Note:** This is a personal project for educational purposes. Always respect content creators and follow applicable laws.