import { AlertTriangle, ExternalLink, GitCompareArrows, Search } from "lucide-react";
import { useEffect, useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";

import {
  Badge,
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
import { useHoldings } from "../hooks/useHoldings";
import { usePeerComparison } from "../hooks/usePeers";
import { usePortfolios } from "../hooks/usePortfolios";
import { ApiError } from "../services/apiClient";
import type { AssetFundamentals, FundamentalMetrics } from "../types/fundamentals";
import type { MetricComparisonRow, PeerComparisonResponse, PeerSetQuality } from "../types/peers";

type MetricKind = "multiple" | "percent" | "currency" | "number";

const METRIC_FORMATS: Record<string, MetricKind> = {
  pe_ratio: "multiple",
  forward_pe: "multiple",
  price_to_book: "multiple",
  ev_to_ebitda: "multiple",
  peg: "multiple",
  roe: "percent",
  roa: "percent",
  operating_margin: "percent",
  net_margin: "percent",
  revenue_growth: "percent",
  eps_growth: "percent",
  dividend_yield: "percent",
  debt_to_equity: "multiple",
  market_cap: "currency"
};

export function PeersPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tickerParam = searchParams.get("ticker")?.trim().toUpperCase() || "";
  const portfolios = usePortfolios();
  const selectedPortfolio = portfolios.data?.[0] ?? null;
  const holdings = useHoldings(selectedPortfolio?.id);
  const holdingSymbols = useMemo(
    () => Array.from(new Set((holdings.data ?? []).map((holding) => holding.symbol.toUpperCase()))).sort(),
    [holdings.data]
  );
  const selectedSymbol = tickerParam || holdingSymbols[0] || "";
  const comparison = usePeerComparison(selectedPortfolio?.id, selectedSymbol || null);

  useEffect(() => {
    if (!tickerParam && holdingSymbols[0]) {
      setSearchParams({ ticker: holdingSymbols[0] }, { replace: true });
    }
  }, [holdingSymbols, setSearchParams, tickerParam]);

  if (portfolios.isLoading) {
    return <LoadingState label="Loading portfolios" />;
  }

  if (portfolios.isError) {
    return <ErrorState title="Unable to load portfolios" detail={portfolios.error.message} />;
  }

  if (!selectedPortfolio) {
    return (
      <div className="space-y-6">
        <PeersHeader />
        <EmptyState title="No portfolio yet" detail="Create a portfolio before comparing holding peers." />
        <Link to="/onboarding">
          <Button>Create portfolio</Button>
        </Link>
      </div>
    );
  }

  const disabledError = getFeatureDisabledError(comparison.error);

  function handleSymbolChange(symbol: string) {
    setSearchParams({ ticker: symbol.toUpperCase() });
  }

  return (
    <div className="space-y-6">
      <PeersHeader />

      {disabledError ? (
        <FeatureDisabledState
          feature="Peer comparison"
          detail="The backend peers feature flag is disabled in this environment."
        />
      ) : null}

      {holdings.isLoading ? (
        <LoadingState label="Loading holdings" />
      ) : holdings.isError ? (
        <ErrorState title="Unable to load holdings" detail={holdings.error.message} />
      ) : holdingSymbols.length || tickerParam ? (
        <HoldingSelector
          symbols={holdingSymbols}
          selectedSymbol={selectedSymbol}
          tickerParam={tickerParam}
          disabled={Boolean(disabledError)}
          onChange={handleSymbolChange}
        />
      ) : (
        <EmptyState title="No holdings" detail="Add holdings before using the portfolio holding selector." />
      )}

      {!selectedSymbol ? null : comparison.isLoading ? (
        <LoadingState label="Loading peer comparison" />
      ) : comparison.isError && !disabledError ? (
        <ErrorState title="Unable to load peer comparison" detail={comparison.error.message} />
      ) : comparison.data ? (
        <PeerComparisonContent comparison={comparison.data} />
      ) : null}
    </div>
  );
}

function PeersHeader() {
  return (
    <section className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Peers</p>
        <h1 className="mt-1 text-3xl font-semibold">Peer comparison</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Backend peer sets and fundamentals comparisons with static, sparse, and mock-data warnings visible.
        </p>
      </div>
      <Link to="/fundamentals">
        <Button variant="secondary">
          <ExternalLink size={16} />
          Fundamentals
        </Button>
      </Link>
    </section>
  );
}

function HoldingSelector({
  symbols,
  selectedSymbol,
  tickerParam,
  disabled,
  onChange
}: {
  symbols: string[];
  selectedSymbol: string;
  tickerParam: string;
  disabled: boolean;
  onChange: (symbol: string) => void;
}) {
  const hasDeepLinkedUnknown = Boolean(tickerParam && !symbols.includes(tickerParam));

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Portfolio holding selector</CardTitle>
          <p className="mt-1 text-sm text-slate-600">Select a holding, or open `/peers?ticker=SYMBOL` directly.</p>
        </div>
        <Search className="text-accent" size={22} />
      </CardHeader>
      <label className="block max-w-xl">
        <span className="mb-1 block text-sm font-medium text-slate-600">Holding</span>
        <select
          className="h-10 w-full rounded-md border border-line bg-white px-3 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/15 disabled:opacity-60"
          value={selectedSymbol}
          onChange={(event) => onChange(event.target.value)}
          disabled={disabled}
        >
          {hasDeepLinkedUnknown ? <option value={tickerParam}>{tickerParam} (deep link)</option> : null}
          {symbols.map((symbol) => (
            <option key={symbol} value={symbol}>
              {symbol}
            </option>
          ))}
        </select>
      </label>
    </Card>
  );
}

