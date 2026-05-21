import { ArrowRight, Clock, FileUp, Landmark, TrendingDown, TrendingUp } from "lucide-react";
import { Link } from "react-router-dom";

import { ApiError } from "../services/apiClient";
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  DataStatusBadge,
  EmptyState,
  ErrorState,
  FeatureDisabledState,
  LoadingState,
  Table,
  Td,
  Th
} from "../components/ui";
import { useMarketOverview } from "../hooks/useMarketOverview";
import type { DataStatus } from "../types/dataStatus";
import type { MarketIndexCard, MarketMover, MarketOverviewResponse, SectorIndexCard } from "../types/marketOverview";

export function MarketPage() {
  const marketOverview = useMarketOverview();

  if (marketOverview.isLoading) {
    return <LoadingState label="Loading market overview" />;
  }

  if (marketOverview.isError) {
    if (isMarketOverviewDisabled(marketOverview.error)) {
      return (
        <FeatureDisabledState
          feature="Market overview"
          detail="The backend market overview feature flag is disabled. Portfolio upload and dashboard workflows are still available."
        />
      );
    }

    return <ErrorState title="Unable to load market overview" detail={marketOverview.error.message} />;
  }

  if (!marketOverview.data) {
    return <EmptyState title="Market overview" detail="No market overview data is available yet." />;
  }

  return <MarketOverviewContent overview={marketOverview.data} />;
}

