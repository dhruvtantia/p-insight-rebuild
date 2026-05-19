import { CheckCircle2, CreditCard, Lock } from "lucide-react";

import { Badge, Button, Card, CardTitle, ErrorState, LoadingState } from "../components/ui";
import { useBilling } from "../hooks/useBilling";
import { demoModeEnabled } from "../lib/env";
import type { BillingPlan } from "../types/billing";

export function BillingPage() {
  const billing = useBilling();

  if (billing.plan.isLoading) {
    return <LoadingState label="Loading billing plan" />;
  }

  if (billing.plan.isError || !billing.plan.data) {
    return <ErrorState title="Unable to load billing" detail={billing.plan.error?.message} />;
  }

  return (
    <div className="space-y-6">
      <BillingHeader />

      <Card>
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle>Current plan: {billing.plan.data.current_plan}</CardTitle>
            <p className="mt-2 text-sm leading-6 text-slate-600">{billing.plan.data.message}</p>
          </div>
          {demoModeEnabled ? (
            <Button
              type="button"
              disabled={billing.createCheckoutSession.isPending}
              onClick={() => billing.createCheckoutSession.mutate()}
            >
              <CreditCard size={16} />
              {billing.createCheckoutSession.isPending ? "Opening" : "Checkout placeholder"}
            </Button>
          ) : null}
        </div>
        {billing.createCheckoutSession.data ? (
          <p className="mt-3 text-sm text-slate-600">{billing.createCheckoutSession.data.message}</p>
        ) : null}
        {billing.createCheckoutSession.isError ? (
          <div className="mt-4">
            <ErrorState title="Checkout unavailable" detail={billing.createCheckoutSession.error.message} />
          </div>
        ) : null}
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        {billing.plan.data.plans.map((plan) => (
          <PlanCard key={plan.id} plan={plan} />
        ))}
      </div>

      <Card>
        <CardTitle>Usage snapshot</CardTitle>
        <div className="mt-4 grid gap-4 md:grid-cols-4">
          <UsageMetric label="Portfolios" value={billing.plan.data.usage.portfolio_count} />
          <UsageMetric label="Holdings" value={billing.plan.data.usage.holdings_count} />
          <UsageMetric label="AI conversations" value={billing.plan.data.usage.ai_conversation_count} />
          <UsageMetric label="Enforcement" value={billing.plan.data.usage.enforcement_enabled ? "On" : "Off"} />
        </div>
      </Card>
    </div>
  );
}

function BillingHeader() {
  return (
    <section>
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Billing</p>
      <h1 className="mt-1 text-3xl font-semibold">Plans and usage</h1>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
        Billing is a placeholder for beta. Plan surfaces are visible, but no Stripe checkout is active yet.
      </p>
    </section>
  );
}

function PlanCard({ plan }: { plan: BillingPlan }) {
  return (
    <Card className={plan.is_current ? "border-accent" : ""}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-ink">{plan.name}</h3>
          <p className="mt-1 text-2xl font-semibold">{plan.price_label}</p>
        </div>
        {plan.is_current ? <Badge>current</Badge> : plan.is_available ? null : <Lock className="text-slate-400" size={20} />}
      </div>
      <ul className="mt-5 grid gap-3">
        {plan.features.map((feature) => (
          <li key={feature} className="flex items-start gap-2 text-sm text-slate-700">
            <CheckCircle2 className="mt-0.5 text-accent" size={15} />
            <span>{feature}</span>
          </li>
        ))}
      </ul>
      <Button type="button" variant={plan.is_current ? "primary" : "secondary"} disabled={!plan.is_available || plan.is_current} className="mt-5 w-full">
        {plan.is_current ? "Current plan" : plan.is_available ? "Select plan" : "Coming soon"}
      </Button>
    </Card>
  );
}

function UsageMetric({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-ink">{value}</p>
    </div>
  );
}
