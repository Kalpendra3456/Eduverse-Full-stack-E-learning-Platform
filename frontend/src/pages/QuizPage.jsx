import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import { createApiClient } from "../api/client";

const QuizPage = () => {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showSummary, setShowSummary] = useState(false);

  const answeredCount = Object.keys(answers).length;
  const totalCount = quiz?.questions?.length || 0;
  const progressPercent = totalCount > 0 ? (answeredCount / totalCount) * 100 : 0;

  useEffect(() => {
    const fetchQuiz = async () => {
      try {
        const api = createApiClient(token);
        const res = await api.get(`/quizzes/${quizId}`);
        setQuiz(res.data);
      } catch (err) {
        setError(err.response?.data?.message || "Failed to load quiz");
      } finally {
        setLoading(false);
      }
    };
    fetchQuiz();
  }, [quizId, token]);

  const handleChange = (questionId, option) => {
    setAnswers((prev) => ({ ...prev, [questionId]: option }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const api = createApiClient(token);
      const payload = {
        answers: Object.entries(answers).map(([questionId, selected_option]) => ({
          question_id: Number(questionId),
          selected_option,
        })),
      };
      const res = await api.post(`/quizzes/${quizId}/submit`, payload);
      navigate(`/student/quiz-results/${res.data.attempt_id}`);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to submit quiz");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="page-container">Loading...</div>;
  if (error) return <div className="page-container error-text">{error}</div>;
  if (!quiz) return <div className="page-container">Quiz not available.</div>;

  return (
    <div className="page-container">
      <div className="quiz-header">
        <h1>{quiz.lesson_title || "Lesson Quiz"}</h1>
        <div className="quiz-progress-container">
          <div className="quiz-progress-bar" style={{ width: `${progressPercent}%` }}></div>
          <span className="quiz-progress-text">{answeredCount} of {totalCount} answered</span>
        </div>
      </div>

      {quiz.summary && (
        <div className="quiz-summary-ref">
          <button 
            type="button" 
            className="summary-toggle-btn"
            onClick={() => setShowSummary(!showSummary)}
          >
            {showSummary ? "Hide Reference Summary" : "Show Reference Summary"}
          </button>
          {showSummary && (
            <div className="summary-content-box">
              <p>{quiz.summary}</p>
            </div>
          )}
        </div>
      )}
      <form onSubmit={handleSubmit} className="quiz-form">
        {quiz.questions.map((q, idx) => (
          <div key={q.id} className="quiz-question">
            <h3>
              Q{idx + 1}. {q.question_text}
            </h3>
            <div className="quiz-options">
              {["A", "B", "C", "D"].map((opt) => (
                <label key={opt} className="quiz-option">
                  <input
                    type="radio"
                    name={`q-${q.id}`}
                    value={opt}
                    checked={answers[q.id] === opt}
                    onChange={() => handleChange(q.id, opt)}
                  />
                  <span>
                    {opt === "A" && q.option_a}
                    {opt === "B" && q.option_b}
                    {opt === "C" && q.option_c}
                    {opt === "D" && q.option_d}
                  </span>
                </label>
              ))}
            </div>
          </div>
        ))}
        <button type="submit" disabled={submitting}>
          {submitting ? "Submitting..." : "Submit quiz"}
        </button>
      </form>
    </div>
  );
};

export default QuizPage;


