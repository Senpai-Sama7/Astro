"use client";

import { cn } from "@/utils/cn";
import { motion } from "framer-motion";

interface StatusIndicatorProps {
  status: "online" | "offline" | "warning" | "processing";
  label?: string;
  size?: "sm" | "md" | "lg";
  showPulse?: boolean;
  className?: string;
}

export function StatusIndicator({
  status,
  label,
  size = "md",
  showPulse = true,
  className,
}: StatusIndicatorProps) {
  const statusColors = {
    online: "#00d26a",
    offline: "#ff2d2d",
    warning: "#ffd700",
    processing: "#0066ff",
  };

  const statusLabels = {
    online: "Online",
    offline: "Offline",
    warning: "Warning",
    processing: "Processing",
  };

  const sizes = {
    sm: { dot: "w-2 h-2", text: "text-xs" },
    md: { dot: "w-3 h-3", text: "text-sm" },
    lg: { dot: "w-4 h-4", text: "text-base" },
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="relative">
        {showPulse && status !== "offline" && (
          <motion.div
            className={cn("absolute inset-0 rounded-full", sizes[size].dot)}
            style={{ backgroundColor: statusColors[status] }}
            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          />
        )}
        <div
          className={cn("rounded-full relative z-10", sizes[size].dot)}
          style={{ backgroundColor: statusColors[status] }}
        />
      </div>
      {label !== undefined && (
        <span
          className={cn("font-medium", sizes[size].text)}
          style={{ color: statusColors[status] }}
        >
          {label ?? statusLabels[status]}
        </span>
      )}
    </div>
  );
}

interface SystemStatusProps {
  systems: Array<{
    name: string;
    status: "online" | "offline" | "warning" | "processing";
    uptime?: string;
  }>;
  className?: string;
}

export function SystemStatus({ systems, className }: SystemStatusProps) {
  return (
    <div className={cn("space-y-3", className)}>
      {systems.map((system, index) => (
        <motion.div
          key={system.name}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3, delay: index * 0.05 }}
          className="flex items-center justify-between p-3 bg-[#1a1a1a] border border-[#2a2a2a] hover:border-[#3a3a3a] transition-colors"
        >
          <div className="flex items-center gap-3">
            <StatusIndicator status={system.status} size="sm" showPulse />
            <span className="text-sm font-medium text-[#fafafa]">{system.name}</span>
          </div>
          {system.uptime && (
            <span className="text-xs font-mono text-[#6a6a6a]">{system.uptime}</span>
          )}
        </motion.div>
      ))}
    </div>
  );
}
