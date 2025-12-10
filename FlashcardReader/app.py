import os
import io
import json
import base64
import tempfile
from urllib.parse import quote_plus

from flask import Flask, render_template, request, jsonify, send_file

import cv2
import numpy as np
import pytesseract
import pandas as pd
from gtts import gTTS

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'flashcards2.csv')

# Configure Tesseract path for Windows if available
TESSERACT_ENV = os.environ.get('TESSERACT_CMD')
if TESSERACT_ENV and os.path.exists(TESSERACT_ENV):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_ENV
else:
    common_paths = [
        r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
    ]
    for p in common_paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break

# Load CSV into memory with hot-reload support
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"CSV not found at {CSV_PATH}")

required_cols = ['category', 'keyword', 'explanation', 'fun_fact', 'image_path', 'video_link']
records_by_keyword = {}
CSV_MTIME = None


def _load_csv_into_memory():
    global records_by_keyword
    df_local = pd.read_csv(CSV_PATH)
    for c in required_cols:
        if c not in df_local.columns:
            raise ValueError(f"Missing required column '{c}' in CSV")
    rbk = {}
    for _, row in df_local.iterrows():
        key = str(row['keyword']).strip().upper()
        rbk[key] = {
            'category': str(row['category']).strip(),
            'keyword': key,
            'explanation': str(row['explanation']).strip(),
            'fun_fact': str(row['fun_fact']).strip(),
            'image_path': str(row['image_path']).strip() if not pd.isna(row['image_path']) else '',
            'video_link': str(row['video_link']).strip() if not pd.isna(row['video_link']) else '',
        }
    records_by_keyword = rbk


def refresh_data_if_changed():
    global CSV_MTIME
    try:
        mtime = os.path.getmtime(CSV_PATH)
    except OSError:
        return
    if CSV_MTIME is None or mtime != CSV_MTIME:
        _load_csv_into_memory()
        CSV_MTIME = mtime


# Initial load
refresh_data_if_changed()

app = Flask(__name__)


def _resolve_media_path(path_str: str) -> str:
    """Resolve a media path that may be absolute or relative to BASE_DIR.
    Also normalize slashes and strip extraneous quotes.
    """
    if not path_str:
        return ''
    s = str(path_str).strip().strip('"').strip("'")
    # Normalize slashes and path
    s = s.replace('/', os.sep)
    s = os.path.normpath(s)
    if os.path.isabs(s):
        return s
    return os.path.normpath(os.path.join(BASE_DIR, s))

