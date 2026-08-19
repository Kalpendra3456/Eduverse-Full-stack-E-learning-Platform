import React, { useState } from "react";
import { Link } from "react-router-dom";
import { createApiClient } from "../api/client";

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [debugToken, setDebugToken] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);
    try {
      const api = createApiClient();
      const res = await api.post("/auth/forgot-password", { email });
      setMessage(res.data.message);
      if (res.data.debug_token) {
          setDebugToken(res.data.debug_token);
      }
    } catch (err) {
      setError(err.response?.data?.message || "Failed to send reset email");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <h1>Forgot Password</h1>
      <p style={{ marginBottom: "1.5rem", color: "#666" }}>
        Enter your email address and we'll send you a link to reset your password.
      </p>
      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="Enter your email"
          />
        </div>
        {error && <div className="error-text">{error}</div>}
        {message && <div className="success-text" style={{ color: "green", marginBottom: "1rem" }}>{message}</div>}
        
        {debugToken && (
            <div style={{ padding: "1rem", backgroundColor: "#f0f0f0", borderRadius: "8px", marginBottom: "1rem" }}>
                <p style={{ fontSize: "0.8rem", margin: 0 }}><strong>Debug Token (Simulation):</strong></p>
                <Link to={`/reset-password?token=${debugToken}`} style={{ wordBreak: "break-all", fontSize: "0.8rem" }}>
                    Click here to reset (Reset Link)
                </Link>
            </div>
        )}

        <button type="submit" disabled={loading} style={{ marginTop: "1rem" }}>
          {loading ? "Sending..." : "Send Reset Link"}
        </button>
      </form>
      <p>
        Back to <Link to="/login">Login</Link>
      </p>
    </div>
  );
};

export default ForgotPassword;
