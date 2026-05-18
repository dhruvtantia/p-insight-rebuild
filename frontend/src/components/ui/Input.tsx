import type { InputHTMLAttributes } from "react";

import { cn } from "../../lib/cn";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-md border border-line bg-white px-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-accent focus:ring-2 focus:ring-accent/15",
        className
      )}
      {...props}
    />
  );
}
