import React, { useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { createApiClient } from "../api/client";

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");
  
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
        setError("Passwords do not match");
        return;
    }
    
    setError("");
    setMessage("");
    setLoading(true);
    try {
      const api = createApiClient();
      await api.post("/auth/reset-password", { token, new_password: newPassword });
      setMessage("Password reset successfully! Redirecting to login...");
      setTimeout(() => {
          navigate("/login");
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to reset password");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
      return (
          <div className="auth-container">
              <h1>Invalid Request</h1>
              <p>No reset token provided. Please use the link sent to your email.</p>
              <Link to="/login">Back to Login</Link>
          </div>
      );
  }

  return (
    <div className="auth-container">
      <h1>Reset Password</h1>
      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label>New Password</label>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            placeholder="Enter new password"
          />
        </div>
        <div className="form-group">
          <label>Confirm New Password</label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            placeholder="Confirm new password"
          />
        </div>
        {error && <div className="error-text">{error}</div>}
        {message && <div className="success-text" style={{ color: "green", marginBottom: "1rem" }}>{message}</div>}
        
        <button type="submit" disabled={loading} style={{ marginTop: "1rem" }}>
          {loading ? "Resetting..." : "Reset Password"}
        </button>
      </form>
    </div>
  );
};

export default ResetPassword;
