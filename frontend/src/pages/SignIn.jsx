import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import API_BASE_URL from "../../api_config";

const SignIn = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setErrorMsg("");

    try {
      const response = await axios.post(`${API_BASE_URL}/login`, 
        JSON.stringify({ email, password }),
      {
    headers: {
      "Content-Type": "application/json",
    },
    }
    );

      console.log("login data", response.data)

      const user = response.data;

      const access_token = response.data.access_token
      // Store user/token info in localStorage or context
      localStorage.setItem("token", access_token);
      localStorage.setItem("user", JSON.stringify(user.email));

      navigate("/dashboard"); // replace with your admin route

    } catch (error) {
      console.error("Login failed:", error);
      setErrorMsg("Invalid credentials or server error.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-blackPrimary">
      <form
        onSubmit={handleLogin}
        className="bg-white dark:bg-gray-800 p-8 rounded shadow-md w-full max-w-sm"
      >
        <h2 className="text-2xl font-bold mb-6 text-center text-black dark:text-white">
          Admin Sign In
        </h2>

        {errorMsg && (
          <div className="text-red-500 text-sm mb-4 text-center">
            {errorMsg}
          </div>
        )}

        <div className="mb-4">
          <label className="block text-sm mb-1 dark:text-white">Email</label>
          <input
            type="email"
             className="w-full px-3 py-2 border border-gray-300 rounded dark:bg-gray-700 dark:text-white dark:border-gray-600"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-sm mb-1 dark:text-white">Password</label>
          <input
            type="password"
             className="w-full px-3 py-2 border border-gray-300 rounded dark:bg-gray-700 dark:text-white dark:border-gray-600"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button
          type="submit"
          className="w-full bg-black text-white py-2 rounded hover:bg-gray-900 hover:shadow-md"
        >
          Sign In
        </button>
      </form>
    </div>
  );
};

export default SignIn;
