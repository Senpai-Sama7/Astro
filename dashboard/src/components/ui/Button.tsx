"use client";

import { cn } from "@/utils/cn";
import { motion } from "framer-motion";
import { ReactNode } from "react";

interface ButtonProps {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost" | "danger" | "outline";
  size?: "sm" | "md" | "lg";
  icon?: ReactNode;
  loading?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
  type?: "button" | "submit" | "reset";
}

export function Button({
  children,
  className,
  variant = "primary",
  size = "md",
  icon,
  loading,
  disabled,
  onClick,
  type = "button",
}: ButtonProps) {
  const variants = {
    primary:
      "bg-[#0066ff] text-white border-2 border-[#0066ff] hover:bg-[#0052cc] hover:border-[#0052cc] active:bg-[#004099]",
    secondary:
      "bg-[#2a2a2a] text-[#fafafa] border-2 border-[#3a3a3a] hover:bg-[#3a3a3a] hover:border-[#4a4a4a]",
    ghost:
      "bg-transparent text-[#9a9a9a] border-2 border-transparent hover:text-[#fafafa] hover:bg-[#2a2a2a]",
    danger:
      "bg-[#ff2d2d] text-white border-2 border-[#ff2d2d] hover:bg-[#cc2424] hover:border-[#cc2424]",
    outline:
      "bg-transparent text-[#fafafa] border-2 border-[#3a3a3a] hover:border-[#6a6a6a] hover:bg-[#1a1a1a]",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };

  return (
    <motion.button
      type={type}
      whileTap={{ scale: 0.98 }}
      whileHover={{ scale: 1.02 }}
      className={cn(
        "relative inline-flex items-center justify-center gap-2 font-semibold uppercase tracking-wider transition-all duration-200",
        variants[variant],
        sizes[size],
        (disabled || loading) && "opacity-50 cursor-not-allowed pointer-events-none",
        className
      )}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading ? (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : icon ? (
        <span className="w-4 h-4">{icon}</span>
      ) : null}
      {children}
    </motion.button>
  );
}
