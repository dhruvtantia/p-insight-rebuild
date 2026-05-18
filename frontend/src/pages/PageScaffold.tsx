import { Badge, Card, CardHeader, CardTitle, EmptyState, ErrorState, LoadingState } from "../components/ui";

type PageScaffoldProps = {
  title: string;
  eyebrow?: string;
  description: string;
  status?: "ready" | "coming-soon";
  relevantStates?: boolean;
};

export function PageScaffold({
  title,
  eyebrow = "MVP placeholder",
  description,
  status = "ready",
  relevantStates = true
}: PageScaffoldProps) {
  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">{eyebrow}</p>
          <h1 className="mt-1 text-3xl font-semibold text-ink">{title}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">{description}</p>
        </div>
        <Badge tone={status === "coming-soon" ? "warning" : "success"}>
          {status === "coming-soon" ? "Coming soon" : "Ready for implementation"}
        </Badge>
      </section>

      {relevantStates ? (
        <div className="grid gap-4 lg:grid-cols-3">
          <LoadingState label={`${title} loading state`} />
          <EmptyState title="No data yet" detail="This page will render its first useful state after backend data is available." />
          <ErrorState title="Error state" detail="API and validation errors will use this shared surface." />
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Implementation notes</CardTitle>
            <p className="mt-1 text-sm text-slate-600">
              This page is wired into navigation and ready for feature work in a later phase.
            </p>
          </div>
        </CardHeader>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="h-20 rounded-md bg-surface" />
          <div className="h-20 rounded-md bg-surface" />
          <div className="h-20 rounded-md bg-surface" />
        </div>
      </Card>
    </div>
  );
}
