# Flashcard Reader Web App (Flask)

A modern, browser-based flashcard reader using your webcam, OpenCV + Tesseract OCR, CSV-backed flashcards, optional image/video display, Google Images/YouTube fallbacks, and text-to-speech.

## Features
- Webcam OCR with OpenCV preprocessing and Tesseract
- Stability check: requires same detected word for 3 frames before confirming
- CSV lookup (`flashcards2.csv`) for category, explanation, fun fact, image and video
- Auto-displays local image (if path exists) and embeds YouTube (if link provided)
- Fallback quick links to Google Images and YouTube searches
- Text-to-speech via gTTS to read explanation + fun fact
- Clean, responsive dashboard UI

## Requirements
- Python 3.10+
- Tesseract OCR installed on Windows:
  - Download: https://github.com/UB-Mannheim/tesseract/wiki
  - Default path: `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`
  - If installed elsewhere, set an environment variable `TESSERACT_CMD` to the full path of `tesseract.exe` before starting the app.
- The CSV file must exist at `flashcards2.csv` in the project root with columns:
  `category, keyword, explanation, fun_fact, image_path, video_link`

## Setup
```bash
pip install -r requirements.txt
python app.py
```
Then open: http://localhost:5000

If the camera does not start:
- Allow camera permission in your browser.
- On Windows, you may have to enable camera access in Privacy settings.

## Data Notes
- Image paths in your CSV can be absolute (e.g., `D:\\PROJECTS\\FlashcardReader\\images\\gravity.jpeg`) or relative to the project root. This app will serve the file if it exists.
- `video_link` supports direct YouTube links (e.g., `https://www.youtube.com/watch?v=...`) or `youtu.be/...`.

## Text-to-Speech
- gTTS requires internet connectivity.
- To switch to an offline engine like `pyttsx3`, you can add an alternative `/tts` implementation in `app.py`.

## Troubleshooting
- If OCR quality is low, improve lighting and ensure the flashcard title is centered and large in view.
- You can also tweak preprocessing in `preprocess_for_ocr()` in `app.py`.
