
import os
from datetime import timedelta
from uuid import uuid4

from flask import Flask, jsonify, request, g, send_from_directory, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename

from .config import load_config
from .extensions import db
from .models import (
    User,
    Course,
    Lesson,
    Enrollment,
    Quiz,
    QuizQuestion,
    QuizAttempt,
    QuizAttemptAnswer,
)
from .utils_jwt import create_access_token, decode_access_token
# Revert to utils_transcription based on user request "switch whisper to elevenlabs"
from .utils_transcription import transcribe_video
from .utils_summary import summarize_transcript
from .utils_quiz import generate_quiz_questions_from_text
from .recommender import recommend
from .support_helper import generate_explanation, chat_with_ai

# Fix: Programmatically add ffmpeg to PATH so libraries like whisper can find it
import shutil
if not shutil.which("ffmpeg"):
    try:
        import imageio_ffmpeg
        ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
        if ffmpeg_dir not in os.environ["PATH"]:
            os.environ["PATH"] += os.pathsep + ffmpeg_dir
            print(f"DEBUG: Added imageio-ffmpeg to PATH: {ffmpeg_dir}")
    except Exception as e:
        print(f"WARNING: Could not add ffmpeg to PATH: {e}")
else:
    print(f"DEBUG: ffmpeg already in PATH: {shutil.which('ffmpeg')}")


