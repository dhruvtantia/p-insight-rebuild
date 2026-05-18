import { ArrowRight, BarChart3, Bot, Building2, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge, Button, Card, CardTitle } from "../components/ui";

const features = [
  {
    title: "Portfolio analytics",
    detail: "Track holdings, allocation, concentration, and performance signals from clean portfolio data.",
    icon: BarChart3
  },
  {
    title: "AI explanations",
    detail: "Ask questions backed by structured portfolio context, not raw prompts or frontend secrets.",
    icon: Bot
  },
  {
    title: "Broker-ready model",
    detail: "Manual uploads come first, with broker connections normalizing into the same holdings model later.",
    icon: Building2
  }
];

export function LandingPage() {
  return (
    <div className="space-y-12">
      <section className="grid min-h-[520px] gap-8 py-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
        <div className="space-y-6">
          <Badge tone="success">Greenfield MVP</Badge>
          <div className="space-y-4">
            <h1 className="max-w-3xl text-5xl font-semibold leading-tight text-ink">
              Understand your portfolio in minutes.
            </h1>
            <p className="max-w-2xl text-lg leading-8 text-slate-600">
              Upload holdings or connect your broker to get analytics, risk insights, and AI-powered explanations.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to="/onboarding">
              <Button>
                Start onboarding
                <ArrowRight size={16} />
              </Button>
            </Link>
            <Link to="/dashboard">
              <Button variant="secondary">View dashboard shell</Button>
            </Link>
          </div>
        </div>

        <div className="rounded-md border border-line bg-white p-4 shadow-soft">
          <div className="grid gap-3">
            <div className="rounded-md bg-surface p-4">
              <div className="mb-4 flex items-center justify-between">
                <span className="text-sm font-semibold">Portfolio value</span>
                <Badge>Mock shell</Badge>
              </div>
              <div className="h-48 rounded-md bg-[linear-gradient(135deg,#197278_0%,#f6f7f7_55%,#d99b28_100%)]" />
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <Metric label="Holdings" value="24" />
              <Metric label="Risk flags" value="3" />
              <Metric label="AI notes" value="7" />
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <Card key={feature.title}>
              <Icon className="mb-4 text-accent" size={24} />
              <CardTitle>{feature.title}</CardTitle>
              <p className="mt-2 text-sm leading-6 text-slate-600">{feature.detail}</p>
            </Card>
          );
        })}
      </section>

      <section className="grid gap-4 lg:grid-cols-[1fr_1fr]">
        <Card>
          <div className="flex items-start gap-3">
            <ShieldCheck className="mt-1 text-accent" size={22} />
            <div>
              <CardTitle>Pricing preview</CardTitle>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Free starts with basic portfolios and limited AI usage. Pro expands portfolios, analytics, and question limits. Premium later is reserved for advanced broker sync and richer advisor workflows.
              </p>
            </div>
          </div>
        </Card>
        <Card>
          <CardTitle>Broker connections coming soon</CardTitle>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Plaid, Zerodha, IBKR, and Alpaca are planned as backend-only integrations that normalize into P-insight holdings and transactions.
          </p>
        </Card>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold">{value}</p>
    </div>
  );
}
