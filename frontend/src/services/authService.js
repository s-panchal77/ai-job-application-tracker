import api from "../api/axios";

// Matches backend: POST /auth/register — expects JSON body
export async function registerUser({ email, password, full_name }) {
  const response = await api.post("/auth/register", {
    email,
    password,
    full_name,
  });
  return response.data;
}

// Matches backend: POST /auth/login — expects FORM data, not JSON.
// FastAPI's OAuth2PasswordRequestForm requires application/x-www-form-urlencoded
// with fields named 'username' and 'password' (see backend Phase 5).
export async function loginUser({ email, password }) {
  const formData = new URLSearchParams();
  formData.append("username", email); // backend treats "username" as the email
  formData.append("password", password);

  const response = await api.post("/auth/login", formData, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return response.data; // { access_token, token_type }
}

// Matches backend: GET /auth/me — protected, returns the logged-in user
export async function getCurrentUser() {
  const response = await api.get("/auth/me");
  return response.data;
}
