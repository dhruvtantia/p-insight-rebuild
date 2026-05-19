import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Briefcase, FileUp, LineChart } from "lucide-react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";

import { Button, Card, CardTitle, ErrorState, Input } from "../components/ui";
import { useDemoSeed } from "../hooks/useDemoSeed";
import { usePortfolios } from "../hooks/usePortfolios";

const steps = [
  { title: "Create portfolio", detail: "Name the portfolio and set base currency.", icon: Briefcase },
  { title: "Add holdings", detail: "Enter positions manually through the backend API.", icon: FileUp },
  { title: "Review analytics", detail: "Use backend-calculated metrics and insights later.", icon: LineChart }
];

const portfolioSchema = z.object({
  name: z.string().trim().min(1, "Portfolio name is required").max(120),
  base_currency: z.string().trim().length(3, "Use a 3-letter currency code").default("USD"),
  benchmark_symbol: z.string().trim().max(24).optional()
});

type PortfolioFormValues = z.infer<typeof portfolioSchema>;

export function OnboardingPage() {
  const navigate = useNavigate();
  const portfolios = usePortfolios();
  const demoSeed = useDemoSeed();
  const form = useForm<PortfolioFormValues>({
    resolver: zodResolver(portfolioSchema),
    defaultValues: {
      name: "",
      base_currency: "USD",
      benchmark_symbol: ""
    }
  });

  const onSubmit = form.handleSubmit((values) => {
    portfolios.createPortfolio.mutate(
      {
        name: values.name,
        base_currency: values.base_currency.toUpperCase(),
        benchmark_symbol: values.benchmark_symbol?.trim()
          ? values.benchmark_symbol.trim().toUpperCase()
          : null
      },
      {
        onSuccess: () => {
          navigate("/holdings");
        }
      }
    );
  });

  return (
    <div className="space-y-6">
      <section>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Onboarding</p>
        <h1 className="mt-1 text-3xl font-semibold">Create your first portfolio</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          This creates a backend portfolio for the deterministic demo user. Auth will be replaced later.
        </p>
      </section>

      <div className="grid gap-4 md:grid-cols-3">
        {steps.map((step) => {
          const Icon = step.icon;
          return (
            <Card key={step.title}>
              <Icon className="mb-4 text-accent" size={22} />
              <CardTitle>{step.title}</CardTitle>
              <p className="mt-2 text-sm leading-6 text-slate-600">{step.detail}</p>
            </Card>
          );
        })}
      </div>

      <Card className="max-w-2xl">
        <CardTitle>Portfolio details</CardTitle>
        <form className="mt-5 grid gap-4" onSubmit={onSubmit}>
          {portfolios.createPortfolio.isError ? (
            <ErrorState
              title="Could not create portfolio"
              detail={portfolios.createPortfolio.error.message}
            />
          ) : null}

          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Name</span>
            <Input placeholder="Core Portfolio" {...form.register("name")} />
            {form.formState.errors.name ? (
              <span className="text-xs text-coral">{form.formState.errors.name.message}</span>
            ) : null}
          </label>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="grid gap-2">
              <span className="text-sm font-medium text-ink">Base currency</span>
              <Input placeholder="USD" {...form.register("base_currency")} />
              {form.formState.errors.base_currency ? (
                <span className="text-xs text-coral">{form.formState.errors.base_currency.message}</span>
              ) : null}
            </label>
            <label className="grid gap-2">
              <span className="text-sm font-medium text-ink">Benchmark symbol</span>
              <Input placeholder="VOO" {...form.register("benchmark_symbol")} />
            </label>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button type="submit" disabled={portfolios.createPortfolio.isPending}>
              {portfolios.createPortfolio.isPending ? "Creating" : "Create portfolio"}
              <ArrowRight size={16} />
            </Button>
            <Button
              type="button"
              variant="secondary"
              disabled={demoSeed.isPending}
              onClick={() =>
                demoSeed.mutate(undefined, {
                  onSuccess: () => navigate("/dashboard")
                })
              }
            >
              {demoSeed.isPending ? "Seeding demo" : "Try demo portfolio"}
            </Button>
            {portfolios.data?.length ? (
              <Button type="button" variant="secondary" onClick={() => navigate("/dashboard")}>
                Continue to dashboard
              </Button>
            ) : null}
          </div>
          {demoSeed.isError ? (
            <ErrorState title="Could not seed demo portfolio" detail={demoSeed.error.message} />
          ) : null}
        </form>
      </Card>
    </div>
  );
}
