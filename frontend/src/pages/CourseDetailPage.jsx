import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import { API_BASE_URL, createApiClient } from "../api/client";

const resolveVideoUrl = (url) => {
  if (!url) return "";
  return url.startsWith("http") ? url : `${API_BASE_URL}${url}`;
};

const CourseDetailPage = () => {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [enrolling, setEnrolling] = useState(false);
  const [enrollMessage, setEnrollMessage] = useState("");
  const [lessonMessage, setLessonMessage] = useState("");
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

  const [generatingQuizFor, setGeneratingQuizFor] = useState(null);

  useEffect(() => {
    const fetchCourse = async () => {
      try {
        const api = createApiClient(token);
        const res = await api.get(`/courses/${courseId}`);
        setCourse(res.data);
      } catch (err) {
        setError("Failed to load course");
      } finally {
        setLoading(false);
      }
    };
    fetchCourse();
  }, [courseId, token]);

  const handleEnroll = async () => {
    setEnrolling(true);
    setEnrollMessage("");
    try {
      const api = createApiClient(token);
      const res = await api.post(`/courses/${courseId}/enroll`);
      setEnrollMessage(res.data.message || "Enrolled successfully");
    } catch (err) {
      setEnrollMessage(err.response?.data?.message || "Enrollment failed");
    } finally {
      setEnrolling(false);
    }
  };

  const handleWatchAndQuiz = async (lessonId) => {
    setGeneratingQuizFor(lessonId);
    setLessonMessage("");
    try {
      const api = createApiClient(token);
      const res = await api.post(`/lessons/${lessonId}/watch`);
      setLessonMessage("Quiz generated. Redirecting...");
      navigate(`/student/quizzes/${res.data.quiz_id}`);
    } catch (err) {
      setLessonMessage(err.response?.data?.message || "Could not generate quiz");
    } finally {
      setGeneratingQuizFor(null);
    }
  };

  if (loading) return <div className="page-container">Loading...</div>;
  if (error) return <div className="page-container error-text">{error}</div>;
  if (!course) return <div className="page-container">Course not found.</div>;

  return (
    <div className="page-container">
      <h1>{course.title}</h1>
      <p>{course.description}</p>
      <div className="toolbar">
        <button onClick={handleEnroll} disabled={enrolling}>
          {enrolling ? "Enrolling..." : "Enroll in this course"}
        </button>
        {enrollMessage && <span className="muted">{enrollMessage}</span>}
      </div>

      <h2>Lessons</h2>
      {lessonMessage && <p className="muted">{lessonMessage}</p>}
      {course.lessons && course.lessons.length > 0 ? (
        <div className="card-grid">
          {course.lessons.map((l) => {
            const embedUrl = getVideoEmbed(l.video_url);
            const resolvedSource = resolveVideoUrl(l.video_url);
            return (
              <div key={l.id} className="card">
                <h3>{l.title}</h3>
                {l.video_url && (
                  <div className="video-frame">
                    {embedUrl ? (
                      <iframe
                        src={embedUrl}
                        title={l.title}
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
              {l.notes_url && (
                <p className="muted">
                  Notes:{" "}
                  <a href={`${API_BASE_URL}${l.notes_url}`} target="_blank" rel="noreferrer">
                    Download notes
                  </a>
                </p>
              )}
              {l.summary && (
                <p className="muted">
                  <strong>Summary:</strong> {l.summary}
                </p>
              )}
              <button
                className="card-action"
                onClick={() => handleWatchAndQuiz(l.id)}
                disabled={generatingQuizFor === l.id}
              >
                {generatingQuizFor === l.id ? "Generating quiz..." : "Watch & generate quiz"}
              </button>
            </div>
            );
          })}
        </div>
      ) : (
        <p>No lessons yet for this course.</p>
      )}
    </div>
  );
};

export default CourseDetailPage;


