import { Building2, CheckCircle2, Trash2, Upload } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge, Button, Card, CardTitle, EmptyState, ErrorState, LoadingState, Table, Td, Th } from "../components/ui";
import { useBrokerConnections } from "../hooks/useBrokerConnections";

export function BrokerConnectionsPage() {
  const brokers = useBrokerConnections();

  return (
    <div className="space-y-6">
      <BrokerHeader />

      <Card>
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle>Upload now, broker sync later</CardTitle>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Manual upload is the supported MVP import path. Broker connections are placeholders so beta users can mark interest without starting real broker auth.
            </p>
          </div>
          <Link to="/upload">
            <Button>
              <Upload size={16} />
              Upload holdings
            </Button>
          </Link>
        </div>
      </Card>

      {brokers.isLoading ? (
        <LoadingState label="Loading broker placeholders" />
      ) : brokers.isError ? (
        <ErrorState title="Unable to load broker placeholders" detail={brokers.error?.message} />
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {(brokers.providers.data ?? []).map((provider) => (
              <Card key={provider.provider}>
                <div className="flex items-start justify-between gap-3">
                  <Building2 className="text-accent" size={24} />
                  <Badge>{provider.status.replace("_", " ")}</Badge>
                </div>
                <h3 className="mt-4 text-lg font-semibold text-ink">{provider.display_name}</h3>
                <p className="mt-2 min-h-20 text-sm leading-6 text-slate-600">{provider.message}</p>
                <Button
                  type="button"
                  variant="secondary"
                  className="mt-4 w-full"
                  disabled={brokers.createPlaceholder.isPending}
                  onClick={() => brokers.createPlaceholder.mutate(provider.display_name)}
                >
                  <CheckCircle2 size={16} />
                  Mark interest
                </Button>
              </Card>
            ))}
          </div>

          {brokers.createPlaceholder.isError ? (
            <ErrorState title="Unable to mark interest" detail={brokers.createPlaceholder.error.message} />
          ) : null}

          <ConnectionInterestTable
            connections={brokers.connections.data ?? []}
            isDeleting={brokers.deleteConnection.isPending}
            onDelete={(connectionId) => brokers.deleteConnection.mutate(connectionId)}
          />
        </>
      )}
    </div>
  );
}

function BrokerHeader() {
  return (
    <section>
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Broker connections</p>
      <h1 className="mt-1 text-3xl font-semibold">Broker sync placeholders</h1>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
        Plaid, Zerodha, IBKR, and Alpaca support are planned. No real broker authorization runs in this MVP.
      </p>
    </section>
  );
}

function ConnectionInterestTable({
  connections,
  isDeleting,
  onDelete
}: {
  connections: Array<{ id: string; provider: string; status: string; message: string; created_at: string }>;
  isDeleting: boolean;
  onDelete: (connectionId: string) => void;
}) {
  if (!connections.length) {
    return <EmptyState title="No broker interest yet" detail="Mark interest on a provider to help prioritize future broker sync work." />;
  }

  return (
    <Card>
      <CardTitle>Marked interest</CardTitle>
      <div className="mt-4">
        <Table>
          <thead>
            <tr>
              <Th>Provider</Th>
              <Th>Status</Th>
              <Th>Message</Th>
              <Th>Created</Th>
              <Th>Actions</Th>
            </tr>
          </thead>
          <tbody>
            {connections.map((connection) => (
              <tr key={connection.id}>
                <Td className="font-semibold text-ink">{connection.provider}</Td>
                <Td>{connection.status}</Td>
                <Td>{connection.message}</Td>
                <Td>{formatDate(connection.created_at)}</Td>
                <Td>
                  <Button
                    type="button"
                    variant="secondary"
                    className="h-8 px-2 text-coral"
                    disabled={isDeleting}
                    onClick={() => onDelete(connection.id)}
                    aria-label={`Remove ${connection.provider} interest`}
                  >
                    <Trash2 size={14} />
                  </Button>
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    </Card>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}
