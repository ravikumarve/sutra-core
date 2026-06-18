"use client";

import { Suspense, type FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/dashboard";

  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/auth/login`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ phone_number: phoneNumber, password }),
        }
      );

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Invalid credentials");
      }

      const data = await res.json();
      document.cookie = `sutra_token=${data.data?.access_token || data.access_token}; path=/; max-age=86400; samesite=strict`;
      router.push(redirect);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-dvh flex items-center justify-center bg-bg-void">
      <div className="fixed inset-0 z-0">
        <div className="dot-matrix-overlay" />
        <div className="ambient-core" />
      </div>

      <div className="relative z-10 w-full max-w-md px-8">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-3 text-2xl font-bold text-text-main mb-3">
            <div className="w-4 h-4 border-2 border-emerald rounded-full shadow-[0_0_10px_var(--emerald-dim)]" />
            SUTRA Core
          </div>
          <p className="text-text-muted text-sm font-light">
            Sign in to your dashboard
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-bg-surface border border-border-dim rounded-2xl p-10 space-y-6"
        >
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg px-4 py-3 font-mono">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <label htmlFor="phone" className="font-mono text-xs text-text-muted uppercase tracking-wider">
              WhatsApp Number
            </label>
            <input
              id="phone"
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="+919876543210"
              required
              className="w-full bg-bg-void border border-border-dim rounded-lg px-4 py-3 text-text-main text-sm font-light placeholder:text-text-faint outline-none transition-colors focus:border-emerald focus:ring-1 focus:ring-emerald/30"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="font-mono text-xs text-text-muted uppercase tracking-wider">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full bg-bg-void border border-border-dim rounded-lg px-4 py-3 text-text-main text-sm font-light placeholder:text-text-faint outline-none transition-colors focus:border-emerald focus:ring-1 focus:ring-emerald/30"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-titanium text-bg-void font-mono text-xs uppercase tracking-wider rounded-full transition-all duration-500 hover:bg-transparent hover:text-titanium hover:border hover:border-titanium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="inline-flex items-center gap-2">
                <span className="w-3 h-3 border-2 border-bg-void border-t-transparent rounded-full animate-spin" />
                Authenticating...
              </span>
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        <p className="text-center text-text-faint text-xs mt-6 font-mono">
          Demo: +919876543210 / password123
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-dvh flex items-center justify-center bg-bg-void">
          <div className="w-6 h-6 border-2 border-emerald border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
