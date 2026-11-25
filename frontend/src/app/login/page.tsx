"use client";
import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthService } from "../../services/auth-service";
import { BrandLogo } from "../../components/ui/BrandLogo";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please fill in both email and password.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await AuthService.login(email, password);
      router.push("/");
    } catch (err: any) {
      setError(err?.message || "Failed to log in. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-box">
        <div style={{ marginBottom: 18 }}>
          <BrandLogo size={38} />
        </div>

        <h1 className="auth-title">Welcome Back</h1>
        <p className="auth-sub">Sign in to your AI Business Intelligence dashboard</p>

        {error && <div className="error-banner">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="login-email">Email Address</label>
            <input
              id="login-email"
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="analyst@company.com"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Signing in..." : "Sign In to Dashboard →"}
          </button>
        </form>

        <div className="auth-footer">
          Don't have an account?
          <Link href="/register" className="auth-link">Create Account</Link>
        </div>
      </div>
    </div>
  );
}
