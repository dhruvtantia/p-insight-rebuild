import { AlertTriangle, Inbox, Loader2, Lock } from "lucide-react";

import { Card } from "./Card";

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <Card className="flex items-center gap-3 text-sm text-slate-600">
      <Loader2 className="animate-spin text-accent" size={18} />
      {label}
    </Card>
  );
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <Card className="border-dashed">
      <div className="flex items-start gap-3">
        <Inbox className="mt-0.5 text-slate-400" size={20} />
        <div>
          <h3 className="text-sm font-semibold text-ink">{title}</h3>
          <p className="mt-1 text-sm text-slate-600">{detail}</p>
        </div>
      </div>
    </Card>
  );
}

export function ErrorState({ title = "Something went wrong", detail }: { title?: string; detail?: string }) {
  return (
    <Card className="border-coral/30 bg-[#fff8f6]">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 text-coral" size={20} />
        <div>
          <h3 className="text-sm font-semibold text-coral">{title}</h3>
          <p className="mt-1 text-sm text-coral/80">{detail ?? "The request could not be completed."}</p>
        </div>
      </div>
    </Card>
  );
}

export function FeatureDisabledState({ feature, detail }: { feature: string; detail?: string }) {
  return (
    <Card className="border-dashed bg-white">
      <div className="flex items-start gap-3">
        <Lock className="mt-0.5 text-slate-400" size={20} />
        <div>
          <h3 className="text-sm font-semibold text-ink">{feature} is not enabled</h3>
          <p className="mt-1 text-sm text-slate-600">
            {detail ?? "This module is available behind a backend feature flag and is not active in this environment."}
          </p>
        </div>
      </div>
    </Card>
  );
}
