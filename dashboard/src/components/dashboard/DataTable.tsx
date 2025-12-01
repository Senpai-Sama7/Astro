"use client";

import { cn } from "@/utils/cn";
import { motion } from "framer-motion";
import { ReactNode } from "react";

interface Column<T> {
  key: keyof T | string;
  header: string;
  width?: string;
  align?: "left" | "center" | "right";
  render?: (value: unknown, row: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  onRowClick?: (row: T) => void;
  loading?: boolean;
  emptyMessage?: string;
  className?: string;
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  onRowClick,
  loading,
  emptyMessage = "No data available",
  className,
}: DataTableProps<T>) {
  const getNestedValue = (obj: T, path: string): unknown => {
    return path.split(".").reduce((acc: unknown, part) => {
      if (acc && typeof acc === "object" && part in acc) {
        return (acc as Record<string, unknown>)[part];
      }
      return undefined;
    }, obj);
  };

  return (
    <div className={cn("w-full overflow-x-auto", className)}>
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-[#2a2a2a]">
            {columns.map((column) => (
              <th
                key={String(column.key)}
                className={cn(
                  "px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[#6a6a6a] bg-[#151515]",
                  column.align === "center" && "text-center",
                  column.align === "right" && "text-right",
                  !column.align && "text-left"
                )}
                style={{ width: column.width }}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <tr key={i} className="border-b border-[#1a1a1a]">
                {columns.map((column) => (
                  <td key={String(column.key)} className="px-4 py-4">
                    <div className="h-4 bg-[#2a2a2a] animate-pulse w-3/4" />
                  </td>
                ))}
              </tr>
            ))
          ) : data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-12 text-center text-sm text-[#6a6a6a]"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <motion.tr
                key={rowIndex}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.2, delay: rowIndex * 0.03 }}
                onClick={() => onRowClick?.(row)}
                className={cn(
                  "border-b border-[#1a1a1a] transition-colors",
                  onRowClick && "cursor-pointer hover:bg-[#1a1a1a]"
                )}
              >
                {columns.map((column) => {
                  const value = getNestedValue(row, String(column.key));
                  return (
                    <td
                      key={String(column.key)}
                      className={cn(
                        "px-4 py-4 text-sm text-[#e8e8e8]",
                        column.align === "center" && "text-center",
                        column.align === "right" && "text-right"
                      )}
                    >
                      {column.render ? column.render(value, row) : String(value ?? "")}
                    </td>
                  );
                })}
              </motion.tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
