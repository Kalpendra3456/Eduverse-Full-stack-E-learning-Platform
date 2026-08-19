
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import { createApiClient } from "../api/client";

// Reusing ScorePieChart component concept (inline or imported if shared)
// Implementation inline for simplicity here
const StatPieChart = ({ value, label, colorFn }) => {
  if (value === null || value === undefined) return <span className="muted">N/A</span>;

  const size = 80;
  const radius = 35;
  const circumference = 2 * Math.PI * radius;
  const normalizedValue = Math.max(0, Math.min(100, value));
  const offset = circumference - (normalizedValue / 100) * circumference;

  const color = colorFn ? colorFn(normalizedValue) : "#2196f3";

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}>
      <svg width={size} height={size} viewBox="0 0 80 80" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="40" cy="40" r={radius} fill="none" stroke="#eee" strokeWidth="8" />
        <circle
          cx="40" cy="40" r={radius} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
        <text
          x="40" y="40" dy="0.3em" textAnchor="middle"
          style={{
            fontSize: "16px",
            fill: "#333",
            fontWeight: "bold",
            transform: "rotate(90deg)",
            transformOrigin: "center"
          }}
        >
          {Math.round(normalizedValue)}%
        </text>
      </svg>
      <span style={{ fontSize: "0.9rem", color: "#666" }}>{label}</span>
    </div>
  );
};

const StudentDashboard = () => {
  const { token } = useAuth();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [performance, setPerformance] = useState([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const api = createApiClient(token);
        const [coursesRes, perfRes] = await Promise.all([
          api.get("/student/courses"),
          api.get("/student/performance"),
        ]);
        setCourses(coursesRes.data);
        setPerformance(perfRes.data);
      } catch (err) {
        setError("Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [token]);

  // Calculate Overall Stats
  const overallProgress = courses.length > 0
    ? courses.reduce((acc, c) => acc + (c.progress || 0), 0) / courses.length
    : 0;

  // Average score from performance history or derived from course specific avg
  // Let's use the explicit performance history for "Recent" and course data for "Overall" if available
  // Actually, calculating average of averages for simplicity
  const overallScore = courses.length > 0
    ? courses.reduce((acc, c) => acc + (c.average_score || 0), 0) / courses.length
    : 0;

  return (
    <div className="page-container">
      <h1>Student Dashboard</h1>
      {error && <p className="error-text">{error}</p>}
      {loading && <p>Loading...</p>}

      <div style={{ display: "flex", flexWrap: "wrap", gap: "2rem", marginBottom: "2rem" }}>
        <div className="card" style={{ flex: 1, minWidth: "250px", textAlign: "center" }}>
          <div className="card-body">
            <h3>Viewing Progress</h3>
            <div style={{ display: "flex", justifyContent: "center", margin: "1rem 0" }}>
              <StatPieChart
                value={overallProgress}
                label="Lesson Completion"
                colorFn={() => "#2196f3"} // Blue for progress
              />
            </div>
            <p className="muted">Percentage of lessons completed across enrolled courses.</p>
          </div>
        </div>
        <div className="card" style={{ flex: 1, minWidth: "250px", textAlign: "center" }}>
          <div className="card-body">
            <h3>Quiz Performance</h3>
            <div style={{ display: "flex", justifyContent: "center", margin: "1rem 0" }}>
              <StatPieChart
                value={overallScore}
                label="Average Score"
                colorFn={(val) => val >= 70 ? "#4caf50" : val >= 40 ? "#ff9800" : "#f44336"}
              />
            </div>
            <p className="muted">Average score across all quizzes taken.</p>
          </div>
        </div>
      </div>

      <section className="section">
        <h2>Your Courses</h2>
        {/* We can repeat stats per course if desired */}
        <div className="card-grid">
          {courses.map((c) => (
            <div key={c.id} className="card">
              {c.teacher_profile_image ? (
                <div className="card-cover" style={{ backgroundImage: `url(${createApiClient(null).defaults.baseURL}${c.teacher_profile_image})` }}></div>
              ) : (
                <div className="card-cover" style={{ background: "linear-gradient(135deg, #1e293b, #0f172a)" }}></div>
              )}

              <div className="card-body">
                <h3>{c.title}</h3>
                <p>{c.description}</p>
                <div style={{ display: "flex", gap: "1rem", margin: "1rem 0", fontSize: "0.85rem" }}>
                  <div style={{ flex: 1 }}>
                    <strong style={{ display: "block", marginBottom: "4px" }}>Progress</strong>
                    <div style={{ background: "rgba(255,255,255,0.1)", height: "6px", width: "100%", borderRadius: "3px" }}>
                      <div style={{ background: "#38bdf8", height: "100%", width: `${c.progress || 0}%`, borderRadius: "3px" }} />
                    </div>
                  </div>
                  <div>
                    <strong style={{ display: "block", marginBottom: "4px" }}>Score</strong>
                    <div style={{ color: "#4ade80", fontWeight: "bold" }}>{Math.round(c.average_score || 0)}%</div>
                  </div>
                </div>
                <div className="card-actions">
                  <Link to={`/student/courses/${c.id}`} className="card-action" style={{ textAlign: "center", textDecoration: "none" }}>
                    Continue Learning
                  </Link>
                </div>
              </div>
            </div>
          ))}
          {!loading && courses.length === 0 && (
            <p>You have not enrolled in any courses yet.</p>
          )}
        </div>
      </section>

      <section className="section">
        <h2>Recent Quiz Attempts</h2>
        {performance.length === 0 ? (
          <p>No attempts yet.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Course</th>
                <th>Lesson</th>
                <th>Date</th>
                <th>Score</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {performance.map((p) => (
                <tr key={p.attempt_id}>
                  <td>{p.course_title}</td>
                  <td>{p.lesson_title}</td>
                  <td>{new Date(p.taken_at).toLocaleDateString()}</td>
                  <td>{p.score.toFixed(1)}%</td>
                  <td>
                    <Link to={`/student/quiz-results/${p.attempt_id}`}>
                      View Results
                    </Link>
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

export default StudentDashboard;
