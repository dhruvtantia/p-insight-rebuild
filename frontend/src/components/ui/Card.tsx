import type { HTMLAttributes, PropsWithChildren } from "react";

import { cn } from "../../lib/cn";

export function Card({ children, className, ...props }: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div className={cn("rounded-md border border-line bg-white p-5 shadow-soft", className)} {...props}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className, ...props }: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div className={cn("mb-4 flex items-start justify-between gap-4", className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className, ...props }: PropsWithChildren<HTMLAttributes<HTMLHeadingElement>>) {
  return (
    <h3 className={cn("text-base font-semibold text-ink", className)} {...props}>
      {children}
    </h3>
  );
}
