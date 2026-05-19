import { MessageSquare, Menu, Search } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import { betaFeedbackUrl } from "../../lib/env";
import { Button, Input } from "../ui";

const pageTitles: Record<string, string> = {
  "/": "Landing",
  "/login": "Login",
  "/signup": "Signup",
  "/onboarding": "Onboarding",
  "/dashboard": "Dashboard",
  "/holdings": "Holdings",
  "/upload": "Upload",
  "/analytics": "Analytics",
  "/advisor": "AI Advisor",
  "/watchlist": "Watchlist",
  "/brokers": "Broker Connections",
  "/billing": "Billing",
  "/settings": "Settings",
  "/admin": "Admin"
};

export function Header() {
  const location = useLocation();
  const title = pageTitles[location.pathname] ?? "P-insight";

  return (
    <header className="sticky top-0 z-10 border-b border-line bg-white/95 backdrop-blur">
      <div className="flex min-h-16 items-center justify-between gap-4 px-4 md:px-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" className="h-9 w-9 p-0 lg:hidden" aria-label="Open navigation">
            <Menu size={18} />
          </Button>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Workspace</p>
            <h2 className="text-lg font-semibold text-ink">{title}</h2>
          </div>
        </div>

        <div className="hidden w-full max-w-sm items-center gap-2 md:flex">
          <div className="relative w-full">
            <Search className="pointer-events-none absolute left-3 top-2.5 text-slate-400" size={16} />
            <Input className="pl-9" placeholder="Search symbols or portfolios" />
          </div>
        </div>

        <div className="flex items-center gap-2">
          {betaFeedbackUrl ? (
            <a
              href={betaFeedbackUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-semibold text-ink transition hover:bg-surface"
            >
              <MessageSquare size={16} />
              <span className="hidden sm:inline">Feedback</span>
            </a>
          ) : null}
          <Link to="/login" className="hidden text-sm font-medium text-slate-600 hover:text-ink sm:inline">
            Log in
          </Link>
          <Link to="/signup">
            <Button>Sign up</Button>
          </Link>
        </div>
      </div>
    </header>
  );
}
