import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import { createApiClient } from "../api/client";

const QuizResultPage = () => {
  const { attemptId } = useParams();
  const { token } = useAuth();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchResult = async () => {
      try {
        const api = createApiClient(token);
        const res = await api.get(`/quiz-attempts/${attemptId}`);
        setResult(res.data);
      } catch (err) {
        setError("Failed to load quiz result");
      } finally {
        setLoading(false);
      }
    };
    fetchResult();
  }, [attemptId, token]);

  if (loading) return <div className="page-container">Loading...</div>;
  if (error) return <div className="page-container error-text">{error}</div>;
  if (!result) return <div className="page-container">Result not found.</div>;

  return (
    <div className="page-container">
      <h1>Quiz Result</h1>
      <p>
        <strong>Score:</strong> {result.score.toFixed(1)}%
      </p>
      <h2>Answers</h2>
      <ul className="answer-list">
        {result.answers.map((a, idx) => (
          <li key={idx} className={a.is_correct ? "answer-correct" : "answer-wrong"}>
            Question {a.question_id}: you chose {a.selected_option} –{" "}
            {a.is_correct ? "Correct" : "Incorrect"}
          </li>
        ))}
      </ul>
      <Link to="/student" className="primary-link">
        Back to dashboard
      </Link>
    </div>
  );
};

export default QuizResultPage;


