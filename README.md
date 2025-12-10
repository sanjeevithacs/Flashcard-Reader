# Flashcard-Reader

A modern, interactive flashcard application that uses computer vision and natural language processing to enhance learning. The app uses your webcam to scan flashcard titles and displays relevant information including explanations, fun facts, images, and videos.

## Features

- **Webcam OCR Integration**: Uses OpenCV and Tesseract OCR to read flashcard titles
- **Smart Detection**: Stability check requires consistent word detection across multiple frames
- **Rich Media Support**:
  - Local image display
  - YouTube video embedding
  - Google Images/YouTube search fallbacks
- **Audio Learning**: Text-to-speech for explanations and fun facts
- **Responsive Design**: Works on desktop and mobile browsers

## Prerequisites

- Python 3.10 or higher
- Tesseract OCR installed on your system
- Webcam access

## Installation

1. **Install Tesseract OCR**:
   - Windows: Download from [UB Mannheim's Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
   - macOS: `brew install tesseract`
   - Linux: `sudo apt install tesseract-ocr`

2. **Clone the repository**:
   ```bash
   git clone https://github.com/sanjeevithacs/Flashcard-Reader.git
   cd Flashcard-Reader

3. **Set up the environment**:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
python app.py
```

2. Open your browser and navigate to:
http://localhost:5000

3. Grant camera permissions when prompted
4. Show a flashcard to the camera to see its contents



## Project Structure

```
FlashcardReader/
├── app.py              # Main application file
├── main2.py            # Secondary application file
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── flashcards2.csv     # Flashcard database
├── static/             # Static files (CSS, JS)
├── templates/          # HTML templates
├── images/             # Local images for flashcards
└── videos/             # Local videos for flashcards

```

## Output ScreenShot

<img width="1243" height="421" alt="Screenshot 2025-11-26 112519" src="https://github.com/user-attachments/assets/eb92e6e1-2cb4-4d60-b409-aba8dbea321e" />

<img width="1250" height="640" alt="Screenshot 2025-11-26 112611" src="https://github.com/user-attachments/assets/549bdcff-890c-46b3-9b59-07a80534bfc5" />



## Flashcard Format
The application reads from flashcards2.csv with the following columns:
- **category**: Category of the flashcard
- **keyword**: The word or phrase to detect
- **explanation**: Detailed explanation
- **fun_fact**: Interesting fact about the topic
- **image_path**: Path to local image (relative or absolute)
- **video_link**: YouTube URL or local video path


## Tips for Best Results
- Ensure good lighting when scanning cards
- Keep the flashcard steady for 1-2 seconds
- Use clear, large text on your flashcards
- For best OCR results, use high contrast text


## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.


## License
This project is licensed under the MIT License - see the LICENSE file for details.
