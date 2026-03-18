import pickle
import os
import re
import httpx
import concurrent.futures
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Configuration ───────────────────────────────────────────────
# Put your YouTube Data API v3 key here (do not commit the real key to GitHub!):
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "YOUR_API_KEY_HERE")

from deep_translator import GoogleTranslator

def translate_text(text: str) -> str:
    """Translate a single text to English. Returns original if fails or empty."""
    if not text.strip():
        return text
    try:
        res = GoogleTranslator(source='auto', target='en').translate(text)
        return res if res else text
    except Exception:
        return text

def translate_comments_concurrently(comments: list[str]) -> list[str]:
    """Translate a list of comments to English concurrently to save time."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        return list(executor.map(translate_text, comments))


# ── Load the trained model ──────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "fast_api_model.pkl")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

best_model = model.best_estimator_ if hasattr(model, "best_estimator_") else model

# ── App setup ───────────────────────────────────────────────────
app = FastAPI(title="YouTube Sentiment Analyzer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LABEL_MAP = {0: "Negative", 1: "Neutral", 2: "Positive"}


# ── Request / Response schemas ──────────────────────────────────
class PredictRequest(BaseModel):
    comments: list[str]


class VideoRequest(BaseModel):
    video_id: str
    max_comments: int = 100


class CommentResult(BaseModel):
    text: str
    label: int
    sentiment: str


class AnalyzeResponse(BaseModel):
    total: int
    positive: int
    neutral: int
    negative: int
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    overall_sentiment: str
    results: list[CommentResult]


# ── Helpers ─────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    """Light preprocessing matching the training pipeline."""
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def fetch_youtube_comments(video_id: str, max_comments: int) -> list[str]:
    """Fetch comments from YouTube Data API v3."""
    if YOUTUBE_API_KEY == "YOUR_API_KEY_HERE":
        raise HTTPException(
            status_code=500,
            detail="YouTube API key not configured. Set YOUTUBE_API_KEY in backend/app.py",
        )

    comments = []
    next_page = ""

    async with httpx.AsyncClient(timeout=30) as client:
        while len(comments) < max_comments:
            per_page = min(100, max_comments - len(comments))
            url = (
                f"https://www.googleapis.com/youtube/v3/commentThreads"
                f"?part=snippet&videoId={video_id}&maxResults={per_page}"
                f"&order=relevance&textFormat=plainText&key={YOUTUBE_API_KEY}"
            )
            if next_page:
                url += f"&pageToken={next_page}"

            resp = await client.get(url)
            if resp.status_code != 200:
                err = resp.json().get("error", {}).get("message", resp.text)
                raise HTTPException(status_code=resp.status_code, detail=f"YouTube API: {err}")

            data = resp.json()
            for item in data.get("items", []):
                comments.append(item["snippet"]["topLevelComment"]["snippet"]["textDisplay"])

            next_page = data.get("nextPageToken", "")
            if not next_page:
                break

    return comments[:max_comments]


def build_analysis(original_comments: list[str], translated_comments: list[str] = None) -> AnalyzeResponse:
    """Run model prediction and build response. Uses translated comments for prediction if provided."""
    if translated_comments is None:
        translated_comments = original_comments
        
    cleaned = [clean_text(c) for c in translated_comments]
    preds = best_model.predict(cleaned).tolist()

    total = len(preds)
    neg = preds.count(0)
    neu = preds.count(1)
    pos = preds.count(2)

    if total == 0:
        overall = "Neutral"
    elif pos >= neg and pos >= neu:
        overall = "Positive"
    elif neg >= pos and neg >= neu:
        overall = "Negative"
    else:
        overall = "Neutral"

    return AnalyzeResponse(
        total=total,
        positive=pos,
        neutral=neu,
        negative=neg,
        positive_pct=round(pos / total * 100, 1) if total else 0,
        neutral_pct=round(neu / total * 100, 1) if total else 0,
        negative_pct=round(neg / total * 100, 1) if total else 0,
        overall_sentiment=overall,
        results=[
            CommentResult(text=orig, label=int(p), sentiment=LABEL_MAP[int(p)])
            for orig, p in zip(original_comments, preds)
        ],
    )


# ── Endpoints ───────────────────────────────────────────────────
@app.get("/")
def health():
    return {"status": "ok", "model": "SGDClassifier + TfidfVectorizer"}


@app.post("/predict")
def predict(req: PredictRequest):
    cleaned = [clean_text(c) for c in req.comments]
    preds = best_model.predict(cleaned).tolist()
    return {
        "predictions": [
            {"text": orig, "label": int(p), "sentiment": LABEL_MAP[int(p)]}
            for orig, p in zip(req.comments, preds)
        ]
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: PredictRequest):
    # For direct analyze requests, translate synchronously
    translated = translate_comments_concurrently(req.comments)
    return build_analysis(req.comments, translated)


@app.post("/analyze_video", response_model=AnalyzeResponse)
async def analyze_video(req: VideoRequest):
    """Fetch comments from YouTube, translate them, and analyze them."""
    comments = await fetch_youtube_comments(req.video_id, req.max_comments)
    if not comments:
        raise HTTPException(status_code=404, detail="No comments found for this video.")
    
    # Translate comments in a separate thread pool so we don't block the async event loop
    import asyncio
    translated = await asyncio.get_running_loop().run_in_executor(
        None, translate_comments_concurrently, comments
    )
    
    return build_analysis(comments, translated)
