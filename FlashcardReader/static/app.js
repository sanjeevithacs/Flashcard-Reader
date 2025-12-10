let stream = null;
let intervalId = null;
let stabilityCount = 0;
let lastText = '';
let ocrInFlight = false;
const REQUIRED_STABLE_FRAMES = 3;

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const detectedTextEl = document.getElementById('detectedText');
const stabilityBar = document.getElementById('stabilityBar');
const videoWrap = document.getElementById('videoWrap');

const categoryPill = document.getElementById('categoryPill');
const keywordTitle = document.getElementById('keywordTitle');
const explanationEl = document.getElementById('explanation');
const funFactEl = document.getElementById('funFact');
const imageDisplay = document.getElementById('imageDisplay');
const videoContainer = document.getElementById('videoContainer');
const localVideo = document.getElementById('localVideo');
const googleImagesLink = document.getElementById('googleImagesLink');
const youtubeSearchLink = document.getElementById('youtubeSearchLink');
const ttsAudio = document.getElementById('ttsAudio');

const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');

function setStableUI(isStable) {
  if (isStable) {
    videoWrap.classList.add('stable');
  } else {
    videoWrap.classList.remove('stable');
  }
}

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false
    });
    video.srcObject = stream;
    await video.play();

    // Start OCR polling
    if (!intervalId) {
      intervalId = setInterval(captureAndSendFrame, 350);
    }
  } catch (err) {
    alert('Could not access camera: ' + err.message);
  }
}

function stopCamera() {
  if (intervalId) {
    clearInterval(intervalId);
    intervalId = null;
  }
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
  setStableUI(false);
}

async function captureAndSendFrame() {
  if (!video.videoWidth || !video.videoHeight) return;
  if (ocrInFlight) return;
  ocrInFlight = true;
  // Downscale to max width 640 to reduce bandwidth/CPU
  const maxW = 640;
  const scale = Math.min(1, maxW / video.videoWidth);
  canvas.width = Math.round(video.videoWidth * scale);
  canvas.height = Math.round(video.videoHeight * scale);
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  const blob = await new Promise(res => canvas.toBlob(res, 'image/jpeg', 0.5));
  const formData = new FormData();
  formData.append('frame', blob, 'frame.jpg');

  try {
    const r = await fetch('/ocr', { method: 'POST', body: formData });
    const data = await r.json();
    const text = (data.text || '').trim();

    if (text.length > 0) {
      detectedTextEl.textContent = text;
      if (text === lastText) {
        stabilityCount = Math.min(REQUIRED_STABLE_FRAMES, stabilityCount + 1);
      } else {
        lastText = text;
        stabilityCount = 1;
      }
    } else {
      detectedTextEl.textContent = '–';
      lastText = '';
      stabilityCount = 0;
    }

    const pct = Math.round((stabilityCount / REQUIRED_STABLE_FRAMES) * 100);
    stabilityBar.style.width = pct + '%';

    if (stabilityCount >= REQUIRED_STABLE_FRAMES && text) {
      setStableUI(true);
      await onStableKeyword(text);
      // reset to require a fresh stable detection to trigger again
      stabilityCount = 0;
      lastText = '';
      setTimeout(() => setStableUI(false), 1200);
    }
  } catch (e) {
    console.error(e);
  } finally {
    ocrInFlight = false;
  }
}

function embedYouTube(url) {
  try {
    const u = new URL(url);
    if (u.hostname.includes('youtube.com')) {
      const v = u.searchParams.get('v');
      if (v) return `https://www.youtube.com/embed/${v}`;
    }
    if (u.hostname === 'youtu.be') {
      const id = u.pathname.replace('/', '');
      if (id) return `https://www.youtube.com/embed/${id}`;
    }
  } catch {}
  return '';
}

async function onStableKeyword(keyword) {
  try {
    const r = await fetch(`/lookup?q=${encodeURIComponent(keyword)}`);
    const data = await r.json();

    if (data.found) {
      categoryPill.textContent = data.category || 'Category';
      keywordTitle.textContent = data.keyword || keyword;
      explanationEl.textContent = data.explanation || '';
      funFactEl.textContent = data.fun_fact || '';

      // Image
      if (data.image_available && data.image_url) {
        imageDisplay.src = data.image_url;
        imageDisplay.classList.remove('hidden');
      } else {
        imageDisplay.src = '';
        imageDisplay.classList.add('hidden');
      }

      // Video handling: prefer local video if available, else try YouTube embed
      // Reset
      localVideo.classList.add('hidden');
      localVideo.removeAttribute('src');
      localVideo.load();
      videoContainer.innerHTML = '';
      videoContainer.classList.add('hidden');

      if (data.video_available && data.video_url) {
        // Local video served by Flask
        localVideo.src = data.video_url;
        localVideo.classList.remove('hidden');
      } else {
        const embed = data.video_link ? embedYouTube(data.video_link) : '';
        if (embed) {
          const iframe = document.createElement('iframe');
          iframe.src = embed;
          iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
          iframe.allowFullscreen = true;
          videoContainer.appendChild(iframe);
          videoContainer.classList.remove('hidden');
        }
      }

      // Links
      googleImagesLink.href = data.google_images;
      youtubeSearchLink.href = data.youtube_search;

      // Speak
      const speakText = [data.explanation, data.fun_fact].filter(Boolean).join('. ');
      if (speakText) {
        const ttsResp = await fetch(`/tts?text=${encodeURIComponent(speakText)}`);
        if (ttsResp.ok) {
          const blob = await ttsResp.blob();
          ttsAudio.src = URL.createObjectURL(blob);
          ttsAudio.play().catch(() => {});
        }
      }
    } else {
      categoryPill.textContent = 'Not found';
      keywordTitle.textContent = data.keyword || keyword;
      explanationEl.textContent = 'No match in your CSV. Use the links to explore.';
      funFactEl.textContent = '';
      imageDisplay.classList.add('hidden');
      videoContainer.classList.add('hidden');
      googleImagesLink.href = data.google_images;
      youtubeSearchLink.href = data.youtube_search;

      // Speak not found feedback
      const nf = `Not found: ${keyword}. Opening Google Images and YouTube links.`;
      const ttsResp = await fetch(`/tts?text=${encodeURIComponent(nf)}`);
      if (ttsResp.ok) {
        const blob = await ttsResp.blob();
        ttsAudio.src = URL.createObjectURL(blob);
        ttsAudio.play().catch(() => {});
      }
    }
  } catch (e) {
    console.error(e);
  }
}

startBtn.addEventListener('click', startCamera);
stopBtn.addEventListener('click', stopCamera);
