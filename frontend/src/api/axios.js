import axios from "axios";

// Base URL for the FastAPI backend. Override via a .env file
// (VITE_API_BASE_URL=...) when deploying somewhere other than localhost.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
});

// ── Request interceptor ──────────────────────────────────────
// Runs before every single request made through this instance.
// Reads the JWT from localStorage and attaches it as a Bearer token,
// so individual service files never have to think about auth headers.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor ─────────────────────────────────────
// Runs after every response. Centralizes what happens on auth failure
// so every page doesn't need to duplicate this logic.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token missing, invalid, or expired — the backend's
      // get_current_user dependency rejected the request.
      // Clear stale credentials and send the user back to login.
      localStorage.removeItem("access_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
