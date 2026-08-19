import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../state/AuthContext";

const TopBar = () => {
  const { user, logout } = useAuth();

  const [menuOpen, setMenuOpen] = React.useState(false);

  return (
    <header className="topbar">
      <div className="topbar-left">
        <Link to="/" className="logo">
          Eduverse
        </Link>
      </div>
      
      <button 
        className="mobile-menu-toggle" 
        onClick={() => setMenuOpen(!menuOpen)}
        aria-label="Toggle menu"
      >
        <span className={`hamburger ${menuOpen ? 'open' : ''}`}></span>
      </button>

      <div className={`topbar-right ${menuOpen ? 'mobile-open' : ''}`}>
        {user && (
          <>
            <span className="user-label">
              {user.name} ({user.role})
            </span>
            {user.role === "student" && (
              <>
                <Link to="/student" className="topbar-link" onClick={() => setMenuOpen(false)}>
                  Dashboard
                </Link>
                <Link to="/student/courses" className="topbar-link" onClick={() => setMenuOpen(false)}>
                  Courses
                </Link>
                <Link to="/support" className="topbar-link" onClick={() => setMenuOpen(false)}>
                  Support
                </Link>
              </>
            )}
            {user.role === "teacher" && (
              <>
                <Link to="/teacher" className="topbar-link" onClick={() => setMenuOpen(false)}>
                  Teacher Dashboard
                </Link>
                <Link to="/support" className="topbar-link" onClick={() => setMenuOpen(false)}>
                  Support
                </Link>
              </>
            )}
            <button className="topbar-button" onClick={() => { logout(); setMenuOpen(false); }}>
              Logout
            </button>
          </>
        )}
        {!user && (
          <>
            <Link to="/login" className="topbar-link" onClick={() => setMenuOpen(false)}>
              Login
            </Link>
            <Link to="/register" className="topbar-link" onClick={() => setMenuOpen(false)}>
              Register
            </Link>
          </>
        )}
      </div>
    </header>
  );

};

export default TopBar;


