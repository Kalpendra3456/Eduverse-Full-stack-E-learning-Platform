# Eduverse-Full-stack-E-learning-Platform
A full-stack e-learning platform enabling teachers to manage courses and students to track their learning progress.

## Eduverse – Full‑stack E‑learning Platform

Eduverse is a minimal full‑stack e‑learning platform with **Student** and **Teacher** roles.
It uses **Flask + MySQL (XAMPP)** on the backend and **React (Vite)** on the frontend.

### 1. Prerequisites

- XAMPP with **MySQL** running
- Python 3.10+
- Node.js + npm

### 2. Database (MySQL via XAMPP)

1. Open XAMPP Control Panel and start **MySQL** (and **Apache** if you want phpMyAdmin).
2. In phpMyAdmin, create a database named **`eduverse`**.

### 3. Backend Setup (Flask)

From project root:

```bash
cd backend
```

Create a `.env` file in `backend`:

```env
FLASK_ENV=development
FLASK_DEBUG=1

DB_HOST=localhost
DB_PORT=3306
DB_NAME=eduverse
DB_USER=root
DB_PASSWORD=      # leave empty if root has no password

JWT_SECRET_KEY=your_jwt_secret_here

# OpenAI API key for Whisper transcription and GPT-based summary/quiz generation
OPENAI_API_KEY=your_openai_api_key_here

UPLOAD_FOLDER=uploads
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Run the Flask API (from **project root**, not inside `backend`):

```bash
python -m backend.app
```

The API will be available at `http://localhost:5000/api/...`.
Uploaded files (videos + notes) are written to `<project>/backend/uploads/...` and
served via `http://localhost:5000/uploads/<type>/<filename>`.

**Important Requirements:**
- **ffmpeg**: Required for audio extraction from videos. Install from https://ffmpeg.org/download.html
- **OpenAI API Key**: Required for Whisper transcription and AI-powered summary/quiz generation.
  Get your key from https://platform.openai.com/api-keys

**How it works:**
1. Teacher uploads a video → stored locally
2. Backend extracts audio from video using ffmpeg
3. Audio is transcribed using OpenAI Whisper API
4. Transcript is summarized using OpenAI GPT API
5. Summary is stored in the database
6. When a student watches the video, a quiz is generated from the summary using GPT API

> **Schema note:** lessons store transcripts, summaries, and quiz history.
> If you ran an older version, drop & recreate the database (or add the new columns
> `summary_text`, `video_storage_path` to `lessons` and `summary_snapshot` to `quizzes`).
> Remove `youtube_video_id` column from `lessons` if it exists.

### 4. Frontend Setup (React + Vite)

From project root:

```bash
cd frontend
npm install
```

Create `frontend/.env` to point to the backend API:

```env
VITE_API_BASE_URL=http://localhost:5000
```

Run the React dev server:

```bash
npm run dev
```

Open the URL shown in the terminal (usually `http://localhost:5173`) in your browser.

### 5. Core Features (Implemented)

- **Auth with JWT**: register/login as student or teacher.
- **Teacher dashboard**:
  - Create courses, upload lesson assets.
  - Videos are uploaded to YouTube automatically using your OAuth credentials (link stored in MySQL).
  - Backend auto-transcribes locally, saves transcripts & AI-style summaries.
  - Real-time stats: enrollment counts and quiz performance averages per course.
- **Student dashboard**:
  - View enrolled courses, embedded videos, downloadable notes, and AI summary text.
  - “Watch & generate quiz” creates a fresh quiz every time the video is watched, based on the saved summary.
  - Dashboard lists historical quiz attempts (score + date).
- **MySQL storage**:
  - Users, courses, lessons (with transcripts, summaries, storage paths), enrollments,
    quizzes (with summary snapshot), quiz questions, quiz attempts, quiz answers.


