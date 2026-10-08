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
2. <img width="1915" height="971" alt="image" src="https://github.com/user-attachments/assets/04792fa2-0165-42c2-8a20-400be9c7f29d" />

3. Backend extracts audio from video using ffmpeg
4. Audio is transcribed using OpenAI Whisper API
5. Transcript is summarized using OpenAI GPT API
6. Summary is stored in the database
7. When a student watches the video, a quiz is generated from the summary using GPT API

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
  - <img width="1910" height="938" alt="image" src="https://github.com/user-attachments/assets/b8f746fc-7330-4f89-8dcc-e9ab6e8a1f22" />
  <img width="1912" height="947" alt="image" src="https://github.com/user-attachments/assets/63f62319-0efe-4a96-a307-db2baddae4a9" />


  - Videos are uploaded to YouTube automatically using your OAuth credentials (link stored in MySQL).
  - Backend auto-transcribes locally, saves transcripts & AI-style summaries.
  - Real-time stats: enrollment counts and quiz performance averages per course.
- **Student dashboard**:
- <img width="1915" height="971" alt="image" src="https://github.com/user-attachments/assets/2ed45a96-5540-4ab8-99d6-336633a2d48b" />

<img width="1911" height="911" alt="image" src="https://github.com/user-attachments/assets/7dc9343f-c182-4ef3-b143-bfc18956945e" />


<img width="1915" height="971" alt="image" src="https://github.com/user-attachments/assets/bdbb3da0-b1bc-4931-a05f-74065e448412" />


  - View enrolled courses, embedded videos, downloadable notes, and AI summary text.
  - <img width="1915" height="957" alt="image" src="https://github.com/user-attachments/assets/ff9755e6-b5ec-4cd1-8869-304b09c3c04c" />
  <img width="1778" height="748" alt="image" src="https://github.com/user-attachments/assets/4c61865f-9d30-4ce0-bed2-e426f49f5858" />


  - 
  - “Watch & generate quiz” creates a fresh quiz every time the video is watched, based on the saved summary.
  - <img width="1913" height="975" alt="image" src="https://github.com/user-attachments/assets/bc7bb7f5-ba35-4613-9dd6-6e60e5ed185c" />

  - Dashboard lists historical quiz attempts (score + date).
  - <img width="1915" height="957" alt="image" src="https://github.com/user-attachments/assets/4fdfe14e-8aa4-4ed7-9991-50aac1aec817" />

- **MySQL storage**:
  - Users, courses, lessons (with transcripts, summaries, storage paths), enrollments,
    quizzes (with summary snapshot), quiz questions, quiz attempts, quiz answers.


