# 🎓 Eduverse – Full-Stack AI E-Learning Platform

Eduverse is a full-stack e-learning platform that connects **teachers and students** through course management, video-based learning, AI-generated summaries, and AI-powered quizzes.

Teachers can create courses and upload learning materials, while students can watch lessons, access notes and summaries, generate quizzes, and track their quiz performance.

---

## 🚀 Key Features

### 👨‍🏫 Teacher

- Register and login with JWT authentication
- Create and manage courses
- Upload lesson videos and notes
- Automatic video upload to YouTube
- Automatic audio extraction using FFmpeg
- AI-powered video transcription using OpenAI Whisper
- AI-generated lesson summaries
- View course enrollment statistics
- Track average quiz performance

### 👨‍🎓 Student

- Register and login securely
- Browse and enroll in courses
- Watch lesson videos
- Download lesson notes
- Read AI-generated summaries
- Generate quizzes from lesson content
- Submit quizzes and receive scores
- View previous quiz attempts and performance history

### 🤖 AI Features

- Video → Audio extraction
- Audio → Text transcription
- AI-generated lesson summaries
- AI-generated quizzes from lesson summaries
- Fresh quiz generation for each attempt

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite |
| Backend | Python, Flask |
| Database | MySQL |
| Authentication | JWT |
| AI | OpenAI Whisper, OpenAI GPT |
| Video Processing | FFmpeg |
| Video Hosting | YouTube API |
| Development Environment | XAMPP |
| API Communication | REST API |

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │     React + Vite    │
                    │      Frontend       │
                    └──────────┬──────────┘
                               │
                               │ REST API
                               ▼
                    ┌─────────────────────┐
                    │      Flask API      │
                    │      Backend        │
                    └──────┬─────┬────────┘
                           │     │
                ┌──────────┘     └─────────────┐
                ▼                              ▼
        ┌───────────────┐              ┌────────────────┐
        │     MySQL     │              │   OpenAI API   │
        │   Database    │              │ Whisper + GPT  │
        └───────────────┘              └───────┬────────┘
                                               │
                                               ▼
                                        AI Summary / Quiz

                           ┌────────────────┐
                           │     FFmpeg     │
                           │ Audio Extract  │
                           └────────────────┘

                           ┌────────────────┐
                           │   YouTube API  │
                           │ Video Hosting  │
                           └────────────────┘
```

---

## 🔄 How It Works

### Teacher Upload Flow

```text
Teacher uploads video
        ↓
Video stored by backend
        ↓
FFmpeg extracts audio
        ↓
OpenAI Whisper transcribes audio
        ↓
GPT generates lesson summary
        ↓
Summary stored in MySQL
        ↓
Video uploaded to YouTube
        ↓
YouTube video ID stored in database
```

### Student Learning Flow

```text
Student enrolls in course
        ↓
Watches lesson
        ↓
Reads notes + AI summary
        ↓
Generates quiz
        ↓
GPT creates quiz from lesson summary
        ↓
Student submits answers
        ↓
Score calculated
        ↓
Attempt stored in MySQL
        ↓
Performance displayed on dashboard
```

---

## 🗄️ Database Structure

The application uses MySQL to manage users, courses, lessons, enrollments, quizzes, and student performance.

### Main Tables

```text
users
courses
lessons
enrollments
quizzes
quiz_questions
quiz_attempts
quiz_answers
```

Lessons contain:

- Video information
- Transcripts
- AI-generated summaries
- Video storage information

Quiz records contain:

- Quiz questions
- Summary snapshot
- Student attempts
- Answers
- Scores

---

# ⚙️ Installation & Setup

## 1. Prerequisites

Install the following:

- Python 3.10+
- Node.js and npm
- XAMPP
- FFmpeg
- OpenAI API Key

---

## 2. Clone Repository

```bash
git clone https://github.com/your-username/Eduverse-Full-stack-E-learning-Platform.git

cd Eduverse-Full-stack-E-learning-Platform
```

---

## 3. Database Setup

Open **XAMPP Control Panel** and start:

```text
MySQL
```

Start Apache as well if you want to use phpMyAdmin.

Create a database:

```sql
CREATE DATABASE eduverse;
```

---

# 🔧 Backend Setup

Navigate to the project root and create the backend environment file:

```text
backend/.env
```

Add:

```env
FLASK_ENV=development
FLASK_DEBUG=1

DB_HOST=localhost
DB_PORT=3306
DB_NAME=eduverse
DB_USER=root
DB_PASSWORD=

JWT_SECRET_KEY=your_jwt_secret_here

OPENAI_API_KEY=your_openai_api_key_here

UPLOAD_FOLDER=uploads
```

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

Run the Flask backend from the **project root**:

```bash
python -m backend.app
```

Backend API:

```text
http://localhost:5000
```

---

# 🎨 Frontend Setup

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create:

```text
frontend/.env
```

Add:

```env
VITE_API_BASE_URL=http://localhost:5000
```

Start the development server:

```bash
npm run dev
```

Frontend will normally run at:

```text
http://localhost:5173
```

---

# 🎥 Video Processing

Eduverse uses **FFmpeg** to extract audio from uploaded videos.

The processing pipeline is:

```text
Video
  ↓
