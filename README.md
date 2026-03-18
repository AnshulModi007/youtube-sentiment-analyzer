# YouTube Comments Sentiment Analyzer 🎭

A full-stack AI project that analyzes the sentiment of YouTube video comments in real-time. It features a custom trained Machine Learning model, a lightning-fast FastAPI backend, and a beautifully designed, premium dark-themed Chrome Extension.

![Demo Banner](https://via.placeholder.com/800x400?text=YouTube+Sentiment+Analyzer)

## ✨ Features
- **Custom ML Model**: Built using Scikit-Learn (`TfidfVectorizer` + `SGDClassifier`) fine-tuned via `GridSearchCV` on a large dataset.
- **Multilingual Support 🌍**: Automatically detects and translates non-English comments into English on-the-fly using `deep-translator` before running predictions.
- **Premium Chrome Extension**: 
  - Glassmorphic dark UI.
  - Animated sentiment distribution bars.
  - Dynamic interactive Donut chart.
  - Color-coded comment cards.
- **FastAPI Backend**: Asynchronous endpoints, concurrent background translations, and extremely low latency.

---

## 📂 Project Structure
```text
youtube_sentiment/
├── fast_api_model.pkl        # Trained scikit-learn model pipeline
├── Untitled23.ipynb          # Jupyter Notebook with the training process
├── backend/                  # FastAPI Server
│   ├── app.py                # Server code & API endpoints
│   └── requirements.txt      # Python dependencies
└── extension/                # Chrome Extension (Manifest V3)
    ├── manifest.json         
    ├── popup.html            # UI Structure
    ├── popup.css             # Premium Styling
    ├── popup.js              # Extension Logic & API Calls
    └── icon128.png           # Extension icon
```

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.9+
- Google Chrome browser
- A [YouTube Data API v3 Key](https://console.cloud.google.com/apis/library/youtube.googleapis.com)

### 2. Backend Setup
1. Clone the repository and navigate to the backend folder:
   ```bash
   cd youtube_sentiment/backend
   ```
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Add your YouTube Data API Key:
   Open `backend/app.py` and replace `"YOUR_API_KEY_HERE"` on line 11 with your actual API key:
   ```python
   YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "YOUR_ACTUAL_API_KEY")
   ```
4. Start the FastAPI server:
   ```bash
   python -m uvicorn app:app --host 127.0.0.1 --port 8000
   ```
   > The server should now be running at `http://127.0.0.1:8000`.

### 3. Extension Setup
1. Open Google Chrome and navigate to `chrome://extensions`.
2. Turn on **Developer mode** (toggle in the top right corner).
3. Click the **Load unpacked** button.
4. Select the `extension/` folder from this repository.
5. The extension icon will now appear in your browser toolbar!

---

## 💻 How to Use
1. Ensure the **FastAPI backend** is running in your terminal.
2. Go to any YouTube video in Chrome.
3. Click the **Sentiment Analyzer** extension icon in your toolbar.
4. Select the maximum number of comments you want to analyze (20, 50, or 100).
5. Click **⚡ Analyze Comments**.
6. View the overarching sentiment, the statistical chart, and the breakdown of individual comments!

---

## 🛠️ Tech Stack
- **Machine Learning**: `scikit-learn`, `pandas`, `jupyter`
- **Backend API**: `FastAPI`, `uvicorn`, `pydantic`, `httpx`
- **Translation**: `deep-translator`
- **Frontend Chrome Extension**: Vanilla HTML5, CSS3, JavaScript (Manifest V3)

---

## 📄 License
MIT License. Feel free to use and modify this project!
