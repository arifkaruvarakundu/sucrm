// const API_BASE_URL = "http://localhost:8000";
// const API_BASE_URL = "http://161.35.208.91";
// const API_BASE_URL = "https://app.souqalsultan.com";

// export default API_BASE_URL;

import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // ensures guest_id cookie is sent automatically
});

// Attach JWT token automatically if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token"); // adjust if you store it in Redux instead
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
