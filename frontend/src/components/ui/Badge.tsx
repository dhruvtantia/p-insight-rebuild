import type { HTMLAttributes, PropsWithChildren } from "react";

import { cn } from "../../lib/cn";

type BadgeProps = PropsWithChildren<HTMLAttributes<HTMLSpanElement>> & {
  tone?: "neutral" | "success" | "warning" | "danger";
};

export function Badge({ children, className, tone = "neutral", ...props }: BadgeProps) {
  const tones = {
    neutral: "bg-slate-100 text-slate-700",
    success: "bg-emerald-50 text-emerald-700",
    warning: "bg-amber-50 text-amber-700",
    danger: "bg-red-50 text-red-700"
  };

  return (
    <span
      className={cn("inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold", tones[tone], className)}
      {...props}
    >
      {children}
    </span>
  );
}
