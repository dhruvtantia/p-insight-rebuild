import { AlertTriangle } from "lucide-react";

export function DemoDataBanner() {
  return (
    <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 shrink-0" size={17} />
        <span>Demo data: prices are simulated and not suitable for investment decisions.</span>
      </div>
    </div>
  );
}
