"use client";

import { cn } from "@/utils/cn";
import { motion } from "framer-motion";

interface ProgressProps {
  value: number;
  max?: number;
  variant?: "default" | "success" | "warning" | "danger" | "gradient";
  size?: "sm" | "md" | "lg";
  showValue?: boolean;
  animate?: boolean;
  className?: string;
}

export function Progress({
  value,
  max = 100,
  variant = "default",
  size = "md",
  showValue = false,
  animate = true,
  className,
}: ProgressProps) {
  const percentage = Math.min((value / max) * 100, 100);

  const variants = {
    default: "bg-[#0066ff]",
    success: "bg-[#00d26a]",
    warning: "bg-[#ffd700]",
    danger: "bg-[#ff2d2d]",
    gradient: "bg-gradient-to-r from-[#0066ff] via-[#a855f7] to-[#ff2d2d]",
  };

  const sizes = {
    sm: "h-1",
    md: "h-2",
    lg: "h-3",
  };

  return (
    <div className={cn("w-full", className)}>
      <div
        className={cn(
          "w-full bg-[#2a2a2a] overflow-hidden",
          sizes[size]
        )}
      >
        <motion.div
          className={cn("h-full", variants[variant])}
          initial={animate ? { width: 0 } : { width: `${percentage}%` }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>
      {showValue && (
        <div className="mt-1 text-right">
          <span className="text-xs font-mono text-[#6a6a6a]">
            {value.toFixed(0)}/{max}
          </span>
        </div>
      )}
    </div>
  );
}

interface CircularProgressProps {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  variant?: "default" | "success" | "warning" | "danger";
  showValue?: boolean;
  label?: string;
  className?: string;
}

export function CircularProgress({
  value,
  max = 100,
  size = 120,
  strokeWidth = 8,
  variant = "default",
  showValue = true,
  label,
  className,
}: CircularProgressProps) {
  const percentage = Math.min((value / max) * 100, 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  const colors = {
    default: "#0066ff",
    success: "#00d26a",
    warning: "#ffd700",
    danger: "#ff2d2d",
  };

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#2a2a2a"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colors[variant]}
          strokeWidth={strokeWidth}
          strokeLinecap="square"
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: [0.16, 1, 0.3, 1] }}
          style={{
            strokeDasharray: circumference,
          }}
        />
      </svg>
      {showValue && (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className="text-2xl font-bold text-[#fafafa] font-mono"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5, duration: 0.3 }}
          >
            {percentage.toFixed(0)}%
          </motion.span>
          {label && (
            <span className="text-[10px] uppercase tracking-wider text-[#6a6a6a] mt-1">
              {label}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
