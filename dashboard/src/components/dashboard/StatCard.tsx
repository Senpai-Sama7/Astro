"use client";

import { cn } from "@/utils/cn";
import { motion } from "framer-motion";
import { ReactNode } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: number;
  changeLabel?: string;
  icon?: ReactNode;
  trend?: "up" | "down" | "neutral";
  variant?: "default" | "accent" | "success" | "warning" | "danger";
  size?: "sm" | "md" | "lg";
  delay?: number;
  className?: string;
}

export function StatCard({
  title,
  value,
  subtitle,
  change,
  changeLabel,
  icon,
  trend,
  variant = "default",
  size = "md",
  delay = 0,
  className,
}: StatCardProps) {
  const variants = {
    default: "border-[#2a2a2a]",
    accent: "border-[#0066ff]",
    success: "border-[#00d26a]",
    warning: "border-[#ffd700]",
    danger: "border-[#ff2d2d]",
  };

  const accentColors = {
    default: "#6a6a6a",
    accent: "#0066ff",
    success: "#00d26a",
    warning: "#ffd700",
    danger: "#ff2d2d",
  };

  const sizes = {
    sm: { padding: "p-4", title: "text-xs", value: "text-2xl" },
    md: { padding: "p-6", title: "text-xs", value: "text-3xl" },
    lg: { padding: "p-8", title: "text-sm", value: "text-4xl" },
  };

  const getTrendIcon = () => {
    if (trend === "up") return <TrendingUp className="w-4 h-4" />;
    if (trend === "down") return <TrendingDown className="w-4 h-4" />;
    return <Minus className="w-4 h-4" />;
  };

  const getTrendColor = () => {
    if (trend === "up") return "text-[#00d26a]";
    if (trend === "down") return "text-[#ff2d2d]";
    return "text-[#6a6a6a]";
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "relative bg-[#1a1a1a] border overflow-hidden group transition-all duration-300 hover:border-[#4a4a4a]",
        variants[variant],
        sizes[size].padding,
        className
      )}
    >
      {/* Accent line */}
      <div
        className="absolute top-0 left-0 right-0 h-[2px]"
        style={{ backgroundColor: accentColors[variant] }}
      />

      {/* Content */}
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <span
            className={cn(
              "uppercase tracking-wider font-semibold text-[#6a6a6a]",
              sizes[size].title
            )}
          >
            {title}
          </span>
          {icon && (
            <div
              className="p-2 bg-[#2a2a2a] text-[#9a9a9a] group-hover:bg-[#3a3a3a] transition-colors"
              style={{ color: accentColors[variant] }}
            >
              {icon}
            </div>
          )}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: delay + 0.2 }}
        >
          <span
            className={cn(
              "font-bold text-[#fafafa] font-mono block",
              sizes[size].value
            )}
          >
            {value}
          </span>
        </motion.div>

        {(subtitle || change !== undefined) && (
          <div className="mt-3 flex items-center gap-3">
            {change !== undefined && (
              <span className={cn("flex items-center gap-1 text-sm font-medium", getTrendColor())}>
                {getTrendIcon()}
                {Math.abs(change)}%
              </span>
            )}
            {(subtitle || changeLabel) && (
              <span className="text-xs text-[#6a6a6a]">
                {subtitle || changeLabel}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Hover glow */}
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
        style={{
          background: `radial-gradient(circle at 50% 0%, ${accentColors[variant]}15, transparent 70%)`,
        }}
      />
    </motion.div>
  );
}
