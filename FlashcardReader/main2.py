import cv2
import pytesseract
import pandas as pd
import pyttsx3
import time
import threading
import webbrowser
import os

# Path to Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load flashcards dataset
df = pd.read_csv('flashcards2.csv')

print("Press 'Q' in the video window to quit.")

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine.stop()

REQUIRED_STABLE_FRAMES = 3

while True:
    cap = cv2.VideoCapture(0)
    detected = False
    text = ""
    prev_text = ""
    stable_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray).strip().upper()

        # Overlay detected text on the video
        display_text = text if text else "Detecting..."
        cv2.putText(frame, display_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow("Flashcard Reader", frame)

        if text:
            if text == prev_text:
                stable_count += 1
            else:
                stable_count = 1
                prev_text = text

            if stable_count >= REQUIRED_STABLE_FRAMES:
                cap.release()
                cv2.destroyAllWindows()

                match = df[df['keyword'].str.upper() == text]

                if not match.empty:
                    category = match.iloc[0]['category']
                    explanation = match.iloc[0]['explanation']
                    fun_fact = match.iloc[0]['fun_fact']

                    print(f"[{category}] {text}: {explanation}")
                    print(f"Fun Fact: {fun_fact}")

                    speech_text = f"{category} - {text}: {explanation}. Fun fact: {fun_fact}"
                    threading.Thread(target=speak, args=(speech_text,)).start()

                    # Show image if available, else open Google Images search
                    if 'image_path' in match.columns:
                        img_path = match.iloc[0]['image_path']
                        if pd.notna(img_path) and os.path.exists(img_path):
                            img = cv2.imread(img_path)
                            cv2.imshow("Flashcard Image", img)
                            cv2.waitKey(2000)
                            cv2.destroyWindow("Flashcard Image")
                        else:
                            webbrowser.open(f"https://www.google.com/search?tbm=isch&q={text}")

                    # Open video link if available, else open YouTube search
                    if 'video_link' in match.columns:
                        video_link = match.iloc[0]['video_link']
                        if pd.notna(video_link):
                            webbrowser.open(video_link)
                        else:
                            webbrowser.open(f"https://www.youtube.com/results?search_query={text}")

                else:
                    print(f"Flashcard '{text}' not found in database.")
                    threading.Thread(target=speak, args=(f"Flashcard {text} not found",)).start()
                    # Open web search for unknown flashcards
                    webbrowser.open(f"https://www.google.com/search?q={text}")

                detected = True
                break
        else:
            stable_count = 0
            prev_text = ""

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            detected = True
            text = None
            break

        time.sleep(0.2)

    if text is None:
        break

    if detected:
        print("Show next flashcard...")
        time.sleep(1)
