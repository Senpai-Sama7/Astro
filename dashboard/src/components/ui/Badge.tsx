"use client";

import { cn } from "@/utils/cn";
import { ReactNode } from "react";

interface BadgeProps {
  children: ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "info" | "outline";
  size?: "sm" | "md";
  pulse?: boolean;
  className?: string;
}

export function Badge({
  children,
  variant = "default",
  size = "sm",
  pulse = false,
  className,
}: BadgeProps) {
  const variants = {
    default: "bg-[#2a2a2a] text-[#9a9a9a] border-[#3a3a3a]",
    success: "bg-[#00d26a]/10 text-[#00d26a] border-[#00d26a]/30",
    warning: "bg-[#ffd700]/10 text-[#ffd700] border-[#ffd700]/30",
    danger: "bg-[#ff2d2d]/10 text-[#ff2d2d] border-[#ff2d2d]/30",
    info: "bg-[#0066ff]/10 text-[#0066ff] border-[#0066ff]/30",
    outline: "bg-transparent text-[#9a9a9a] border-[#3a3a3a]",
  };

  const sizes = {
    sm: "px-2 py-0.5 text-[10px]",
    md: "px-3 py-1 text-xs",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 font-semibold uppercase tracking-wider border",
        variants[variant],
        sizes[size],
        className
      )}
    >
      {pulse && (
        <span className="relative flex h-2 w-2">
          <span
            className={cn(
              "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
              variant === "success" && "bg-[#00d26a]",
              variant === "warning" && "bg-[#ffd700]",
              variant === "danger" && "bg-[#ff2d2d]",
              variant === "info" && "bg-[#0066ff]",
              variant === "default" && "bg-[#6a6a6a]"
            )}
          />
          <span
            className={cn(
              "relative inline-flex rounded-full h-2 w-2",
              variant === "success" && "bg-[#00d26a]",
              variant === "warning" && "bg-[#ffd700]",
              variant === "danger" && "bg-[#ff2d2d]",
              variant === "info" && "bg-[#0066ff]",
              variant === "default" && "bg-[#6a6a6a]"
            )}
          />
        </span>
      )}
      {children}
    </span>
  );
}
