
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import { createApiClient, API_BASE_URL } from "../api/client";

const CourseListPage = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [enrolledCourseIds, setEnrolledCourseIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const publicApi = createApiClient(null); // Public client
        const coursesRes = await publicApi.get("/courses");
        const allCourses = coursesRes.data;

        let enrolledIds = new Set();
        if (user && user.role === "student") {
          try {
            const authApi = createApiClient(token);
            const enrolledRes = await authApi.get("/student/courses");
            enrolledIds = new Set(enrolledRes.data.map((c) => c.id));
            setEnrolledCourseIds(enrolledIds);
          } catch (enrollErr) {
            console.error("Failed to fetch enrolled courses", enrollErr);
          }
        }

        // Sort: enrolled first
        const sortedCourses = [...allCourses].sort((a, b) => {
          const aEnrolled = enrolledIds.has(a.id);
          const bEnrolled = enrolledIds.has(b.id);
          if (aEnrolled && !bEnrolled) return -1;
          if (!aEnrolled && bEnrolled) return 1;
          return 0;
        });

        setCourses(sortedCourses);
      } catch (err) {
        setError("Failed to load courses.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [user, token]);

  const handleEnroll = async (courseId) => {
    if (!user) {
      navigate("/login");
      return;
    }
    if (user.role !== "student") {
      alert("Only students can enroll.");
      return;
    }

    try {
      const api = createApiClient(token);
      await api.post(`/courses/${courseId}/enroll`);
      alert("Enrolled successfully!");
      setEnrolledCourseIds((prev) => new Set(prev).add(courseId));
    } catch (err) {
      alert(err.response?.data?.message || "Enrollment failed");
    }
  };

  const handleViewCourse = (courseId) => {
    navigate(`/student/courses/${courseId}`);
  };

  // Helper to generate a consistent gradient based on string input
  const getGradient = (str) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue1 = Math.abs(hash % 360);
    const hue2 = (hue1 + 40) % 360;
    return `linear-gradient(135deg, hsl(${hue1}, 70%, 60%), hsl(${hue2}, 80%, 60%))`;
  };

  const renderCourseCard = (course) => {
    const isEnrolled = enrolledCourseIds.has(course.id);
    const gradient = getGradient(course.title + course.id);

    return (
      <div key={course.id} className="card">
        <div className="card-cover" style={{ background: gradient }}>
          {isEnrolled && <div className="enrolled-badge-overlay">Enrolled</div>}
        </div>

        <div className="card-body">
          <h3>{course.title}</h3>

          {/* Mock Badges for visual flair */}
          <div className="card-badges">
            <span className="badge badge-yellow">★ 4.8</span>
            <span className="badge badge-blue">Beginner</span>
          </div>

          <p>{course.description}</p>


          <div className="card-actions">
            {isEnrolled ? (
              <button
                className="card-action"
                onClick={() => handleViewCourse(course.id)}
              >
                View Course
              </button>
            ) : (
              <button
                className="btn-primary"
                style={{ width: "100%" }}
                onClick={() => handleEnroll(course.id)}
              >
                Enroll Now
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (loading) return <div className="page-container">Loading courses...</div>;
  if (error) return <div className="page-container error-text">{error}</div>;



  return (
    <div className="page-container">
      {/* Featured Section - Always Horizontal */}


      {/* Main List - Grid Only */}
      <section className="section">
        <h1>Courses</h1>
        {courses.length === 0 ? (
          <p>No courses available at the moment.</p>
        ) : (
          <div className="card-grid">
            {courses.map((course) => renderCourseCard(course))}
          </div>
        )}
      </section>
    </div>
  );
};

export default CourseListPage;
