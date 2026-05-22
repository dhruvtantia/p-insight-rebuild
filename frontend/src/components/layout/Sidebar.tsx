import {
  BarChart3,
  Bot,
  Building2,
  CreditCard,
  FileUp,
  Gauge,
  GitCompareArrows,
  Home,
  Landmark,
  LineChart,
  ListChecks,
  Lock,
  SearchCheck,
  Settings,
  Shield,
  SlidersHorizontal,
  Sparkles,
  Star,
  UsersRound
} from "lucide-react";
import { NavLink } from "react-router-dom";

import { cn } from "../../lib/cn";

const navItems = [
  { to: "/", label: "Landing", icon: Home },
  { to: "/onboarding", label: "Onboarding", icon: ListChecks },
  { to: "/market", label: "Market", icon: Landmark },
  { to: "/dashboard", label: "Dashboard", icon: Gauge },
  { to: "/changes", label: "Changes", icon: GitCompareArrows },
  { to: "/holdings", label: "Holdings", icon: BarChart3 },
  { to: "/upload", label: "Upload", icon: FileUp },
  { to: "/analytics", label: "Analytics", icon: LineChart },
  { to: "/fundamentals", label: "Fundamentals", icon: SearchCheck },
  { to: "/peers", label: "Peers", icon: UsersRound },
  { to: "/advisor", label: "AI Advisor", icon: Bot },
  { to: "/simulate", label: "Simulate", icon: SlidersHorizontal },
  { to: "/optimize", label: "Optimize", icon: Sparkles },
  { to: "/watchlist", label: "Watchlist", icon: Star },
  { to: "/brokers", label: "Brokers", icon: Building2 },
  { to: "/billing", label: "Billing", icon: CreditCard },
  { to: "/settings", label: "Settings", icon: Settings },
  { to: "/admin", label: "Admin", icon: Shield }
];

type SidebarProps = {
  width?: number;
};

export function Sidebar({ width }: SidebarProps) {
  return (
    <aside
      className="hidden min-h-screen shrink-0 border-r border-line bg-white px-4 py-5 lg:block"
      style={width ? { width, flexBasis: width } : undefined}
    >
      <div className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">P-insight</p>
        <h1 className="mt-1 text-xl font-semibold text-ink">Portfolio OS</h1>
      </div>

      <nav className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition",
                  isActive ? "bg-accent text-white" : "text-slate-600 hover:bg-surface hover:text-ink"
                )
              }
            >
              <Icon size={17} />
              {item.label}
            </NavLink>
          );
        })}
      </nav>

      <div className="mt-8 rounded-md border border-line bg-surface p-3 text-xs text-slate-600">
        <div className="mb-2 flex items-center gap-2 font-semibold text-ink">
          <Lock size={14} />
          Backend-only keys
        </div>
        Market data, AI, broker, and payment secrets stay on the API server.
      </div>
    </aside>
  );
}
