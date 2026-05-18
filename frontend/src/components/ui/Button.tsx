import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

import { cn } from "../../lib/cn";

type ButtonProps = PropsWithChildren<ButtonHTMLAttributes<HTMLButtonElement>> & {
  variant?: "primary" | "secondary" | "ghost";
};

export function Button({ children, className, variant = "primary", ...props }: ButtonProps) {
  const variants = {
    primary: "bg-accent text-white hover:bg-[#135c61]",
    secondary: "border border-line bg-white text-ink hover:bg-surface",
    ghost: "text-ink hover:bg-white"
  };

  return (
    <button
      className={cn(
        "inline-flex h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