function MarketOverviewContent({ overview }: { overview: MarketOverviewResponse }) {
  const status = overview.market_status;
  const statusWarning = overview.data_status.warning ?? status.data_status.warning;

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <DataStatusBadge status={overview.data_status} />
            <DataStatusBadge status={status.data_status} compact />
          </div>
          <div>
            <p className="text-sm font-semibold uppercase text-accent">Market context</p>
            <h1 className="mt-1 text-3xl font-semibold text-ink">{status.market} market overview</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              {status.exchange ? `${status.exchange} · ` : ""}
              Market is {formatMarketState(status.state)} as of {formatDateTime(status.as_of)} ({status.timezone}).
            </p>
          </div>
          {statusWarning ? (
            <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-900">
              {statusWarning}
            </div>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-2">
          <Link to="/upload">
            <Button>
              <FileUp size={16} />
              Upload holdings
            </Button>
          </Link>
          <Link to="/">
            <Button variant="secondary">
              Demo entry
              <ArrowRight size={16} />
            </Button>
          </Link>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {overview.major_indices.length ? (
          overview.major_indices.map((index) => <IndexCard key={index.symbol} index={index} />)
        ) : (
          <div className="md:col-span-3">
            <EmptyState title="Major indices" detail="No index cards were returned by the market overview endpoint." />
          </div>
        )}
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <SectorIndicesCard sectors={overview.sector_indices} />
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Market status</CardTitle>
              <p className="mt-1 text-sm text-slate-600">Session timing and source freshness.</p>
            </div>
            <Landmark className="text-accent" size={22} />
          </CardHeader>
          <div className="grid gap-3 sm:grid-cols-2">
            <StatusItem label="State" value={formatMarketState(status.state)} />
            <StatusItem label="Generated" value={formatDateTime(overview.generated_at)} />
            <StatusItem label="Next open" value={status.next_open_at ? formatDateTime(status.next_open_at) : "N/A"} />
            <StatusItem label="Next close" value={status.next_close_at ? formatDateTime(status.next_close_at) : "N/A"} />
          </div>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <MoversCard title="Top gainers" movers={overview.top_gainers} direction="up" />
        <MoversCard title="Top losers" movers={overview.top_losers} direction="down" />
      </section>
    </div>
  );
}

function IndexCard({ index }: { index: MarketIndexCard }) {
  const changeTone = getChangeTone(index.change_percent);
  const Icon = changeTone === "negative" ? TrendingDown : TrendingUp;

  return (
    <Card>
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-slate-500">{index.symbol}</p>
          <CardTitle className="mt-1">{index.name}</CardTitle>
        </div>
        <DataStatusBadge status={index.data_status} compact />
      </div>
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-3xl font-semibold text-ink">{formatNumber(index.value)}</p>
          <p className="mt-2 text-sm text-slate-500">{index.exchange ?? index.currency}</p>
        </div>
        <div className={changeTone === "negative" ? "text-right text-coral" : "text-right text-emerald-700"}>
          <Icon className="ml-auto" size={18} />
          <p className="mt-1 text-sm font-semibold">{formatPercent(index.change_percent)}</p>
          <p className="text-xs">{formatSignedNumber(index.change)}</p>
        </div>
      </div>
    </Card>
  );
}

function SectorIndicesCard({ sectors }: { sectors: SectorIndexCard[] }) {
  if (!sectors.length) {
    return <EmptyState title="Sector indices" detail="No sector index rows were returned by the market overview endpoint." />;
  }

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Sector indices</CardTitle>
          <p className="mt-1 text-sm text-slate-600">India sector movement with source labels.</p>
        </div>
      </CardHeader>
      <Table>
        <thead>
          <tr>
            <Th>Sector</Th>
            <Th>Index</Th>
            <Th>Value</Th>
            <Th>Change</Th>
            <Th>Source</Th>
          </tr>
        </thead>
        <tbody>
          {sectors.map((sector) => (
            <tr key={sector.symbol}>
              <Td>
                <span className="font-medium text-ink">{sector.sector}</span>
              </Td>
              <Td>{sector.name}</Td>
              <Td>{formatNumber(sector.value)}</Td>
              <Td className={getChangeTone(sector.change_percent) === "negative" ? "text-coral" : "text-emerald-700"}>
                {formatPercent(sector.change_percent)}
              </Td>
              <Td>
                <DataStatusBadge status={sector.data_status} compact />
              </Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function MoversCard({ title, movers, direction }: { title: string; movers: MarketMover[]; direction: "up" | "down" }) {
  if (!movers.length) {
    return <EmptyState title={title} detail="No mover rows were returned by the market overview endpoint." />;
  }

  const Icon = direction === "up" ? TrendingUp : TrendingDown;

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{title}</CardTitle>
          <p className="mt-1 text-sm text-slate-600">Price moves from the configured market data provider.</p>
        </div>
        <Icon className={direction === "up" ? "text-emerald-700" : "text-coral"} size={22} />
      </CardHeader>
      <Table>
        <thead>
          <tr>
            <Th>Symbol</Th>
            <Th>Price</Th>
            <Th>Move</Th>
            <Th>Source</Th>
          </tr>
        </thead>
        <tbody>
          {movers.map((mover) => (
            <tr key={mover.symbol}>
              <Td>
                <div>
                  <p className="font-medium text-ink">{mover.symbol}</p>
                  <p className="text-xs text-slate-500">{mover.company_name}</p>
                </div>
              </Td>
              <Td>{formatCurrency(mover.last_price, mover.currency)}</Td>
              <Td className={getChangeTone(mover.change_percent) === "negative" ? "text-coral" : "text-emerald-700"}>
                <span className="font-semibold">{formatPercent(mover.change_percent)}</span>
                <span className="ml-1 text-xs">({formatSignedNumber(mover.change)})</span>
              </Td>
              <Td>
                <DataStatusBadge status={mover.data_status} compact />
              </Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function StatusItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase text-slate-500">
        <Clock size={13} />
        {label}
      </div>
      <p className="mt-1 text-sm font-semibold text-ink">{value}</p>
    </div>
  );
}

function isMarketOverviewDisabled(error: unknown) {
  return (
    error instanceof ApiError &&
    error.status === 404 &&
    typeof error.details === "object" &&
    error.details !== null &&
    "feature" in error.details &&
    error.details.feature === "ENABLE_MARKET_OVERVIEW"
  );
}

function getChangeTone(value: number | null) {
  return value !== null && value < 0 ? "negative" : "positive";
}

function formatMarketState(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2
  }).format(value);
}

function formatCurrency(value: number, currency: string) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2
  }).format(value);
}

function formatPercent(value: number | null) {
  if (value === null) {
    return "N/A";
  }
  return `${value > 0 ? "+" : ""}${new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2
  }).format(value)}%`;
}

function formatSignedNumber(value: number | null) {
  if (value === null) {
    return "N/A";
  }
  return `${value > 0 ? "+" : ""}${formatNumber(value)}`;
}
