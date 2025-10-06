import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { register } from "../redux/actions/AuthActions"

const Register = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { loading, error, isAuthenticated } = useSelector((state) => state.auth);

  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [focusedField, setFocusedField] = useState(null);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (form.password !== form.confirmPassword) {
      alert("Passwords do not match");
      return;
    }

    dispatch(
      register(
        form.firstName,
        form.lastName,
        form.email,
        form.password,
        form.confirmPassword
      )
    );
  };

  useEffect(() => {
    if (isAuthenticated) {
      setShowSuccess(true);
      setTimeout(() => {
        navigate("/");
      }, 1500);
    }
  }, [isAuthenticated, navigate]);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background:
          "linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)",
        padding: "20px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Animated background elements */}
      <div
        style={{
          position: "absolute",
          top: "-50%",
          right: "-10%",
          width: "600px",
          height: "600px",
          background:
            "radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)",
          borderRadius: "50%",
          animation: "float 20s ease-in-out infinite",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: "-30%",
          left: "-10%",
          width: "500px",
          height: "500px",
          background:
            "radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%)",
          borderRadius: "50%",
          animation: "float 15s ease-in-out infinite reverse",
        }}
      />

      <style>
        {`
          @keyframes float {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            33% { transform: translate(30px, -30px) rotate(120deg); }
            66% { transform: translate(-20px, 20px) rotate(240deg); }
          }
          @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
          }
          @keyframes checkmark {
            0% { transform: scale(0) rotate(45deg); }
            50% { transform: scale(1.2) rotate(45deg); }
            100% { transform: scale(1) rotate(45deg); }
          }
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}
      </style>

      <form
        onSubmit={handleSubmit}
        style={{
          background: "rgba(255, 255, 255, 0.95)",
          backdropFilter: "blur(20px)",
          padding: "48px 40px",
          borderRadius: "24px",
          boxShadow:
            "0 20px 60px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.2)",
          width: "100%",
          maxWidth: "480px",
          position: "relative",
          zIndex: 1,
          animation: "slideUp 0.6s ease-out",
        }}
      >
        {showSuccess ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              minHeight: "300px",
            }}
          >
            <div
              style={{
                width: "80px",
                height: "80px",
                borderRadius: "50%",
                background:
                  "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: "24px",
                animation: "slideUp 0.5s ease-out",
              }}
            >
              <div
                style={{
                  width: "30px",
                  height: "50px",
                  borderRight: "4px solid white",
                  borderBottom: "4px solid white",
                  transform: "rotate(45deg)",
                  marginBottom: "10px",
                  animation: "checkmark 0.5s ease-out 0.2s both",
                }}
              />
            </div>
            <h2
              style={{
                fontSize: "28px",
                fontWeight: "700",
                background:
                  "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
                marginBottom: "12px",
              }}
            >
              Registration Successful!
            </h2>
            <p style={{ color: "#64748b", fontSize: "16px" }}>
              Redirecting to dashboard...
            </p>
          </div>
        ) : (
          <>
            <h2
              style={{
                fontSize: "32px",
                fontWeight: "700",
                marginBottom: "12px",
                textAlign: "center",
                background:
                  "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
                letterSpacing: "-0.5px",
              }}
            >
              Create Account
            </h2>
            <p
              style={{
                textAlign: "center",
                color: "#64748b",
                marginBottom: "32px",
                fontSize: "15px",
              }}
            >
              Join us today and get started
            </p>

            {error && (
              <div
                style={{
                  padding: "12px 16px",
                  backgroundColor: "#fee2e2",
                  border: "1px solid #fecaca",
                  borderRadius: "12px",
                  marginBottom: "24px",
                  animation: "slideUp 0.3s ease-out",
                }}
              >
                <p
                  style={{
                    color: "#dc2626",
                    fontSize: "14px",
                    margin: 0,
                    textAlign: "center",
                    fontWeight: "500",
                  }}
                >
                  {error}
                </p>
              </div>
            )}

            <div style={{ display: "flex", gap: "16px", marginBottom: "20px" }}>
              <div style={{ flex: 1 }}>
                <label
                  style={{
                    display: "block",
                    fontSize: "14px",
                    fontWeight: "600",
                    marginBottom: "8px",
                    color: "#334155",
                  }}
                >
                  First Name
                </label>
                <input
                  type="text"
                  name="firstName"
                  value={form.firstName}
                  onChange={handleChange}
                  onFocus={() => setFocusedField("firstName")}
                  onBlur={() => setFocusedField(null)}
                  style={{
                    width: "100%",
                    padding: "14px 16px",
                    border: "2px solid",
                    borderColor:
                      focusedField === "firstName" ? "#667eea" : "#e2e8f0",
                    borderRadius: "12px",
                    fontSize: "15px",
                    outline: "none",
                    transition: "all 0.3s ease",
                    backgroundColor: "#ffffff",
                    boxShadow:
                      focusedField === "firstName"
                        ? "0 0 0 4px rgba(102, 126, 234, 0.1)"
                        : "none",
                  }}
                  required
                />
              </div>

              <div style={{ flex: 1 }}>
                <label
                  style={{
                    display: "block",
                    fontSize: "14px",
                    fontWeight: "600",
                    marginBottom: "8px",
                    color: "#334155",
                  }}
                >
                  Last Name
                </label>
                <input
                  type="text"
                  name="lastName"
                  value={form.lastName}
                  onChange={handleChange}
                  onFocus={() => setFocusedField("lastName")}
                  onBlur={() => setFocusedField(null)}
                  style={{
                    width: "100%",
                    padding: "14px 16px",
                    border: "2px solid",
                    borderColor:
                      focusedField === "lastName" ? "#667eea" : "#e2e8f0",
                    borderRadius: "12px",
                    fontSize: "15px",
                    outline: "none",
                    transition: "all 0.3s ease",
                    backgroundColor: "#ffffff",
                    boxShadow:
                      focusedField === "lastName"
                        ? "0 0 0 4px rgba(102, 126, 234, 0.1)"
                        : "none",
                  }}
                  required
                />
              </div>
            </div>

            <div style={{ marginBottom: "20px" }}>
              <label
                style={{
                  display: "block",
                  fontSize: "14px",
                  fontWeight: "600",
                  marginBottom: "8px",
                  color: "#334155",
                }}
              >
                Email
              </label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                onFocus={() => setFocusedField("email")}
                onBlur={() => setFocusedField(null)}
                style={{
                  width: "100%",
                  padding: "14px 16px",
                  border: "2px solid",
                  borderColor:
                    focusedField === "email" ? "#667eea" : "#e2e8f0",
                  borderRadius: "12px",
                  fontSize: "15px",
                  outline: "none",
                  transition: "all 0.3s ease",
                  backgroundColor: "#ffffff",
                  boxShadow:
                    focusedField === "email"
                      ? "0 0 0 4px rgba(102, 126, 234, 0.1)"
                      : "none",
                }}
                required
              />
            </div>

            <div style={{ marginBottom: "20px" }}>
              <label
                style={{
                  display: "block",
                  fontSize: "14px",
                  fontWeight: "600",
                  marginBottom: "8px",
                  color: "#334155",
                }}
              >
                Password
              </label>
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                onFocus={() => setFocusedField("password")}
                onBlur={() => setFocusedField(null)}
                style={{
                  width: "100%",
                  padding: "14px 16px",
                  border: "2px solid",
                  borderColor:
                    focusedField === "password" ? "#667eea" : "#e2e8f0",
                  borderRadius: "12px",
                  fontSize: "15px",
                  outline: "none",
                  transition: "all 0.3s ease",
                  backgroundColor: "#ffffff",
                  boxShadow:
                    focusedField === "password"
                      ? "0 0 0 4px rgba(102, 126, 234, 0.1)"
                      : "none",
                }}
                required
              />
            </div>

            <div style={{ marginBottom: "28px" }}>
              <label
                style={{
                  display: "block",
                  fontSize: "14px",
                  fontWeight: "600",
                  marginBottom: "8px",
                  color: "#334155",
                }}
              >
                Confirm Password
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={form.confirmPassword}
                onChange={handleChange}
                onFocus={() => setFocusedField("confirmPassword")}
                onBlur={() => setFocusedField(null)}
                style={{
                  width: "100%",
                  padding: "14px 16px",
                  border: "2px solid",
                  borderColor:
                    focusedField === "confirmPassword"
                      ? "#667eea"
                      : "#e2e8f0",
                  borderRadius: "12px",
                  fontSize: "15px",
                  outline: "none",
                  transition: "all 0.3s ease",
                  backgroundColor: "#ffffff",
                  boxShadow:
                    focusedField === "confirmPassword"
                      ? "0 0 0 4px rgba(102, 126, 234, 0.1)"
                      : "none",
                }}
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%",
                padding: "16px",
                background: loading
                  ? "#94a3b8"
                  : "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                color: "white",
                border: "none",
                borderRadius: "12px",
                fontSize: "16px",
                fontWeight: "600",
                cursor: loading ? "not-allowed" : "pointer",
                transition: "all 0.3s ease",
                boxShadow: loading
                  ? "none"
                  : "0 4px 15px rgba(102, 126, 234, 0.4)",
                transform: loading ? "none" : "translateY(0)",
              }}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.currentTarget.style.transform = "translateY(-2px)";
                  e.currentTarget.style.boxShadow =
                    "0 6px 20px rgba(102, 126, 234, 0.5)";
                }
              }}
              onMouseLeave={(e) => {
                if (!loading) {
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow =
                    "0 4px 15px rgba(102, 126, 234, 0.4)";
                }
              }}
            >
              {loading ? (
                <span
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "8px",
                  }}
                >
                  <span
                    style={{
                      width: "16px",
                      height: "16px",
                      border: "2px solid rgba(255,255,255,0.3)",
                      borderTop: "2px solid white",
                      borderRadius: "50%",
                      animation: "spin 0.8s linear infinite",
                    }}
                  />
                  Creating Account...
                </span>
              ) : (
                "Create Account"
              )}
            </button>

            <p
              style={{
                textAlign: "center",
                marginTop: "24px",
                fontSize: "14px",
                color: "#64748b",
              }}
            >
              Already have an account?{" "}
              <a
                href="/signin"
                style={{
                  color: "#667eea",
                  textDecoration: "none",
                  fontWeight: "600",
                  transition: "color 0.2s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = "#764ba2";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = "#667eea";
                }}
              >
                Sign in
              </a>
            </p>
          </>
        )}
      </form>
    </div>
  );
};

export default Register;
