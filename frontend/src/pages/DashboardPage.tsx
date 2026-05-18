import { Bot, PieChart, Plus, WalletCards } from "lucide-react";
import { Link } from "react-router-dom";

import { Button, Card, CardTitle, EmptyState, ErrorState, LoadingState, Table, Td, Th } from "../components/ui";
import { useHoldings } from "../hooks/useHoldings";
import { usePortfolios } from "../hooks/usePortfolios";
import type { Portfolio } from "../types/portfolio";

export function DashboardPage() {
  const portfolios = usePortfolios();
  const selectedPortfolio = portfolios.data?.[0] ?? null;
  const holdings = useHoldings(selectedPortfolio?.id);

  if (portfolios.isLoading) {
    return <LoadingState label="Loading portfolios" />;
  }

  if (portfolios.isError) {
    return <ErrorState title="Unable to load portfolios" detail={portfolios.error.message} />;
  }

  if (!portfolios.data?.length) {
    return (
      <div className="space-y-6">
        <DashboardHeader />
        <EmptyState title="No portfolio yet" detail="Create a portfolio to populate the dashboard shell." />
        <Link to="/onboarding">
          <Button>
            <Plus size={16} />
            Create portfolio
          </Button>
        </Link>
        <DashboardPlaceholders />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <DashboardHeader />
      <PortfolioSummary portfolio={selectedPortfolio!} />
      <DashboardPlaceholders />
      <HoldingsPreview portfolioId={selectedPortfolio!.id} isLoading={holdings.isLoading} isError={holdings.isError} holdings={holdings.data ?? []} errorMessage={holdings.error?.message} />
    </div>
  );
}

function DashboardHeader() {
  return (
    <section className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Dashboard</p>
        <h1 className="mt-1 text-3xl font-semibold">Portfolio command center</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          This dashboard reads portfolio and holdings data from the backend. Analytics calculations stay server-side.
        </p>
      </div>
      <Link to="/holdings">
        <Button variant="secondary">Manage holdings</Button>
      </Link>
    </section>
  );
}

function PortfolioSummary({ portfolio }: { portfolio: Portfolio }) {
  return (
    <Card>
      <div className="grid gap-4 md:grid-cols-4">
        <SummaryItem label="Selected portfolio" value={portfolio.name} />
        <SummaryItem label="Base currency" value={portfolio.base_currency} />
        <SummaryItem label="Benchmark" value={portfolio.benchmark_symbol ?? "--"} />
        <SummaryItem label="Risk-free rate" value={portfolio.risk_free_rate === null ? "--" : `${portfolio.risk_free_rate}`} />
      </div>
    </Card>
  );
}

function DashboardPlaceholders() {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <SummaryCard title="Market value" value="Backend analytics later" icon={WalletCards} />
        <SummaryCard title="Allocation" value="Chart placeholder" icon={PieChart} />
        <SummaryCard title="AI summary" value="Context placeholder" icon={Bot} />
      </div>
      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardTitle>Chart placeholders</CardTitle>
          <div className="mt-4 grid gap-3">
            <div className="h-56 rounded-md bg-surface" />
            <div className="grid grid-cols-4 gap-2">
              <div className="h-3 rounded bg-accent/70" />
              <div className="h-3 rounded bg-gold/70" />
              <div className="h-3 rounded bg-coral/70" />
              <div className="h-3 rounded bg-slate-300" />
            </div>
          </div>
        </Card>
        <Card>
          <CardTitle>AI summary placeholder</CardTitle>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Advisor summaries will come from backend-structured portfolio context, not direct frontend AI calls.
          </p>
          <div className="mt-4 space-y-2">
            <div className="h-3 w-full rounded bg-surface" />
            <div className="h-3 w-5/6 rounded bg-surface" />
            <div className="h-3 w-2/3 rounded bg-surface" />
          </div>
        </Card>
      </div>
    </div>
  );
}

function HoldingsPreview({
  holdings,
  isLoading,
  isError,
  errorMessage
}: {
  portfolioId: string;
  holdings: Array<{ id: string; symbol: string; company_name: string | null; quantity: number; market_value: number | null }>;
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
}) {
  if (isLoading) {
    return <LoadingState label="Loading holdings preview" />;
  }

  if (isError) {
    return <ErrorState title="Unable to load holdings" detail={errorMessage} />;
  }

  if (!holdings.length) {
    return (
      <EmptyState
        title="No holdings yet"
        detail="Add holdings manually from the holdings page to start filling this preview."
      />
    );
  }

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between gap-4">
        <CardTitle>Holdings preview</CardTitle>
        <Link to="/holdings">
          <Button variant="secondary">Open holdings</Button>
        </Link>
      </div>
      <Table>
        <thead>
          <tr>
            <Th>Symbol</Th>
            <Th>Name</Th>
            <Th>Quantity</Th>
            <Th>Market value</Th>
          </tr>
        </thead>
        <tbody>
          {holdings.slice(0, 5).map((holding) => (
            <tr key={holding.id}>
              <Td className="font-semibold text-ink">{holding.symbol}</Td>
              <Td>{holding.company_name ?? "--"}</Td>
              <Td>{formatNumber(holding.quantity)}</Td>
              <Td>{formatCurrency(holding.market_value)}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function SummaryCard({ title, value, icon: Icon }: { title: string; value: string; icon: typeof WalletCards }) {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-600">{title}</p>
          <p className="mt-2 text-lg font-semibold">{value}</p>
        </div>
        <Icon className="text-accent" size={24} />
      </div>
    </Card>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">{label}</p>
      <p className="mt-1 text-base font-semibold text-ink">{value}</p>
    </div>
  );
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 4 }).format(value);
}

function formatCurrency(value: number | null) {
  if (value === null) return "--";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2
  }).format(value);
}
