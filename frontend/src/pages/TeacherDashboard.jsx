
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import { createApiClient } from "../api/client";

const ScorePieChart = ({ score, size = 60 }) => {
  if (score === null || score === undefined) return <span className="muted">N/A</span>;

  const radius = 16;
  const circumference = 2 * Math.PI * radius;
  const normalizedScore = Math.max(0, Math.min(100, score));
  const offset = circumference - (normalizedScore / 100) * circumference;

  // Color based on score
  const color = normalizedScore >= 70 ? "#4caf50" : normalizedScore >= 40 ? "#ff9800" : "#f44336";

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}>
      <svg width={size} height={size} viewBox="0 0 40 40" style={{ transform: "rotate(-90deg)" }}>
        {/* Background Circle */}
        <circle cx="20" cy="20" r={radius} fill="none" stroke="#eee" strokeWidth="4" />
        {/* Progress Circle */}
        <circle
          cx="20" cy="20" r={radius} fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
        {/* Text centered (rotated back) */}
        <text
          x="20" y="20" dy="0.3em" textAnchor="middle"
          style={{
            fontSize: "10px",
            fill: "#333",
            fontWeight: "bold",
            transform: "rotate(90deg)",
            transformOrigin: "center"
          }}
        >
          {Math.round(normalizedScore)}%
        </text>
      </svg>
    </div>
  );
};

const TeacherDashboard = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [newCourseTitle, setNewCourseTitle] = useState("");
  const [newCourseDescription, setNewCourseDescription] = useState("");
  const [creatingCourse, setCreatingCourse] = useState(false);
  const [message, setMessage] = useState("");
  const [performance, setPerformance] = useState([]);

  const api = createApiClient(token);

  const loadData = async () => {
    try {
      const [coursesRes, perfRes] = await Promise.all([
        api.get("/teacher/courses"),
        api.get("/teacher/performance"),
      ]);
      setCourses(coursesRes.data);
      setPerformance(perfRes.data);
    } catch (err) {
      setError("Failed to load your courses");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCreateCourse = async (e) => {
    e.preventDefault();
    setCreatingCourse(true);
    setMessage("");
    try {
      await api.post("/teacher/courses", {
        title: newCourseTitle,
        description: newCourseDescription,
      });
      setNewCourseTitle("");
      setNewCourseDescription("");
      setMessage("Course created.");
      await loadData();
    } catch (err) {
      setMessage(err.response?.data?.message || "Failed to create course");
    } finally {
      setCreatingCourse(false);
    }
  };

  const handleDeleteCourse = async (courseId) => {
    if (!window.confirm("Are you sure you want to delete this course? This will strictly delete ALL lessons, quizzes, and student data associated with it.")) {
      return;
    }
    try {
      await api.delete(`/courses/${courseId}`);
      setMessage("Course deleted successfully.");
      await loadData();
    } catch (err) {
      setMessage(err.response?.data?.message || "Failed to delete course");
    }
  };

  return (
    <div className="page-container">
      <h1>Teacher Dashboard</h1>
      {error && <p className="error-text">{error}</p>}
      {message && <p className="muted">{message}</p>}

      <section className="section">
        <h2>Create a New Course</h2>
        <form onSubmit={handleCreateCourse} className="form-inline">
          <input
            type="text"
            placeholder="Course title"
            value={newCourseTitle}
            onChange={(e) => setNewCourseTitle(e.target.value)}
            required
          />
          <input
            type="text"
            placeholder="Short description"
            value={newCourseDescription}
            onChange={(e) => setNewCourseDescription(e.target.value)}
          />
          <button type="submit" disabled={creatingCourse}>
            {creatingCourse ? "Creating..." : "Create course"}
          </button>
        </form>
      </section>

      <section className="section">
        <h2>Your Courses</h2>
        {loading && <p>Loading...</p>}
        <div className="card-grid">
          {courses.map((c) => (
            <div key={c.id} className="card">
              {/* Note: Teacher Dashboard might not want the Teacher's own face on every card as the cover? 
                   But for consistency, let's allow it, or just use a default gradient since they know who they are.
                   User said "on the couese card", implying public view. But let's check Teacher Dashboard consistency.
                   If I use their profile image, it will look like the public view. */}
              {/* Actually, let's keep it simple for generic course covers if no specific course image exists. 
                  But since we are using teacher profile image as "Cover" generally... */}
              <div className="card-cover" style={{ background: "linear-gradient(135deg, #475569, #334155)" }}></div>
              {/* Leaving TeacherDashboard with gradient for now as they didn't explicitly ask to see their own face 10 times. */}

              <div className="card-body">
                <h3>{c.title}</h3>
                <p>{c.description}</p>
                <div className="card-badges">
                  <span className="badge badge-blue">{c.enrollment_count ?? 0} Students</span>
                </div>
                <div className="card-actions">
                  <button
                    className="card-action"
                    type="button"
                    onClick={() => navigate(`/teacher/courses/${c.id}`)}
                  >
                    Manage
                  </button>
                  <button
                    className="btn-danger"
                    style={{ borderRadius: "0.6rem", padding: "0.6rem 1rem", border: "none", cursor: "pointer", fontSize: "0.9rem", fontWeight: "500" }}
                    type="button"
                    onClick={() => handleDeleteCourse(c.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
          {!loading && courses.length === 0 && (
            <p>You have not created any courses yet.</p>
          )}
        </div>
      </section>

      <section className="section">
        <h2>Quiz Performance Overview</h2>
        {performance.length === 0 ? (
          <p>No quiz attempts yet.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Course</th>
                <th>Enrollments</th>
                <th>Quiz Attempts</th>
                <th>Average Score</th>
              </tr>
            </thead>
            <tbody>
              {performance.map((p) => (
                <tr key={p.course_id}>
                  <td>{p.course_title}</td>
                  <td>{p.enrollment_count}</td>
                  <td>{p.attempt_count}</td>
                  <td>
                    <div style={{ display: "flex", justifyContent: "center" }}>
                      <ScorePieChart score={p.average_score} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
};

export default TeacherDashboard;