def create_app() -> Flask:
    app = Flask(__name__)
    cfg = load_config()
    upload_folder = os.path.join(os.path.dirname(__file__), cfg.UPLOAD_FOLDER)
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(os.path.join(upload_folder, "videos"), exist_ok=True)
    os.makedirs(os.path.join(upload_folder, "notes"), exist_ok=True)

    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=cfg.SQLALCHEMY_DATABASE_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=cfg.SQLALCHEMY_TRACK_MODIFICATIONS,
        JWT_SECRET_KEY=cfg.JWT_SECRET_KEY,
        ENV=cfg.ENV,
        DEBUG=cfg.DEBUG,
        UPLOAD_FOLDER=upload_folder,
    )

    CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "*"}})

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.before_request
    def load_current_user():
        g.current_user = None
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return
        token = auth_header.split(" ", 1)[1]
        payload = decode_access_token(token, app.config["JWT_SECRET_KEY"])
        if not payload:
            return
        user_id = payload.get("sub")
        if not user_id:
            return
        try:
            user = db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return
        g.current_user = user

    # --- Support API ---
    @app.route("/api/support/recommend", methods=["POST", "OPTIONS"])
    def support_recommend():
        if request.method == "OPTIONS":
            return jsonify({"status": "ok"}), 200
        data = request.get_json() or {}
        query = data.get("query", "")
        if not query:
            return jsonify({"results": [], "explanation": ""})
        try:
            results = recommend(query)
            explanation = generate_explanation(query)
            return jsonify({"results": results, "explanation": explanation})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/support/chat", methods=["POST", "OPTIONS"])
    def support_chat():
        if request.method == "OPTIONS":
            return jsonify({"status": "ok"}), 200
        try:
            data = request.get_json() or {}
            user_input = data.get("message", "")
            if not user_input:
                return jsonify({"reply": "Please say something!"})
            reply = chat_with_ai(user_input)
            return jsonify({"reply": reply})
        except Exception as e:
            return jsonify({"reply": f"Error: {str(e)}"})

    def require_auth(role: str | None = None):
        if g.current_user is None:
            return jsonify({"message": "Unauthorized"}), 401
        if role and g.current_user.role != role:
            return jsonify({"message": "Forbidden"}), 403
        return None

    def _delete_lesson_data(lesson):
        """Helper to delete lesson files and associated quiz data."""
        # Delete associated files from filesystem
        if lesson.video_storage_path and os.path.exists(lesson.video_storage_path):
            try:
                os.remove(lesson.video_storage_path)
            except Exception:
                pass  # Continue even if file deletion fails

        if lesson.notes_url:
            notes_path = os.path.join(
                app.config["UPLOAD_FOLDER"], "notes", os.path.basename(lesson.notes_url)
            )
            if os.path.exists(notes_path):
                try:
                    os.remove(notes_path)
                except Exception:
                    pass

        # Associated quizzes, attempts, and questions are deleted via cascade
        db.session.delete(lesson)



    @app.route("/api/auth/register", methods=["POST"])
    def register():
        # Handle multipart/form-data
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        
        # Fallback to JSON if form data is empty
        if not all([name, email, password, role]):
            data = request.get_json() or {}
            name = data.get("name")
            email = data.get("email")
            password = data.get("password")
            role = data.get("role")

        if not all([name, email, password, role]):
            return jsonify({"message": "Missing required fields"}), 400
        if role not in ("student", "teacher"):
            return jsonify({"message": "Invalid role"}), 400

        existing = User.query.filter_by(email=email).first()
        if existing:
            return jsonify({"message": "Email already registered"}), 400

        profile_image_url = None
        profile_file = request.files.get("profile_image")
        if profile_file and profile_file.filename:
            filename = f"profile_{uuid4().hex}_{secure_filename(profile_file.filename)}"
            profile_dir = os.path.join(app.config["UPLOAD_FOLDER"], "profiles")
            os.makedirs(profile_dir, exist_ok=True)
            profile_path = os.path.join(profile_dir, filename)
            profile_file.save(profile_path)
            profile_image_url = f"/uploads/profiles/{filename}"

        from passlib.hash import bcrypt

        user = User(
            name=name,
            email=email,
            password_hash=bcrypt.hash(password),
            role=role,
            profile_image=profile_image_url
        )
        db.session.add(user)
        db.session.commit()

        return jsonify({"message": "User registered successfully"}), 201

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = request.get_json() or {}
        email = data.get("email")
        password = data.get("password")

        if not all([email, password]):
            return jsonify({"message": "Missing required fields"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"message": "Invalid credentials"}), 401

        from passlib.hash import bcrypt

        if not bcrypt.verify(password, user.password_hash):
            return jsonify({"message": "Invalid credentials"}), 401

        access_token = create_access_token(
            {"sub": str(user.id), "role": user.role},
            app.config["JWT_SECRET_KEY"],
            expires_delta=timedelta(hours=8),
        )
        return jsonify(
            {
                "access_token": access_token,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                },
            }
        )

    @app.route("/api/auth/forgot-password", methods=["POST"])
    def forgot_password():
        data = request.get_json() or {}
        email = data.get("email")
        if not email:
            return jsonify({"message": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            # We return 200 even if user not found for security reasons
            return jsonify({"message": "If an account with that email exists, a reset link has been sent."}), 200

        import secrets
        from datetime import datetime, timedelta
        
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        # In a real app, you'd send an email here. 
        # For now, we'll just log it or return it for demonstration (if debugging)
        print(f"DEBUG: Password reset token for {email}: {token}")
        
        return jsonify({"message": "If an account with that email exists, a reset link has been sent.", "debug_token": token}), 200

    @app.route("/api/auth/reset-password", methods=["POST"])
    def reset_password():
        data = request.get_json() or {}
        token = data.get("token")
        new_password = data.get("new_password")

        if not all([token, new_password]):
            return jsonify({"message": "Token and new password are required"}), 400

        from datetime import datetime
        user = User.query.filter(
            User.reset_token == token,
            User.reset_token_expiry > datetime.utcnow()
        ).first()

        if not user:
            return jsonify({"message": "Invalid or expired token"}), 400

        from passlib.hash import bcrypt
        user.password_hash = bcrypt.hash(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        return jsonify({"message": "Password reset successfully"}), 200

    @app.route("/api/teacher/courses", methods=["POST"])
    def create_course():
        auth_error = require_auth(role="teacher")
        if auth_error:
            return auth_error

        data = request.get_json() or {}
        title = data.get("title")
        description = data.get("description")
        if not title:
            return jsonify({"message": "Title is required"}), 400

        course = Course(title=title, description=description, teacher_id=g.current_user.id)
        db.session.add(course)
        db.session.commit()

        return jsonify({"id": course.id, "title": course.title, "description": course.description}), 201

    @app.route("/api/teacher/courses", methods=["GET"])
    def list_teacher_courses():
        auth_error = require_auth(role="teacher")
        if auth_error:
            return auth_error

        courses = Course.query.filter_by(teacher_id=g.current_user.id).all()
        response = []
        for c in courses:
            enrollment_count = Enrollment.query.filter_by(course_id=c.id).count()
            response.append(
                {
                    "id": c.id,
                    "title": c.title,
                    "description": c.description,
                    "enrollment_count": enrollment_count,
                }
            )
        return jsonify(response)
    
    @app.route("/api/courses/<int:course_id>", methods=["DELETE"])
    def delete_course(course_id: int):
        auth_error = require_auth(role="teacher")
        if auth_error:
            return auth_error

        course = db.session.get(Course, course_id)
        if not course:
            return jsonify({"message": "Course not found"}), 404
        
        if course.teacher_id != g.current_user.id:
            return jsonify({"message": "Forbidden"}), 403

        # Delete enrollments
        Enrollment.query.filter_by(course_id=course.id).delete()
        
        # Delete lessons and their data
        lessons = Lesson.query.filter_by(course_id=course.id).all()
        for lesson in lessons:
            _delete_lesson_data(lesson)
        
        # Delete the course itself
        db.session.delete(course)
        db.session.commit()

        return jsonify({"message": "Course deleted successfully"}), 200

    @app.route("/api/courses", methods=["GET"])
    def list_courses():
        courses = Course.query.all()
        return jsonify(
            [
                {
                    "id": c.id,
                    "title": c.title,
                    "description": c.description,
                    "teacher": c.teacher.name if c.teacher else None,
                    "teacher_profile_image": c.teacher.profile_image if c.teacher else None,
                }
                for c in courses
            ]
        )

    @app.route("/api/courses/<int:course_id>", methods=["GET"])
    def get_course(course_id: int):
        course = db.session.get(Course, course_id)
        if not course:
            return jsonify({"message": "Course not found"}), 404

        lessons = Lesson.query.filter_by(course_id=course.id).all()
        return jsonify(
            {
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "teacher": course.teacher.name if course.teacher else None,
                "lessons": [
                    {
                        "id": l.id,
                        "title": l.title,
                        "video_url": l.video_url,
                        "notes_url": l.notes_url,
                        "summary": l.summary_text,
                    }
                    for l in lessons
                ],
            }
        )

    @app.route("/api/courses/<int:course_id>/enroll", methods=["POST"])
    def enroll_in_course(course_id: int):
        auth_error = require_auth(role="student")
        if auth_error:
            return auth_error

        course = db.session.get(Course, course_id)
        if not course:
            return jsonify({"message": "Course not found"}), 404

        existing = Enrollment.query.filter_by(
            student_id=g.current_user.id, course_id=course.id
        ).first()
        if existing:
            return jsonify({"message": "Already enrolled"}), 200

        enrollment = Enrollment(student_id=g.current_user.id, course_id=course.id)
        db.session.add(enrollment)
        db.session.commit()

        return jsonify({"message": "Enrolled successfully"}), 201

    @app.route("/api/student/courses", methods=["GET"])
    def get_student_courses():
        auth_error = require_auth(role="student")
        if auth_error:
            return auth_error

        enrollments = Enrollment.query.filter_by(student_id=g.current_user.id).all()
        
        response = []
        for e in enrollments:
            if not e.course:
                continue
                
            course = e.course
            total_lessons = Lesson.query.filter_by(course_id=course.id).count()
            
            # Completed lessons: lessons with at least one quiz attempt by this student
            # We can find this by joining QuizAttempt -> Quiz -> Lesson
            completed_count = (
                db.session.query(Lesson.id)
                .join(Quiz, Quiz.lesson_id == Lesson.id)
                .join(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
                .filter(Lesson.course_id == course.id)
                .filter(QuizAttempt.student_id == g.current_user.id)
                .distinct()
                .count()
            )
            
            # Average score for this course
            attempts = (
                db.session.query(QuizAttempt.score)
                .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
                .join(Lesson, Lesson.id == Quiz.lesson_id)
                .filter(Lesson.course_id == course.id)
                .filter(QuizAttempt.student_id == g.current_user.id)
                .all()
            )
            scores = [a.score for a in attempts]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            progress = (completed_count / total_lessons * 100) if total_lessons > 0 else 0
            
            response.append({
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "total_lessons": total_lessons,
                "completed_lessons": completed_count,
                "progress": progress,
                "average_score": avg_score
            })
            
        return jsonify(response)

    @app.route("/api/courses/<int:course_id>/lessons", methods=["POST"])
    def create_lesson(course_id: int):
        auth_error = require_auth(role="teacher")
        if auth_error:
            return auth_error

        course = db.session.get(Course, course_id)
        if not course:
            return jsonify({"message": "Course not found"}), 404
        if course.teacher_id != g.current_user.id:
            return jsonify({"message": "Forbidden"}), 403

        data = request.form if request.form else request.get_json() or {}
        title = data.get("title")

        if not title:
            return jsonify({"message": "Title is required"}), 400

        video_file = request.files.get("video_file") if request.files else None
        notes_file = request.files.get("notes_file") if request.files else None

        if not video_file or not video_file.filename:
            return jsonify({"message": "A lesson video file is required"}), 400

        filename = f"{uuid4().hex}_{secure_filename(video_file.filename)}"
        video_dir = os.path.join(app.config["UPLOAD_FOLDER"], "videos")
        os.makedirs(video_dir, exist_ok=True)
        video_abs_path = os.path.join(video_dir, filename)
        video_file.save(video_abs_path)
        video_url = f"/uploads/videos/{filename}"

        notes_url = None
        if notes_file and notes_file.filename:
            notes_filename = f"{uuid4().hex}_{secure_filename(notes_file.filename)}"
            notes_dir = os.path.join(app.config["UPLOAD_FOLDER"], "notes")
            os.makedirs(notes_dir, exist_ok=True)
            notes_abs_path = os.path.join(notes_dir, notes_filename)
            notes_file.save(notes_abs_path)
            notes_url = f"/uploads/notes/{notes_filename}"

        lesson = Lesson(
            course_id=course.id,
            title=title,
            video_url=video_url,
            notes_url=notes_url,
            video_storage_path=video_abs_path,
        )
        db.session.add(lesson)
        db.session.commit()

        # Extract audio, transcribe with Whisper API, and generate AI summary
        try:
            transcript = transcribe_video(video_abs_path)
            if not transcript or not transcript.strip():
                print(f"DEBUG: Transcription returned empty result for lesson {lesson.id}")
                lesson.transcript_text = "No speech detected in video."
                lesson.summary_text = "No summary available (no speech detected)."
            else:
                lesson.transcript_text = transcript
                summary = summarize_transcript(transcript, video_name=os.path.basename(video_abs_path))
                lesson.summary_text = summary or "Summary generation failed (empty result)."

                # Generate initial quiz questions immediately
                if summary:
                    try:
                        print(f"[app] Generating initial quiz for lesson {lesson.id}")
                        quiz = Quiz(lesson_id=lesson.id, summary_snapshot=summary)
                        db.session.add(quiz)
                        db.session.flush()
                        questions_data = generate_quiz_questions_from_text(summary)
                        for q in questions_data:
                            question = QuizQuestion(
                                quiz_id=quiz.id,
                                question_text=q["question_text"],
                                option_a=q["option_a"],
                                option_b=q["option_b"],
                                option_c=q["option_c"],
                                option_d=q["option_d"],
                                correct_option=q["correct_option"],
                            )
                            db.session.add(question)
                        print(f"[app] Initial quiz generated for lesson {lesson.id}")
                    except Exception as q_exc:
                        print(f"WARNING: Initial quiz generation failed: {q_exc}")

            db.session.commit()
        except Exception as exc:
            error_msg = str(exc)
            print(f"ERROR: Transcription/Summary failed for lesson {lesson.id}: {error_msg}")

            # Show user-friendly messages instead of raw errors
            if "no audio" in error_msg.lower() or "zero duration" in error_msg.lower() or "reshape tensor" in error_msg.lower():
                lesson.transcript_text = "No audio track detected in this video."
                lesson.summary_text = "Summary not available: the uploaded video has no audio track. Please re-upload a video with audio."
            elif "failed to extract audio" in error_msg.lower():
                lesson.transcript_text = "Could not extract audio from video."
                lesson.summary_text = "Summary not available: audio extraction failed. Ensure the video file is not corrupted."
            else:
                lesson.transcript_text = "Transcription failed."
                lesson.summary_text = "Summary not available due to a transcription error."
            db.session.commit()

        return jsonify(
            {
                "id": lesson.id,
                "title": lesson.title,
                "video_url": lesson.video_url,
                "notes_url": lesson.notes_url,
            }
        ), 201

    @app.route("/api/lessons/<int:lesson_id>", methods=["GET"])
    def get_lesson(lesson_id: int):
        lesson = db.session.get(Lesson, lesson_id)
        if not lesson:
            return jsonify({"message": "Lesson not found"}), 404

        return jsonify(
            {
                "id": lesson.id,
                "title": lesson.title,
                "video_url": lesson.video_url,
                "notes_url": lesson.notes_url,
                "transcript": lesson.transcript_text,
                "summary": lesson.summary_text,
            }
        )

    @app.route("/api/lessons/<int:lesson_id>/regenerate", methods=["POST"])
    def regenerate_transcript_and_summary(lesson_id: int):
        """Retry transcription and summary generation for a lesson."""
        auth_error = require_auth(role="teacher")
        if auth_error:
            return auth_error

        lesson = db.session.get(Lesson, lesson_id)
        if not lesson:
            return jsonify({"message": "Lesson not found"}), 404

        # Verify the teacher owns the course
        course = db.session.get(Course, lesson.course_id)
        if not course or course.teacher_id != g.current_user.id:
            return jsonify({"message": "Forbidden"}), 403

        if not lesson.video_storage_path or not os.path.exists(lesson.video_storage_path):
            return jsonify({"message": "Video file not found"}), 400

        try:
            print(f"[app] Regeneration started for lesson {lesson.id}: {lesson.title}")
            # Extract audio, transcribe with Whisper API, and generate AI summary
            transcript = transcribe_video(lesson.video_storage_path)
            if not transcript or not transcript.strip():
                lesson.transcript_text = "No speech detected in video."
                lesson.summary_text = "No summary available (no speech detected)."
                summary = lesson.summary_text
            else:
                lesson.transcript_text = transcript
                summary = summarize_transcript(transcript, video_name=os.path.basename(lesson.video_storage_path))
                lesson.summary_text = summary or "Summary generation failed (empty result)."
                
                # Generate initial quiz questions immediately
                if summary:
                    try:
                        print(f"[app] Generating initial quiz for lesson {lesson.id}")
                        quiz = Quiz(lesson_id=lesson.id, summary_snapshot=summary)
                        db.session.add(quiz)
                        db.session.flush()
                        questions_data = generate_quiz_questions_from_text(summary)
                        for q in questions_data:
                            question = QuizQuestion(
                                quiz_id=quiz.id,
                                question_text=q["question_text"],
                                option_a=q["option_a"],
                                option_b=q["option_b"],
                                option_c=q["option_c"],
                                option_d=q["option_d"],
                                correct_option=q["correct_option"],
                            )
                            db.session.add(question)
                        print(f"[app] Initial quiz generated for lesson {lesson.id}")
                    except Exception as q_exc:
                        print(f"WARNING: Initial quiz generation failed: {q_exc}")

            db.session.commit()
            return jsonify({
                "message": "Transcript and summary generated successfully",
                "transcript": transcript[:200] + "..." if len(transcript) > 200 else transcript,
                "summary": summary
            }), 200
        except Exception as exc:
            error_msg = str(exc)
            print(f"ERROR: Regeneration failed for lesson {lesson.id}: {error_msg}")
            db.session.rollback()

            # Show user-friendly messages
            if "no audio" in error_msg.lower() or "zero duration" in error_msg.lower() or "reshape tensor" in error_msg.lower():
                friendly_msg = "This video has no audio track. Please re-upload a video with audio."
            elif "failed to extract audio" in error_msg.lower():
                friendly_msg = "Could not extract audio from video. The file may be corrupted."
            else:
                friendly_msg = f"Failed to generate transcript/summary: {error_msg}"

            return jsonify({
                "message": friendly_msg,
                "error": error_msg
            }), 500

    @app.route("/api/lessons/<int:lesson_id>/regenerate-quiz", methods=["POST"])
    def regenerate_quiz(lesson_id: int):
        """Delete old quiz and generate a fresh one from existing summary."""
        auth_error = require_auth(role="teacher")
        if auth_error:
            return auth_error

        lesson = db.session.get(Lesson, lesson_id)
        if not lesson:
            return jsonify({"message": "Lesson not found"}), 404

        # Verify teacher ownership
        course = db.session.get(Course, lesson.course_id)
        if not course or course.teacher_id != g.current_user.id:
            return jsonify({"message": "Forbidden"}), 403

        if not lesson.summary_text:
            return jsonify({"message": "Cannot generate quiz without a summary. Please regenerate AI Data first."}), 400

        try:
            print(f"[app] Force regenerating quiz for lesson {lesson.id}")
            
            # 1. Delete old quiz if exists
            if lesson.quiz:
                db.session.delete(lesson.quiz)
                db.session.flush()

            # 2. Create new quiz
            new_quiz = Quiz(lesson_id=lesson.id, summary_snapshot=lesson.summary_text)
            db.session.add(new_quiz)
            db.session.flush()

            # 3. Generate questions
            questions_data = generate_quiz_questions_from_text(lesson.summary_text)
            for q in questions_data:
                question = QuizQuestion(
                    quiz_id=new_quiz.id,
                    question_text=q["question_text"],
                    option_a=q["option_a"],
                    option_b=q["option_b"],
                    option_c=q["option_c"],
                    option_d=q["option_d"],
                    correct_option=q["correct_option"],
                )
                db.session.add(question)
            
            db.session.commit()
            return jsonify({
                "message": "Quiz regenerated successfully with new questions",
                "quiz_id": new_quiz.id
            }), 200

        except Exception as exc:
            db.session.rollback()
            print(f"ERROR: Quiz regeneration failed: {exc}")
            return jsonify({"message": f"Failed to regenerate quiz: {str(exc)}"}), 500

    @app.route("/api/lessons/<int:lesson_id>", methods=["DELETE"])
    def delete_lesson(lesson_id: int):
        auth_error = require_auth(role="teacher")
        if auth_error:
            return auth_error

        lesson = db.session.get(Lesson, lesson_id)
        if not lesson:
            return jsonify({"message": "Lesson not found"}), 404

        # Verify the teacher owns the course
        course = db.session.get(Course, lesson.course_id)
        if not course or course.teacher_id != g.current_user.id:
            return jsonify({"message": "Forbidden"}), 403

        # Call the helper to delete files and cascade data
        _delete_lesson_data(lesson)
        db.session.commit()

        return jsonify({"message": "Lesson deleted successfully"}), 200

    @app.route("/api/lessons/<int:lesson_id>/watch", methods=["POST"])
    def watch_lesson(lesson_id: int):
        auth_error = require_auth(role="student")
        if auth_error:
            return auth_error

        lesson = db.session.get(Lesson, lesson_id)
        if not lesson:
            return jsonify({"message": "Lesson not found"}), 404
        enrolled = Enrollment.query.filter_by(
            student_id=g.current_user.id, course_id=lesson.course_id
        ).first()
        if not enrolled:
            return jsonify({"message": "Enroll in the course before watching"}), 403
        if not lesson.summary_text:
            transcript = lesson.transcript_text or ""
            if not transcript and lesson.video_storage_path:
                transcript = transcribe_video(lesson.video_storage_path)
                lesson.transcript_text = transcript
            lesson.summary_text = summarize_transcript(transcript, video_name=os.path.basename(lesson.video_storage_path) if lesson.video_storage_path else "unknown")
            db.session.commit()

        # Only generate a quiz if one doesn't exist for this lesson or if it's empty
        quiz = lesson.quiz
        if quiz and not quiz.questions:
            print(f"[app] Found empty quiz for lesson {lesson.id}, regenerating questions...")
            questions_data = generate_quiz_questions_from_text(lesson.summary_text)
            for q in questions_data:
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_text=q["question_text"],
                    option_a=q["option_a"],
                    option_b=q["option_b"],
                    option_c=q["option_c"],
                    option_d=q["option_d"],
                    correct_option=q["correct_option"],
                )
                db.session.add(question)
            db.session.commit()
            print(f"[app] Quiz questions regenerated successfully for lesson {lesson.id}")

        elif not quiz:
            print(f"[app] Generating new quiz for lesson {lesson.id}")
            quiz = Quiz(lesson_id=lesson.id, summary_snapshot=lesson.summary_text)
            db.session.add(quiz)
            db.session.flush()

            questions_data = generate_quiz_questions_from_text(lesson.summary_text)
            for q in questions_data:
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_text=q["question_text"],
                    option_a=q["option_a"],
                    option_b=q["option_b"],
                    option_c=q["option_c"],
                    option_d=q["option_d"],
                    correct_option=q["correct_option"],
                )
                db.session.add(question)
            db.session.commit()
            print(f"[app] Quiz generated successfully for lesson {lesson.id}")

        return jsonify({"quiz_id": quiz.id, "lesson_id": lesson.id})

    @app.route("/api/quizzes/<int:quiz_id>", methods=["GET"])
    def get_quiz(quiz_id: int):
        quiz = db.session.get(Quiz, quiz_id)
        if not quiz:
            return jsonify({"message": "Quiz not found"}), 404

        questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).all()
        return jsonify(
            {
                "quiz_id": quiz.id,
                "lesson_id": quiz.lesson_id,
                "summary": quiz.summary_snapshot,
                "questions": [
                    {
                        "id": q.id,
                        "question_text": q.question_text,
                        "option_a": q.option_a,
                        "option_b": q.option_b,
                        "option_c": q.option_c,
                        "option_d": q.option_d,
                    }
                    for q in questions
                ],
            }
        )

    @app.route("/api/quizzes/<int:quiz_id>/submit", methods=["POST"])
    def submit_quiz(quiz_id: int):
        auth_error = require_auth(role="student")
        if auth_error:
            return auth_error

        quiz = db.session.get(Quiz, quiz_id)
        if not quiz:
            return jsonify({"message": "Quiz not found"}), 404

        data = request.get_json() or {}
        answers = data.get("answers")  # list of {question_id, selected_option}
        if not isinstance(answers, list):
            return jsonify({"message": "Invalid payload"}), 400

        questions = {q.id: q for q in QuizQuestion.query.filter_by(quiz_id=quiz.id).all()}
        if not questions:
            return jsonify({"message": "No questions for this quiz"}), 400

        total = len(questions)
        correct_count = 0

        attempt = QuizAttempt(quiz_id=quiz.id, student_id=g.current_user.id, score=0)
        db.session.add(attempt)
        db.session.commit()

        for ans in answers:
            q_id = ans.get("question_id")
            selected_option = ans.get("selected_option")
            question = questions.get(q_id)
            if not question or selected_option not in ("A", "B", "C", "D"):
                continue
            is_correct = selected_option == question.correct_option
            if is_correct:
                correct_count += 1
            record = QuizAttemptAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option=selected_option,
                is_correct=is_correct,
            )
            db.session.add(record)

        score = (correct_count / total) * 100 if total > 0 else 0
        attempt.score = score
        db.session.commit()

        return jsonify(
            {
                "attempt_id": attempt.id,
                "score": score,
                "correct_count": correct_count,
                "total_questions": total,
            }
        )

    @app.route("/api/quiz-attempts/<int:attempt_id>", methods=["GET"])
    def get_quiz_attempt(attempt_id: int):
        auth_error = require_auth()
        if auth_error:
            return auth_error

        attempt = db.session.get(QuizAttempt, attempt_id)
        if not attempt:
            return jsonify({"message": "Attempt not found"}), 404
        if attempt.student_id != g.current_user.id and g.current_user.role != "teacher":
            return jsonify({"message": "Forbidden"}), 403

        answers = QuizAttemptAnswer.query.filter_by(attempt_id=attempt.id).all()

        return jsonify(
            {
                "id": attempt.id,
                "quiz_id": attempt.quiz_id,
                "student_id": attempt.student_id,
                "score": attempt.score,
                "answers": [
                    {
                        "question_id": a.question_id,
                        "selected_option": a.selected_option,
                        "is_correct": a.is_correct,
                    }
                    for a in answers
                ],
            }
        )

    @app.route("/api/student/performance", methods=["GET"])
    def student_performance():
        auth_error = require_auth(role="student")
        if auth_error:
            return auth_error

        attempts = (
            db.session.query(QuizAttempt, Quiz, Lesson, Course)
            .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
            .join(Lesson, Lesson.id == Quiz.lesson_id)
            .join(Course, Course.id == Lesson.course_id)
            .filter(QuizAttempt.student_id == g.current_user.id)
            .order_by(QuizAttempt.created_at.desc())
            .all()
        )
        return jsonify(
            [
                {
                    "attempt_id": attempt.id,
                    "quiz_id": quiz.id,
                    "lesson_title": lesson.title,
                    "course_title": course.title,
                    "score": attempt.score,
                    "taken_at": attempt.created_at.isoformat(),
                }
                for attempt, quiz, lesson, course in attempts
            ]
        )

    @app.route("/api/teacher/performance", methods=["GET"])
    def teacher_performance():
        auth_error = require_auth(role="teacher")
        if auth_error:
            return auth_error

        courses = Course.query.filter_by(teacher_id=g.current_user.id).all()
        data = []
        for course in courses:
            enrollment_count = Enrollment.query.filter_by(course_id=course.id).count()
            quiz_attempts = (
                db.session.query(QuizAttempt)
                .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
                .join(Lesson, Lesson.id == Quiz.lesson_id)
                .filter(Lesson.course_id == course.id)
                .all()
            )
            attempt_scores = [a.score for a in quiz_attempts]
            avg_score = sum(attempt_scores) / len(attempt_scores) if attempt_scores else 0
            data.append(
                {
                    "course_id": course.id,
                    "course_title": course.title,
                    "enrollment_count": enrollment_count,
                    "attempt_count": len(quiz_attempts),
                    "average_score": avg_score,
                }
            )
        return jsonify(data)

    @app.route("/uploads/<path:filename>")
    def serve_uploaded_file(filename: str):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    # --- Support AI API removed from here (moved up) ---

    return app


if __name__ == "__main__":
    # Run with: python -m backend.app  (from project root)
    application = create_app()
    application.run(
        host="0.0.0.0",
        port=5005,
        debug=True,
        use_reloader=False,
        exclude_patterns=["**/site-packages/**"],
    )
