import { Plus, RefreshCw, Trash2 } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Button, Card, CardTitle, EmptyState, ErrorState, Input, LoadingState, Table, Td, Th } from "../components/ui";
import { useWatchlist } from "../hooks/useWatchlist";
import { getBatchPrices } from "../services/marketDataApi";
import type { WatchlistItem } from "../types/watchlist";

export function WatchlistPage() {
  const watchlist = useWatchlist();
  const [symbol, setSymbol] = useState("");
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const symbols = useMemo(() => (watchlist.data ?? []).map((item) => item.symbol), [watchlist.data]);
  const prices = useQuery({
    queryKey: ["watchlist", "prices", symbols],
    queryFn: () => getBatchPrices(symbols),
    enabled: symbols.length > 0
  });
  const priceBySymbol = useMemo(
    () => new Map((prices.data?.prices ?? []).map((price) => [price.symbol, price])),
    [prices.data]
  );

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedSymbol = symbol.trim().toUpperCase();
    if (!cleanedSymbol) {
      return;
    }
    watchlist.createItem.mutate(
      {
        symbol: cleanedSymbol,
        name: name.trim() || null,
        notes: notes.trim() || null
      },
      {
        onSuccess: () => {
          setSymbol("");
          setName("");
          setNotes("");
        }
      }
    );
  }

  return (
    <div className="space-y-6">
      <WatchlistHeader isRefreshing={prices.isFetching} onRefresh={() => void prices.refetch()} canRefresh={symbols.length > 0} />

      <Card>
        <CardTitle>Add symbol</CardTitle>
        <form className="mt-4 grid gap-4 lg:grid-cols-[0.5fr_1fr_1.4fr_auto]" onSubmit={handleSubmit}>
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Symbol</span>
            <Input placeholder="AAPL" value={symbol} onChange={(event) => setSymbol(event.target.value.toUpperCase())} />
          </label>
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Name</span>
            <Input placeholder="Apple Inc." value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Notes</span>
            <Input placeholder="Reason to monitor" value={notes} onChange={(event) => setNotes(event.target.value)} />
          </label>
          <Button type="submit" disabled={watchlist.createItem.isPending || !symbol.trim()} className="self-end">
            <Plus size={16} />
            {watchlist.createItem.isPending ? "Adding" : "Add"}
          </Button>
        </form>
        {watchlist.createItem.isError ? (
          <div className="mt-4">
            <ErrorState title="Unable to add symbol" detail={watchlist.createItem.error.message} />
          </div>
        ) : null}
      </Card>

      {watchlist.isLoading ? (
        <LoadingState label="Loading watchlist" />
      ) : watchlist.isError ? (
        <ErrorState title="Unable to load watchlist" detail={watchlist.error.message} />
      ) : !watchlist.data?.length ? (
        <EmptyState title="No watchlist symbols" detail="Add symbols you want to monitor outside current holdings." />
      ) : (
        <WatchlistTable
          items={watchlist.data}
          priceBySymbol={priceBySymbol}
          isDeleting={watchlist.deleteItem.isPending}
          onDelete={(item) => watchlist.deleteItem.mutate(item.id)}
        />
      )}
    </div>
  );
}

function WatchlistHeader({
  isRefreshing,
  canRefresh,
  onRefresh
}: {
  isRefreshing: boolean;
  canRefresh: boolean;
  onRefresh: () => void;
}) {
  return (
    <section className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Watchlist</p>
        <h1 className="mt-1 text-3xl font-semibold">Symbols to monitor</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Track names outside your portfolio while market data stays routed through backend APIs.
        </p>
      </div>
      <Button type="button" variant="secondary" onClick={onRefresh} disabled={!canRefresh || isRefreshing}>
        <RefreshCw className={isRefreshing ? "animate-spin" : ""} size={16} />
        {isRefreshing ? "Refreshing" : "Refresh prices"}
      </Button>
    </section>
  );
}

function WatchlistTable({
  items,
  priceBySymbol,
  isDeleting,
  onDelete
}: {
  items: WatchlistItem[];
  priceBySymbol: Map<string, { price: number; currency: string; source: string; as_of: string }>;
  isDeleting: boolean;
  onDelete: (item: WatchlistItem) => void;
}) {
  return (
    <Card>
      <CardTitle>Watchlist</CardTitle>
      <div className="mt-4">
        <Table>
          <thead>
            <tr>
              <Th>Symbol</Th>
              <Th>Name</Th>
              <Th>Price</Th>
              <Th>Source</Th>
              <Th>Notes</Th>
              <Th>Actions</Th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const quote = priceBySymbol.get(item.symbol);
              const price = quote?.price ?? item.current_price;
              const currency = quote?.currency ?? item.price_currency ?? "USD";
              return (
                <tr key={item.id}>
                  <Td className="font-semibold text-ink">{item.symbol}</Td>
                  <Td>{item.name ?? "N/A"}</Td>
                  <Td>{formatCurrency(price ?? null, currency)}</Td>
                  <Td>{quote?.source ?? item.price_source ?? "N/A"}</Td>
                  <Td>{item.notes ?? "N/A"}</Td>
                  <Td>
                    <Button
                      type="button"
                      variant="secondary"
                      className="h-8 px-2 text-coral"
                      disabled={isDeleting}
                      onClick={() => onDelete(item)}
                      aria-label={`Delete ${item.symbol}`}
                    >
                      <Trash2 size={14} />
                    </Button>
                  </Td>
                </tr>
              );
            })}
          </tbody>
        </Table>
      </div>
    </Card>
  );
}

function formatCurrency(value: number | null, currency: string) {
  if (value === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2
  }).format(value);
}