def preprocess_for_ocr(frame_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    # Light blur (fast) to reduce noise
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    # Fast global threshold with Otsu
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th


def ocr_image_from_bytes(image_bytes: bytes) -> str:
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        return ''
    proc = preprocess_for_ocr(img)
    # Tesseract config: single line of text is expected (faster)
    config = '--psm 7'
    text = pytesseract.image_to_string(proc, config=config)
    text = text.strip()
    # Normalize to uppercase single line keyword candidate
    text = text.replace('\n', ' ').strip().upper()
    # Keep only letters, numbers, space, hyphen, and apostrophe
    cleaned = []
    for ch in text:
        if ch.isalnum() or ch in [' ', '-', '\'']:
            cleaned.append(ch)
    text = ''.join(cleaned)
    # Heuristic: take longest token group (up to 4 words)
    tokens = [t for t in text.split(' ') if t]
    if not tokens:
        return ''
    # Try to find best matching window up to length 4
    best = ' '.join(tokens[:4])
    if len(tokens) > 4:
        # choose longest token string by length
        candidates = []
        for L in range(1, min(4, len(tokens)) + 1):
            for i in range(0, len(tokens) - L + 1):
                s = ' '.join(tokens[i:i+L])
                candidates.append(s)
        best = max(candidates, key=len)
    return best


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ocr', methods=['POST'])
def ocr_endpoint():
    refresh_data_if_changed()
    # Accept multipart/form-data with field 'frame' (image/jpeg)
    if 'frame' not in request.files:
        return jsonify({'text': ''})
    f = request.files['frame']
    image_bytes = f.read()
    text = ocr_image_from_bytes(image_bytes)
    return jsonify({'text': text})


@app.route('/lookup', methods=['GET'])
def lookup():
    refresh_data_if_changed()
    q = request.args.get('q', '').strip().upper()
    if not q:
        return jsonify({'found': False})
    rec = records_by_keyword.get(q)
    if rec:
        image_path = _resolve_media_path(rec['image_path']) if rec['image_path'] else ''
        image_exists = bool(image_path) and os.path.exists(image_path)
        # Support both YouTube links and local video file paths
        video_link_raw = rec['video_link'] if rec['video_link'] else ''
        resolved_video_path = _resolve_media_path(video_link_raw) if video_link_raw else ''
        is_local_video = bool(resolved_video_path) and os.path.exists(resolved_video_path)
        return jsonify({
            'found': True,
            'category': rec['category'],
            'keyword': rec['keyword'],
            'explanation': rec['explanation'],
            'fun_fact': rec['fun_fact'],
            'image_available': image_exists,
            'image_url': f"/image?q={quote_plus(rec['keyword'])}" if image_exists else '',
            # If local video exists, expose via /video; else, pass through original link for YouTube embedding
            'video_link': video_link_raw if (video_link_raw and not is_local_video) else '',
            'video_available': is_local_video,
            'video_url': f"/video?q={quote_plus(rec['keyword'])}" if is_local_video else '',
            'google_images': f"https://www.google.com/search?tbm=isch&q={quote_plus(rec['keyword'])}",
            'youtube_search': f"https://www.youtube.com/results?search_query={quote_plus(rec['keyword'])}",
        })
    # Not found: still return search URLs for the raw q
    return jsonify({
        'found': False,
        'keyword': q,
        'google_images': f"https://www.google.com/search?tbm=isch&q={quote_plus(q)}",
        'youtube_search': f"https://www.youtube.com/results?search_query={quote_plus(q)}",
    })


@app.route('/image')
def image_serve():
    refresh_data_if_changed()
    q = request.args.get('q', '').strip().upper()
    if not q:
        return ('', 404)
    rec = records_by_keyword.get(q)
    if not rec:
        return ('', 404)
    path = _resolve_media_path(rec.get('image_path', ''))
    if not path or not os.path.exists(path):
        return ('', 404)
    # Let Flask infer mimetype
    return send_file(path)


@app.route('/video')
def video_serve():
    # Support HTTP Range for efficient seeking
    from flask import request, Response
    refresh_data_if_changed()
    q = request.args.get('q', '').strip().upper()
    if not q:
        return ('', 404)
    rec = records_by_keyword.get(q)
    if not rec:
        return ('', 404)
    path = _resolve_media_path(rec.get('video_link', ''))
    if not path or not os.path.exists(path):
        return ('', 404)

    file_size = os.path.getsize(path)
    range_header = request.headers.get('Range', None)
    if not range_header:
        # No range requested; send whole file
        return send_file(path)

    # Parse Range: bytes=start-end
    bytes_unit, _, range_spec = range_header.partition('=')
    if bytes_unit.strip().lower() != 'bytes' or '-' not in range_spec:
        return send_file(path)
    start_str, _, end_str = range_spec.partition('-')
    try:
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1
        end = min(end, file_size - 1)
        length = end - start + 1
        with open(path, 'rb') as f:
            f.seek(start)
            data = f.read(length)
        rv = Response(data, 206, mimetype='video/mp4', direct_passthrough=True)
        rv.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
        rv.headers.add('Accept-Ranges', 'bytes')
        rv.headers.add('Content-Length', str(length))
        return rv
    except Exception:
        return send_file(path)


@app.route('/tts')
def tts():
    text = request.args.get('text', '').strip()
    if not text:
        return ('', 400)
    # Generate speech with gTTS and stream as mp3
    try:
        tts = gTTS(text=text, lang='en')
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return send_file(buf, mimetype='audio/mpeg', as_attachment=False, download_name='tts.mp3')
    except Exception as e:
        return ('', 500)


if __name__ == '__main__':
    # For development
    app.run(host='0.0.0.0', port=5000, debug=True)