FFmpeg
  ↓
Audio
  ↓
OpenAI Whisper
  ↓
Transcript
  ↓
OpenAI GPT
  ↓
Summary
```

Make sure FFmpeg is installed and available in your system PATH.

---

# 🤖 AI-Powered Learning

Eduverse uses AI to reduce manual work for teachers and improve the student learning experience.

### AI Summary

A lesson video is transcribed and summarized automatically so students can quickly review the important concepts.

### AI Quiz Generation

The saved lesson summary is provided to the AI model to generate quiz questions.

This allows students to test their understanding without requiring teachers to manually create every quiz.

---

# 🔐 Authentication

The platform uses **JWT-based authentication**.

Users can register and login as:

```text
Student
Teacher
```

Role-based access controls which features and dashboards each user can access.

---

# 📊 Dashboards

### Teacher Dashboard

Teachers can monitor:

- Total courses
- Course enrollments
- Quiz performance
- Lesson content
- Uploaded learning materials

### Student Dashboard

Students can view:

- Enrolled courses
- Available lessons
- Videos
- Notes
- AI summaries
- Quiz scores
- Previous quiz attempts

---

# 📸 Screenshots

## Teacher Dashboard

Add your screenshots here:


<img width="1873" height="930" alt="Screenshot 2026-10-08 163415" src="https://github.com/user-attachments/assets/429506ec-8dd3-49a1-a379-4e3bed54af66" />
<img width="1917" height="930" alt="Screenshot 2026-10-08 163548" src="https://github.com/user-attachments/assets/493ab71c-3ecc-45be-afae-e5a5ffa81bcc" />


<img width="1910" height="938" alt="Screenshot 2026-10-08 160338" src="https://github.com/user-attachments/assets/f73acb2b-f813-4371-ac1e-8b359bbf85de" />



## Student Dashboard

<img width="1915" height="971" alt="Screenshot 2026-10-08 144631" src="https://github.com/user-attachments/assets/e78bc510-4317-4fe5-97f9-f1a1eb01c528" />

## Course / Lesson Page


<img width="1915" height="957" alt="Screenshot 2026-10-08 160209" src="https://github.com/user-attachments/assets/82ca3d54-c119-44e0-88c9-7e7f0b6e7b4c" />
<img width="1907" height="938" alt="Screenshot 2026-10-08 160546" src="https://github.com/user-attachments/assets/6c4f2cb6-836a-404d-ad54-52e1b1eb5c3d" />



## AI Quiz


<img width="1913" height="975" alt="Screenshot 2026-10-08 155935" src="https://github.com/user-attachments/assets/14f2ecea-ff15-47a4-9632-99510701359d" />
<img width="1915" height="957" alt="Screenshot 2026-10-08 160059" src="https://github.com/user-attachments/assets/48acc50a-2a19-47b0-b360-a226b2b13748" />
<img width="1778" height="748" alt="Screenshot 2026-10-08 160232" src="https://github.com/user-attachments/assets/f7675e3f-8891-44d0-a904-ce4a5014c9c0" />




---

# 🔮 Future Improvements

Some planned improvements include:

- 📈 Advanced student performance analytics
- 🧠 Personalized learning recommendations
- 💬 AI learning assistant
- 📚 AI-generated study plans
- 🎯 Adaptive quizzes based on student performance
- 🔔 Learning reminders and notifications
- 🏆 Student achievements and badges
- 📱 Mobile application
- ☁️ Cloud-based video storage
- 🔒 Production-level authentication and security
- ⚡ Background processing for video transcription
- 📊 Advanced teacher analytics

---

# 📁 Project Structure

```text
Eduverse-Full-stack-E-learning-Platform/
│
├── backend/
│   ├── app/
│   ├── uploads/
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env
│
├── screenshots/
│
├── README.md
└── .gitignore
```

---

# ⚠️ Environment Variables

Never commit your API keys or secrets to GitHub.

Make sure `.env` is included in `.gitignore`:

```gitignore
.env
backend/.env
frontend/.env
__pycache__/
*.pyc
node_modules/
uploads/
```

---

# 👨‍💻 Developer

**Kalpendra Yadav**

MCA Graduate | Data Analyst | Power BI Developer | Full-Stack Developer

### Skills Used

```text
React • Python • Flask • MySQL • REST API
JWT • OpenAI API • FFmpeg • JavaScript
```

---

## ⭐ Project Highlights

> Eduverse combines **full-stack development, AI, video processing, and data-driven learning** into a single e-learning platform.

The project demonstrates practical implementation of:

- Full-stack web development
- REST API development
- Authentication & authorization
- Relational database design
- AI API integration
- Video processing
- Automated content generation
- Student performance tracking

---

## 📄 License

This project is developed for Academic project.
