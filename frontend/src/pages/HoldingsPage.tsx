import { zodResolver } from "@hookform/resolvers/zod";
import { Clock, Edit2, Plus, RefreshCw, Save, Search, Trash2, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

import { Badge, Button, Card, CardTitle, EmptyState, ErrorState, Input, LoadingState, Table, Td, Th } from "../components/ui";
import { useHoldings } from "../hooks/useHoldings";
import { usePortfolioPrices } from "../hooks/usePortfolioPrices";
import { usePortfolios } from "../hooks/usePortfolios";
import type { Holding, HoldingCreateInput } from "../types/holdings";

const optionalMoney = z
  .string()
  .trim()
  .refine((value) => value === "" || Number(value) >= 0, "Must be zero or greater");

const holdingSchema = z.object({
  symbol: z.string().trim().min(1, "Symbol is required").max(24),
  company_name: z.string().trim().max(255).optional(),
  quantity: z.string().trim().refine((value) => Number(value) > 0, "Quantity must be positive"),
  average_cost: optionalMoney,
  current_price: optionalMoney,
  currency: z.string().trim().length(3, "Use a 3-letter currency code").default("USD"),
  sector: z.string().trim().max(120).optional(),
  asset_class: z.string().trim().max(80).optional(),
  exchange: z.string().trim().max(80).optional()
});

type HoldingFormValues = z.infer<typeof holdingSchema>;

const defaultHoldingValues: HoldingFormValues = {
  symbol: "",
  company_name: "",
  quantity: "",
  average_cost: "",
  current_price: "",
  currency: "USD",
  sector: "",
  asset_class: "",
  exchange: ""
};

export function HoldingsPage() {
  const portfolios = usePortfolios();
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState("");
  const [sectorFilter, setSectorFilter] = useState("all");
  const [editingHolding, setEditingHolding] = useState<Holding | null>(null);

  useEffect(() => {
    if (!selectedPortfolioId && portfolios.data?.length) {
      setSelectedPortfolioId(portfolios.data[0].id);
    }
  }, [portfolios.data, selectedPortfolioId]);

  const holdings = useHoldings(selectedPortfolioId || null);
  const portfolioPrices = usePortfolioPrices(selectedPortfolioId || null);

  const sectors = useMemo(() => {
    const values = new Set((holdings.data ?? []).map((holding) => holding.sector).filter(Boolean));
    return Array.from(values).sort() as string[];
  }, [holdings.data]);

  const latestPriceUpdatedAt = useMemo(() => getLatestPriceUpdatedAt(holdings.data ?? []), [holdings.data]);

  const filteredHoldings = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();
    return (holdings.data ?? []).filter((holding) => {
      const matchesSearch =
        !normalizedSearch ||
        holding.symbol.toLowerCase().includes(normalizedSearch) ||
        (holding.company_name ?? "").toLowerCase().includes(normalizedSearch);
      const matchesSector = sectorFilter === "all" || holding.sector === sectorFilter;
      return matchesSearch && matchesSector;
    });
  }, [holdings.data, searchTerm, sectorFilter]);

  if (portfolios.isLoading) {
    return <LoadingState label="Loading portfolios" />;
  }

  if (portfolios.isError) {
    return <ErrorState title="Unable to load portfolios" detail={portfolios.error.message} />;
  }

  if (!portfolios.data?.length) {
    return (
      <div className="space-y-6">
        <HoldingsHeader />
        <EmptyState title="No portfolio yet" detail="Create a portfolio before adding holdings." />
        <Link to="/onboarding">
          <Button>
            <Plus size={16} />
            Create portfolio
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <HoldingsHeader />

      <Card>
        <div className="grid gap-4 lg:grid-cols-[1fr_1fr_0.8fr_auto]">
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Portfolio</span>
            <select
              className="h-10 rounded-md border border-line bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/15"
              value={selectedPortfolioId}
              onChange={(event) => {
                setSelectedPortfolioId(event.target.value);
                setEditingHolding(null);
              }}
            >
              {portfolios.data.map((portfolio) => (
                <option key={portfolio.id} value={portfolio.id}>
                  {portfolio.name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Search</span>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-2.5 text-slate-400" size={16} />
              <Input
                className="pl-9"
                placeholder="Search symbol or name"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
              />
            </div>
          </label>
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Sector</span>
            <select
              className="h-10 rounded-md border border-line bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/15"
              value={sectorFilter}
              onChange={(event) => setSectorFilter(event.target.value)}
              disabled={!sectors.length}
            >
              <option value="all">All sectors</option>
              {sectors.map((sector) => (
                <option key={sector} value={sector}>
                  {sector}
                </option>
              ))}
            </select>
          </label>
          <div className="grid gap-2">
            <span className="text-sm font-medium text-ink">Prices</span>
            <Button
              type="button"
              onClick={() => portfolioPrices.refreshPrices.mutate()}
              disabled={!selectedPortfolioId || portfolioPrices.refreshPrices.isPending}
              className="w-full whitespace-nowrap"
            >
              <RefreshCw className={portfolioPrices.refreshPrices.isPending ? "animate-spin" : ""} size={16} />
              {portfolioPrices.refreshPrices.isPending ? "Refreshing" : "Refresh Prices"}
            </Button>
          </div>
        </div>
        <div className="mt-4 flex flex-col gap-3 border-t border-line pt-4 text-sm text-slate-600 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-2">
            <Clock size={16} className="text-accent" />
            <span>Last price update: {latestPriceUpdatedAt ? formatDateTime(latestPriceUpdatedAt) : "N/A"}</span>
          </div>
          {portfolioPrices.refreshPrices.data ? (
            <div className="flex flex-wrap items-center gap-2">
              <span>
                Refreshed {portfolioPrices.refreshPrices.data.refreshed_count} holding
                {portfolioPrices.refreshPrices.data.refreshed_count === 1 ? "" : "s"}
              </span>
              {uniqueSources(portfolioPrices.refreshPrices.data.holdings).map((source) => (
                <Badge key={source} tone={source.toLowerCase().includes("mock") ? "warning" : "neutral"}>
                  {source}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>
        {portfolioPrices.refreshPrices.isError ? (
          <div className="mt-4">
            <ErrorState title="Price refresh failed" detail={portfolioPrices.refreshPrices.error.message} />
          </div>
        ) : null}
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1fr_390px]">
        <HoldingsTable
          holdings={filteredHoldings}
          isLoading={holdings.isLoading}
          isError={holdings.isError}
          errorMessage={holdings.error?.message}
          onEdit={setEditingHolding}
          onDelete={(holding) => {
            if (window.confirm(`Delete ${holding.symbol}?`)) {
              holdings.deleteHolding.mutate(holding.id);
            }
          }}
          isDeleting={holdings.deleteHolding.isPending}
        />

        <HoldingForm
          key={`${selectedPortfolioId}-${editingHolding?.id ?? "new"}`}
          editingHolding={editingHolding}
          onCancelEdit={() => setEditingHolding(null)}
          onSubmit={(input) => {
            if (editingHolding) {
              holdings.updateHolding.mutate(
                { holdingId: editingHolding.id, input },
                { onSuccess: () => setEditingHolding(null) }
              );
            } else {
              holdings.createHolding.mutate(input);
            }
          }}
          isSubmitting={holdings.createHolding.isPending || holdings.updateHolding.isPending}
          errorMessage={
            holdings.createHolding.error?.message ??
            holdings.updateHolding.error?.message ??
            holdings.deleteHolding.error?.message
          }
        />
      </div>
    </div>
  );
}

function uniqueSources(items: Array<{ source: string }>) {
  return Array.from(new Set(items.map((item) => item.source).filter(Boolean))).sort();
}

function HoldingsHeader() {
  return (
    <section className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Holdings</p>
        <h1 className="mt-1 text-3xl font-semibold">Manual holdings</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Add, edit, and delete holdings through the backend portfolio APIs. Upload imports are staged and validated before holdings are created.
        </p>
      </div>
      <Link to="/upload">
        <Button variant="secondary">
          <FileUpIcon />
          Upload holdings
        </Button>
      </Link>
    </section>
  );
}

function FileUpIcon() {
  return <Plus size={16} />;
}

function HoldingsTable({
  holdings,
  isLoading,
  isError,
  errorMessage,
  onEdit,
  onDelete,
  isDeleting
}: {
  holdings: Holding[];
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
  onEdit: (holding: Holding) => void;
  onDelete: (holding: Holding) => void;
  isDeleting: boolean;
}) {
  if (isLoading) {
    return <LoadingState label="Loading holdings" />;
  }

  if (isError) {
    return <ErrorState title="Unable to load holdings" detail={errorMessage} />;
  }

  if (!holdings.length) {
    return <EmptyState title="No matching holdings" detail="Add a holding or adjust search and sector filters." />;
  }

  return (
    <Table>
      <thead>
        <tr>
          <Th>Symbol</Th>
          <Th>Name</Th>
          <Th>Quantity</Th>
          <Th>Average Cost</Th>
          <Th>Current Price</Th>
          <Th>Market Value</Th>
          <Th>Total P/L</Th>
          <Th>Sector</Th>
          <Th>Asset Class</Th>
          <Th>Currency</Th>
          <Th>Actions</Th>
        </tr>
      </thead>
      <tbody>
        {holdings.map((holding) => (
          <tr key={holding.id}>
            <Td className="font-semibold text-ink">{holding.symbol}</Td>
            <Td>{holding.company_name ?? "--"}</Td>
            <Td>{formatNumber(holding.quantity)}</Td>
            <Td>{formatCurrency(holding.average_cost, holding.currency)}</Td>
            <Td>{formatCurrency(holding.current_price, holding.currency)}</Td>
            <Td>{formatCurrency(holding.market_value, holding.currency)}</Td>
            <Td>
              <span className={holding.unrealized_gain_loss && holding.unrealized_gain_loss < 0 ? "text-coral" : "text-emerald-700"}>
                {formatCurrency(holding.unrealized_gain_loss, holding.currency)}
              </span>
            </Td>
            <Td>{holding.sector ?? "--"}</Td>
            <Td>{holding.asset_class ? <Badge>{holding.asset_class}</Badge> : "--"}</Td>
            <Td>{holding.currency}</Td>
            <Td>
              <div className="flex gap-2">
                <Button variant="secondary" className="h-8 px-2" onClick={() => onEdit(holding)} aria-label={`Edit ${holding.symbol}`}>
                  <Edit2 size={14} />
                </Button>
                <Button
                  variant="secondary"
                  className="h-8 px-2 text-coral"
                  onClick={() => onDelete(holding)}
                  disabled={isDeleting}
                  aria-label={`Delete ${holding.symbol}`}
                >
                  <Trash2 size={14} />
                </Button>
              </div>
            </Td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}

function HoldingForm({
  editingHolding,
  onCancelEdit,
  onSubmit,
  isSubmitting,
  errorMessage
}: {
  editingHolding: Holding | null;
  onCancelEdit: () => void;
  onSubmit: (input: HoldingCreateInput) => void;
  isSubmitting: boolean;
  errorMessage?: string;
}) {
  const form = useForm<HoldingFormValues>({
    resolver: zodResolver(holdingSchema),
    defaultValues: defaultHoldingValues
  });

  useEffect(() => {
    if (!editingHolding) {
      form.reset(defaultHoldingValues);
      return;
    }
    form.reset({
      symbol: editingHolding.symbol,
      company_name: editingHolding.company_name ?? "",
      quantity: String(editingHolding.quantity),
      average_cost: toInputValue(editingHolding.average_cost),
      current_price: toInputValue(editingHolding.current_price),
      currency: editingHolding.currency,
      sector: editingHolding.sector ?? "",
      asset_class: editingHolding.asset_class ?? "",
      exchange: editingHolding.exchange ?? ""
    });
  }, [editingHolding, form]);

  const submit = form.handleSubmit((values) => {
    onSubmit({
      symbol: values.symbol.toUpperCase(),
      company_name: emptyToNull(values.company_name),
      quantity: Number(values.quantity),
      average_cost: numberOrNull(values.average_cost),
      current_price: numberOrNull(values.current_price),
      currency: values.currency.toUpperCase(),
      sector: emptyToNull(values.sector),
      asset_class: emptyToNull(values.asset_class),
      exchange: emptyToNull(values.exchange)
    });
    if (!editingHolding) {
      form.reset(defaultHoldingValues);
    }
  });

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between gap-3">
        <CardTitle>{editingHolding ? `Edit ${editingHolding.symbol}` : "Add holding"}</CardTitle>
        {editingHolding ? (
          <Button variant="ghost" className="h-8 px-2" onClick={onCancelEdit}>
            <X size={15} />
            Cancel
          </Button>
        ) : null}
      </div>

      {errorMessage ? <ErrorState title="Holding request failed" detail={errorMessage} /> : null}

      <form className="mt-4 grid gap-4" onSubmit={submit}>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Symbol" error={form.formState.errors.symbol?.message}>
            <Input placeholder="AAPL" {...form.register("symbol")} />
          </Field>
          <Field label="Name" error={form.formState.errors.company_name?.message}>
            <Input placeholder="Apple Inc." {...form.register("company_name")} />
          </Field>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Quantity" error={form.formState.errors.quantity?.message}>
            <Input inputMode="decimal" placeholder="10" {...form.register("quantity")} />
          </Field>
          <Field label="Average Cost" error={form.formState.errors.average_cost?.message}>
            <Input inputMode="decimal" placeholder="100" {...form.register("average_cost")} />
          </Field>
          <Field label="Current Price" error={form.formState.errors.current_price?.message}>
            <Input inputMode="decimal" placeholder="125" {...form.register("current_price")} />
          </Field>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Sector" error={form.formState.errors.sector?.message}>
            <Input placeholder="Technology" {...form.register("sector")} />
          </Field>
          <Field label="Asset Class" error={form.formState.errors.asset_class?.message}>
            <Input placeholder="equity" {...form.register("asset_class")} />
          </Field>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Exchange" error={form.formState.errors.exchange?.message}>
            <Input placeholder="NASDAQ" {...form.register("exchange")} />
          </Field>
          <Field label="Currency" error={form.formState.errors.currency?.message}>
            <Input placeholder="USD" {...form.register("currency")} />
          </Field>
        </div>

        <Button type="submit" disabled={isSubmitting}>
          {editingHolding ? <Save size={16} /> : <Plus size={16} />}
          {isSubmitting ? "Saving" : editingHolding ? "Save changes" : "Add holding"}
        </Button>
      </form>
    </Card>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <label className="grid gap-2">
      <span className="text-sm font-medium text-ink">{label}</span>
      {children}
      {error ? <span className="text-xs text-coral">{error}</span> : null}
    </label>
  );
}

function emptyToNull(value: string | undefined) {
  const trimmed = value?.trim() ?? "";
  return trimmed ? trimmed : null;
}

function numberOrNull(value: string) {
  return value.trim() ? Number(value) : null;
}

function toInputValue(value: number | null) {
  return value === null ? "" : String(value);
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 4 }).format(value);
}

function formatCurrency(value: number | null, currency: string) {
  if (value === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2
  }).format(value);
}

function getLatestPriceUpdatedAt(holdings: Holding[]) {
  const timestamps = holdings
    .filter((holding) => holding.current_price !== null)
    .map((holding) => new Date(holding.updated_at).getTime())
    .filter((timestamp) => Number.isFinite(timestamp));
  if (!timestamps.length) {
    return null;
  }
  return new Date(Math.max(...timestamps)).toISOString();
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}
