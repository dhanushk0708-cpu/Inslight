import { apiRequest } from "./api-client";
import { User, AuthResponse } from "../types";

export const AuthService = {
  getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("inslight_token");
  },

  setSession(token: string, user: User) {
    if (typeof window === "undefined") return;
    localStorage.setItem("inslight_token", token);
    localStorage.setItem("inslight_user", JSON.stringify(user));
  },

  clearSession() {
    if (typeof window === "undefined") return;
    localStorage.removeItem("inslight_token");
    localStorage.removeItem("inslight_user");
  },

  getUser(): User | null {
    if (typeof window === "undefined") return null;
    const userStr = localStorage.getItem("inslight_user");
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  },

  isAuthenticated(): boolean {
    return !!this.getToken();
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const data = await apiRequest<AuthResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
    this.setSession(data.access_token, data.user);
    return data;
  },

  async register(name: string, email: string, password: string): Promise<AuthResponse> {
    const data = await apiRequest<AuthResponse>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password })
    });
    this.setSession(data.access_token, data.user);
    return data;
  },

  async fetchCurrentUser(): Promise<User | null> {
    const token = this.getToken();
    if (!token) return null;
    try {
      const user = await apiRequest<User>("/api/v1/auth/me");
      if (typeof window !== "undefined") {
        localStorage.setItem("inslight_user", JSON.stringify(user));
      }
      return user;
    } catch {
      this.clearSession();
      return null;
    }
  },

  logout() {
    this.clearSession();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }
};
