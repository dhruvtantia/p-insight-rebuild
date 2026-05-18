import type { HTMLAttributes, PropsWithChildren, TableHTMLAttributes } from "react";

import { cn } from "../../lib/cn";

export function Table({ children, className, ...props }: PropsWithChildren<TableHTMLAttributes<HTMLTableElement>>) {
  return (
    <div className="overflow-hidden rounded-md border border-line bg-white">
      <table className={cn("w-full border-collapse text-left text-sm", className)} {...props}>
        {children}
      </table>
    </div>
  );
}

export function Th({ children, className, ...props }: PropsWithChildren<HTMLAttributes<HTMLTableCellElement>>) {
  return (
    <th className={cn("border-b border-line bg-surface px-4 py-3 font-semibold text-slate-700", className)} {...props}>
      {children}
    </th>
  );
}

export function Td({ children, className, ...props }: PropsWithChildren<HTMLAttributes<HTMLTableCellElement>>) {
  return (
    <td className={cn("border-b border-line px-4 py-3 text-slate-700 last:border-b-0", className)} {...props}>
      {children}
    </td>
  );
}
