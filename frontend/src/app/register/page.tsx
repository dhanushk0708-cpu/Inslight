"use client";
import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthService } from "../../services/auth-service";
import { BrandLogo } from "../../components/ui/BrandLogo";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !password) {
      setError("Please fill in all required fields.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await AuthService.register(name, email, password);
      router.push("/");
    } catch (err: any) {
      setError(err?.message || "Failed to register. Email may already be in use.");
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

        <h1 className="auth-title">Create Account</h1>
        <p className="auth-sub">Set up your isolated AI Business Intelligence workspace</p>

        {error && <div className="error-banner">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="register-name">Full Name</label>
            <input
              id="register-name"
              type="text"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Jane Doe"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="register-email">Work Email</label>
            <input
              id="register-email"
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="jane@company.com"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="register-password">Password (min. 6 characters)</label>
            <input
              id="register-password"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Creating workspace..." : "Create Account & Start →"}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account?
          <Link href="/login" className="auth-link">Sign In</Link>
        </div>
      </div>
    </div>
  );
}
