import { createContext, useContext, useEffect, useState } from "react";
import { getCurrentUser, loginUser } from "../services/authService";

const AuthContext = createContext(null);

// Wraps the whole app (see App.jsx). Any component can read auth state
// via useAuth() below instead of prop-drilling user/token everywhere.
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true); // true while we check for an existing session

  // On first load, if a token is already in localStorage (e.g. the user
  // refreshed the page), verify it's still valid by fetching /auth/me.
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setIsLoading(false);
      return;
    }

    getCurrentUser()
      .then((data) => setUser(data))
      .catch(() => {
        // Token expired/invalid — axios interceptor already redirects,
        // but we still clear local state here defensively.
        localStorage.removeItem("access_token");
        setUser(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  async function login(email, password) {
    const { access_token } = await loginUser({ email, password });
    localStorage.setItem("access_token", access_token);
    const currentUser = await getCurrentUser();
    setUser(currentUser);
    return currentUser;
  }

  function logout() {
    localStorage.removeItem("access_token");
    setUser(null);
  }

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Convenience hook — components call useAuth() instead of
// useContext(AuthContext) directly.
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
