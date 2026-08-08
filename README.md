# ⏱️ YouTube Playlist Duration Calculator

A sleek, fast, and feature-rich web application to calculate the total watch time of YouTube playlists, specific video selections, or custom video ranges, with real-time playback speed breakdowns (`1.25x`, `1.5x`, `1.75x`, `2.0x`, etc.).

---

## 🌟 Key Features

- **📏 Range Mode**: Calculate the exact duration of all videos **between** two specified videos (e.g. from `L1` to `L53`), inclusive.
- **🎯 Individual Mode**: Pick specific videos by title or paste their YouTube URLs to calculate total duration for only those videos.
- **📋 Full Playlist Mode**: Calculate total watch duration for the entire playlist in one click.
- **⏩ Speed Multiplier & Breakdown**:
  - Live calculations for `1.0x`, `1.25x`, `1.5x`, `1.75x`, and `2.0x`.
  - Custom playback speed input (e.g., `1.15x`).
  - Displays total **Time Saved** at higher playback speeds!
- **🔗 Flexible Video Inputs**: Accepts both video title keywords AND direct YouTube video URLs (`youtu.be/xxx`, `youtube.com/watch?v=xxx`).
- **🎨 Glassmorphic & Modern UI**: Tailored dark-mode UI built with smooth animations and clean responsive design.

---

## 🚀 Live Demo / Hosting

### Option 1: Deploy to Render in 1-Click
You can deploy this application for free on [Render](https://render.com) using the included `render.yaml`:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/NeelParekh17/YouTube-Playlist-Duration-Calculator)

1. Click the **Deploy to Render** button above.
2. Sign in with GitHub.
3. Render will automatically build and deploy your app.

---

## 💻 Running Locally

### Prerequisites
- Python 3.10+
- `pip`

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NeelParekh17/YouTube-Playlist-Duration-Calculator.git
   cd YouTube-Playlist-Duration-Calculator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Flask application:**
   ```bash
   python app.py
   ```

4. **Open in Browser:**
   Navigate to `http://127.0.0.1:5050` in your web browser.

---

## 📁 Project Structure

```
├── app.py              # Flask backend server & yt-dlp metadata extraction logic
├── static/
│   └── index.html      # Responsive HTML/CSS/JS frontend UI
├── requirements.txt    # Python dependencies
├── Procfile            # Deployment configuration (Gunicorn WSGI)
├── render.yaml         # Render Blueprint configuration
├── .gitignore          # Ignored files
└── README.md           # Project documentation
```

---

## 🛠️ Built With

- **Backend**: Python, Flask, `yt-dlp`
- **Frontend**: HTML5, Vanilla CSS, Modern JavaScript
- **Deployment**: Gunicorn, Render / Heroku / Koyeb

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