function PeerComparisonContent({ comparison }: { comparison: PeerComparisonResponse }) {
  const allCompanies = [comparison.selected_company, ...comparison.peer_companies];

  return (
    <div className="space-y-6">
      <QualityWarnings comparison={comparison} />

      <section className="grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <SelectedCompanyCard company={comparison.selected_company} ranks={comparison.simple_ranks[comparison.symbol]} />
        <PeerSetQualityCard quality={comparison.peer_set_quality} />
      </section>

      {comparison.peer_companies.length ? (
        <PeerCompaniesTable companies={comparison.peer_companies} />
      ) : (
        <EmptyState title="No peer companies" detail="The backend returned no peer companies for this symbol." />
      )}

      <MetricComparisonTable rows={comparison.metric_comparison_table} companies={allCompanies} />
    </div>
  );
}

function QualityWarnings({ comparison }: { comparison: PeerComparisonResponse }) {
  const warnings = [...comparison.warnings];
  if (comparison.peer_set_quality.is_static) {
    warnings.unshift("Peer sets come from a static India peer map, not live research coverage.");
  }
  if (comparison.peer_set_quality.is_sparse) {
    warnings.unshift("Peer set is sparse; comparison breadth is limited.");
  }

  const dataStatusWarnings = [comparison.selected_company, ...comparison.peer_companies]
    .map((company) => company.data_status.warning)
    .filter((warning): warning is string => Boolean(warning));

  return (
    <div className="space-y-3">
      {Array.from(new Set([...warnings, ...dataStatusWarnings])).map((warning) => (
        <WarningBanner key={warning} detail={warning} />
      ))}
    </div>
  );
}

function WarningBanner({ detail }: { detail: string }) {
  return (
    <Card className="border-amber-200 bg-amber-50">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 text-amber-700" size={20} />
        <div>
          <h3 className="text-sm font-semibold text-amber-900">Peer quality warning</h3>
          <p className="mt-1 text-sm text-amber-800">{detail}</p>
        </div>
      </div>
    </Card>
  );
}

function SelectedCompanyCard({
  company,
  ranks
}: {
  company: AssetFundamentals;
  ranks?: Record<string, number | null>;
}) {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Selected company</CardTitle>
          <p className="mt-1 text-sm text-slate-600">Fundamentals are provided by the backend peer comparison response.</p>
        </div>
        <GitCompareArrows className="text-accent" size={22} />
      </CardHeader>
      <div className="space-y-4">
        <div>
          <p className="text-2xl font-semibold text-ink">{company.symbol}</p>
          <p className="text-sm text-slate-600">{company.company_name ?? "No company name returned"}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <DataStatusBadge status={company.data_status} />
          <Badge tone={company.coverage.is_complete ? "success" : "warning"}>
            {formatPercent(company.coverage.coverage_ratio * 100)} metric coverage
          </Badge>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <MetricBlock label="P/E" value={formatMetric(company.metrics.pe_ratio, "multiple", company.currency)} />
          <MetricBlock label="ROE" value={formatMetric(company.metrics.roe, "percent", company.currency)} />
          <MetricBlock label="Market cap" value={formatMetric(company.metrics.market_cap, "currency", company.currency)} />
          <MetricBlock label="P/E rank" value={formatRank(ranks?.pe_ratio)} />
        </div>
      </div>
    </Card>
  );
}

function PeerSetQualityCard({ quality }: { quality: PeerSetQuality }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Peer set quality</CardTitle>
        <Badge tone={quality.is_sparse ? "warning" : "success"}>{quality.is_sparse ? "Sparse" : "Usable"}</Badge>
      </CardHeader>
      <div className="grid gap-3 sm:grid-cols-2">
        <MetricBlock label="Source" value={formatSource(quality.source)} />
        <MetricBlock label="Peer count" value={String(quality.peer_count)} />
        <MetricBlock label="Covered peers" value={String(quality.covered_peer_count)} />
        <MetricBlock label="Coverage" value={formatPercent(quality.coverage_percent)} />
      </div>
      {quality.missing_peer_symbols.length ? (
        <p className="mt-4 text-sm text-amber-800">Missing peers: {quality.missing_peer_symbols.join(", ")}</p>
      ) : null}
    </Card>
  );
}

function MetricBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
      <p className="mt-1 text-base font-semibold text-ink">{value}</p>
    </div>
  );
}

function PeerCompaniesTable({ companies }: { companies: AssetFundamentals[] }) {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Peer companies</CardTitle>
          <p className="mt-1 text-sm text-slate-600">Peer rows include backend fundamentals coverage and source status.</p>
        </div>
        <Badge>{companies.length} peers</Badge>
      </CardHeader>
      <Table>
        <thead>
          <tr>
            <Th>Company</Th>
            <Th>P/E</Th>
            <Th>ROE</Th>
            <Th>Growth</Th>
            <Th>Market cap</Th>
            <Th>Coverage</Th>
            <Th>Source</Th>
          </tr>
        </thead>
        <tbody>
          {companies.map((company) => (
            <tr key={company.symbol}>
              <Td>
                <div>
                  <p className="font-medium text-ink">{company.symbol}</p>
                  <p className="text-xs text-slate-500">{company.company_name ?? "N/A"}</p>
                </div>
              </Td>
              <Td>{formatMetric(company.metrics.pe_ratio, "multiple", company.currency)}</Td>
              <Td>{formatMetric(company.metrics.roe, "percent", company.currency)}</Td>
              <Td>{formatMetric(company.metrics.revenue_growth, "percent", company.currency)}</Td>
              <Td>{formatMetric(company.metrics.market_cap, "currency", company.currency)}</Td>
              <Td>
                <Badge tone={company.coverage.is_complete ? "success" : "warning"}>
                  {formatPercent(company.coverage.coverage_ratio * 100)}
                </Badge>
              </Td>
              <Td>
                <DataStatusBadge status={company.data_status} compact />
              </Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function MetricComparisonTable({ rows, companies }: { rows: MetricComparisonRow[]; companies: AssetFundamentals[] }) {
  const peerSymbols = companies.slice(1).map((company) => company.symbol);

  if (!rows.length) {
    return <EmptyState title="No metric comparisons" detail="The backend returned no metric comparison rows." />;
  }

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Metric comparison</CardTitle>
          <p className="mt-1 text-sm text-slate-600">Rows, peer averages, and ranks are calculated by the backend.</p>
        </div>
      </CardHeader>
      <Table>
        <thead>
          <tr>
            <Th>Metric</Th>
            <Th>Direction</Th>
            <Th>Selected</Th>
            {peerSymbols.map((symbol) => (
              <Th key={symbol}>{symbol}</Th>
            ))}
            <Th>Peer avg</Th>
            <Th>Rank</Th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const kind = METRIC_FORMATS[row.metric] ?? "number";
            const selectedCurrency = companies[0]?.currency ?? "INR";
            return (
              <tr key={row.metric}>
                <Td className="font-medium text-ink">{formatMetricName(row.metric)}</Td>
                <Td>{formatDirection(row.direction)}</Td>
                <Td>{formatMetric(row.selected_value, kind, selectedCurrency)}</Td>
                {peerSymbols.map((symbol) => (
                  <Td key={symbol}>{formatMetric(row.peer_values[symbol] ?? null, kind, selectedCurrency)}</Td>
                ))}
                <Td>{formatMetric(row.peer_average, kind, selectedCurrency)}</Td>
                <Td>{formatRank(row.selected_rank)}</Td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    </Card>
  );
}

function getFeatureDisabledError(error: unknown) {
  if (!(error instanceof ApiError)) {
    return null;
  }

  const details = typeof error.details === "object" && error.details !== null ? error.details : {};
  const feature = "feature" in details ? details.feature : null;
  return error.code === "feature_disabled" || feature === "ENABLE_PEERS" ? error : null;
}

function formatMetric(value: number | null, kind: MetricKind, currency: string) {
  if (value === null) {
    return "N/A";
  }
  if (kind === "percent") {
    return formatPercent(value * 100);
  }
  if (kind === "currency") {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      notation: "compact",
      maximumFractionDigits: 2
    }).format(value);
  }
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2
  }).format(value);
}

function formatPercent(value: number | null) {
  if (value === null) {
    return "N/A";
  }
  return `${new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2
  }).format(value)}%`;
}

function formatRank(value: number | null | undefined) {
  return value ? `#${value}` : "N/A";
}

function formatMetricName(value: string) {
  return value
    .split("_")
    .map((part) => part.toUpperCase())
    .join(" ");
}

function formatDirection(value: string) {
  return value === "lower_is_better" ? "Lower is better" : "Higher is better";
}

function formatSource(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
