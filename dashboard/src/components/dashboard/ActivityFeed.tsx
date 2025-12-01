"use client";

import { cn } from "@/utils/cn";
import { motion } from "framer-motion";
import { ReactNode } from "react";

interface ActivityItem {
  id: string;
  title: string;
  description?: string;
  timestamp: string;
  type: "success" | "warning" | "error" | "info" | "default";
  icon?: ReactNode;
}

interface ActivityFeedProps {
  items: ActivityItem[];
  maxItems?: number;
  className?: string;
}

export function ActivityFeed({ items, maxItems = 5, className }: ActivityFeedProps) {
  const displayItems = items.slice(0, maxItems);

  const typeColors = {
    success: "#00d26a",
    warning: "#ffd700",
    error: "#ff2d2d",
    info: "#0066ff",
    default: "#6a6a6a",
  };

  return (
    <div className={cn("space-y-0", className)}>
      {displayItems.map((item, index) => (
        <motion.div
          key={item.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: index * 0.05 }}
          className="relative pl-6 pb-6 last:pb-0 group"
        >
          {/* Timeline line */}
          {index < displayItems.length - 1 && (
            <div className="absolute left-[5px] top-3 bottom-0 w-[1px] bg-[#2a2a2a]" />
          )}

          {/* Timeline dot */}
          <div
            className="absolute left-0 top-1.5 w-[11px] h-[11px] border-2 bg-[#1a1a1a] transition-transform group-hover:scale-125"
            style={{ borderColor: typeColors[item.type] }}
          />

          {/* Content */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                {item.icon && (
                  <span style={{ color: typeColors[item.type] }}>{item.icon}</span>
                )}
                <span className="text-sm font-medium text-[#fafafa] truncate">
                  {item.title}
                </span>
              </div>
              {item.description && (
                <p className="mt-1 text-xs text-[#6a6a6a] line-clamp-2">
                  {item.description}
                </p>
              )}
            </div>
            <span className="text-[10px] text-[#6a6a6a] font-mono whitespace-nowrap">
              {item.timestamp}
            </span>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
