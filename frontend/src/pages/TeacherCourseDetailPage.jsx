
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import { API_BASE_URL, createApiClient } from "../api/client";

const getVideoEmbed = (url) => {
    if (!url) return null;
    if (url.includes("youtube.com/watch?v=")) {
        return url.replace("watch?v=", "embed/");
    }
    if (url.includes("youtu.be/")) {
        return url.replace("youtu.be/", "www.youtube.com/embed/");
    }
    return null;
};

const TeacherCourseDetailPage = () => {
    const { courseId } = useParams();
    const navigate = useNavigate();
    const { token } = useAuth();
    const api = createApiClient(token);

    const [course, setCourse] = useState(null);
    const [lessons, setLessons] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");

    // Add Lesson State
    const [lessonTitle, setLessonTitle] = useState("");
    const [lessonVideoFile, setLessonVideoFile] = useState(null);
    const [lessonNotesFile, setLessonNotesFile] = useState(null);
    const [creatingLesson, setCreatingLesson] = useState(false);

    const loadCourseData = async () => {
        try {
            setLoading(true);
            const res = await api.get(`/courses/${courseId}`);
            setCourse({
                id: res.data.id,
                title: res.data.title,
                description: res.data.description,
            });
            setLessons(res.data.lessons || []);
        } catch (err) {
            setError(err.response?.data?.message || "Failed to load course details");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadCourseData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [courseId]);

    const handleCreateLesson = async (e) => {
        e.preventDefault();
        setCreatingLesson(true);
        setMessage("");
        try {
            const formData = new FormData();
            formData.append("title", lessonTitle);
            if (lessonVideoFile) {
                formData.append("video_file", lessonVideoFile);
            }
            if (lessonNotesFile) {
                formData.append("notes_file", lessonNotesFile);
            }
            await api.post(`/courses/${courseId}/lessons`, formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            setLessonTitle("");
            setLessonVideoFile(null);
            setLessonNotesFile(null);
            setMessage("Lesson created successfully.");
            // Refresh lessons
            await loadCourseData();
        } catch (err) {
            setMessage(err.response?.data?.message || "Failed to create lesson");
        } finally {
            setCreatingLesson(false);
        }
    };

    const handleDeleteLesson = async (lessonId) => {
        if (!window.confirm("Are you sure you want to delete this lesson?")) {
            return;
        }
        try {
            await api.delete(`/lessons/${lessonId}`);
            setMessage("Lesson deleted successfully");
            await loadCourseData();
        } catch (err) {
            setMessage(err.response?.data?.message || "Failed to delete lesson");
        }
    };

    const handleRegenerateTranscript = async (lessonId) => {
        setMessage("Regenerating transcript and summary...");
        try {
            const res = await api.post(`/lessons/${lessonId}/regenerate`);
            setMessage(res.data.message || "Transcript and summary regenerated successfully");
            await loadCourseData();
        } catch (err) {
            setMessage(err.response?.data?.message || err.response?.data?.error || "Failed to regenerate");
        }
    };

    const handleRegenerateQuiz = async (lessonId) => {
        setMessage("Regenerating quiz with fresh questions...");
        try {
            const res = await api.post(`/lessons/${lessonId}/regenerate-quiz`);
            setMessage(res.data.message || "Quiz regenerated successfully");
            await loadCourseData();
        } catch (err) {
            setMessage(err.response?.data?.message || err.response?.data?.error || "Failed to regenerate quiz");
        }
    };

    if (loading) return <div className="page-container">Loading...</div>;
    if (error) return <div className="page-container error-text">{error}</div>;
    if (!course) return <div className="page-container">Course not found</div>;

    return (
        <div className="page-container">
            <button className="btn-secondary" onClick={() => navigate("/teacher")}>
                &larr; Back to Dashboard
            </button>

            <h1>Manage Course: {course.title}</h1>
            <p>{course.description}</p>

            {message && <p className="muted" style={{ margin: "1rem 0", fontWeight: "bold" }}>{message}</p>}

            <section className="section">
                <h2>Add New Lesson</h2>
                <form onSubmit={handleCreateLesson} className="form-vertical">
                    <label>
                        Lesson title
                        <input
                            type="text"
                            value={lessonTitle}
                            onChange={(e) => setLessonTitle(e.target.value)}
                            required
                        />
                    </label>
                    <label>
                        Upload video file (MP4, MOV, etc.)
                        <input
                            type="file"
                            accept="video/*"
                            onChange={(e) => setLessonVideoFile(e.target.files?.[0] || null)}
                            required
                        />
                    </label>
                    <label>
                        Upload notes (PDF / DOCX)
                        <input
                            type="file"
                            accept=".pdf,.doc,.docx,.ppt,.pptx,.txt"
                            onChange={(e) => setLessonNotesFile(e.target.files?.[0] || null)}
                        />
                    </label>
                    <button type="submit" disabled={creatingLesson}>
                        {creatingLesson ? "Creating lesson..." : "Add Lesson"}
                    </button>
                </form>
            </section>

            <section className="section">
                <h2>Existing Lessons</h2>
                {lessons.length === 0 ? (
                    <p>No lessons yet.</p>
                ) : (
                    <div className="card-grid">
                        {lessons.map((lesson) => {
                            const embedUrl = getVideoEmbed(lesson.video_url);
                            const resolvedSource = lesson.video_url && lesson.video_url.startsWith("http")
                                ? lesson.video_url
                                : `${API_BASE_URL}${lesson.video_url}`;

                            return (
                                <div key={lesson.id} className="card">
                                    <h3>{lesson.title}</h3>
                                    {lesson.video_url && (
                                        <div className="video-frame">
                                            {embedUrl ? (
                                                <iframe
                                                    src={embedUrl}
                                                    title={lesson.title}
                                                    frameBorder="0"
                                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                                    allowFullScreen
                                                />
                                            ) : (
                                                <video
                                                    className="course-video-player"
                                                    controls
                                                    controlsList="nodownload"
                                                    disablePictureInPicture
                                                    src={resolvedSource}
                                                />
                                            )}
                                            <div className="video-actions">
                                                <a href={resolvedSource} target="_blank" rel="noreferrer">
                                                    Open video URL
                                                </a>
                                            </div>
                                        </div>
                                    )}
                                    {lesson.notes_url && (
                                        <p className="muted">
                                            Notes:{" "}
                                            <a
                                                href={`${API_BASE_URL}${lesson.notes_url}`}
                                                target="_blank"
                                                rel="noreferrer"
                                            >
                                                Download notes
                                            </a>
                                        </p>
                                    )}
                                    {lesson.summary && (
                                        <div className="muted" style={{ maxHeight: "150px", overflowY: "auto", margin: "10px 0", background: "#f9f9f9", padding: "10px", borderRadius: "5px" }}>
                                            <strong>Summary:</strong> {lesson.summary}
                                        </div>
                                    )}

                                    <div className="card-actions">
                                        <button
                                            className="card-action"
                                            onClick={() => handleRegenerateTranscript(lesson.id)}
                                            type="button"
                                        >
                                            Regenerate AI Data
                                        </button>
                                        <button
                                            className="card-action btn-warning"
                                            onClick={() => handleRegenerateQuiz(lesson.id)}
                                            type="button"
                                            style={{ marginLeft: "5px" }}
                                        >
                                            Regenerate Quiz
                                        </button>
                                        <button
                                            className="btn-danger"
                                            onClick={() => handleDeleteLesson(lesson.id)}
                                            type="button"
                                        >
                                            Delete Lesson
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </section>
        </div>
    );
};

export default TeacherCourseDetailPage;
