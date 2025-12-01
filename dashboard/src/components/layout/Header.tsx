"use client";

import { cn } from "@/utils/cn";
import { motion } from "framer-motion";
import {
  Bell,
  Search,
  Command,
  Clock,
} from "lucide-react";
import { useEffect, useState } from "react";
import { StatusIndicator } from "../dashboard/StatusIndicator";

interface HeaderProps {
  title?: string;
  subtitle?: string;
  className?: string;
  onSearchClick?: () => void;
  onNotificationsClick?: () => void;
  notificationCount?: number;
}

export function Header({ 
  title = "Dashboard", 
  subtitle, 
  className,
  onSearchClick,
  onNotificationsClick,
  notificationCount = 0,
}: HeaderProps) {
  const [currentTime, setCurrentTime] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header
      className={cn(
        "h-16 bg-[#0a0a0a]/80 backdrop-blur-xl border-b border-[#1a1a1a] flex items-center justify-between px-6 sticky top-0 z-40",
        className
      )}
    >
      {/* Left: Title */}
      <div className="flex items-center gap-4">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <h1 className="text-xl font-bold text-[#fafafa]">{title}</h1>
          {subtitle && (
            <p className="text-xs text-[#6a6a6a] mt-0.5">{subtitle}</p>
          )}
        </motion.div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-4">
        {/* System Status */}
        <div className="hidden md:flex items-center gap-3 px-4 py-2 bg-[#1a1a1a] border border-[#2a2a2a]">
          <StatusIndicator status="online" size="sm" />
          <span className="text-xs font-medium text-[#9a9a9a]">All Systems Operational</span>
        </div>

        {/* Time */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-2 bg-[#1a1a1a] border border-[#2a2a2a] font-mono">
          <Clock className="w-4 h-4 text-[#6a6a6a]" />
          <span className="text-sm text-[#fafafa]">{currentTime}</span>
        </div>

        {/* Search */}
        <button 
          onClick={onSearchClick}
          className="flex items-center gap-2 px-3 py-2 bg-[#1a1a1a] border border-[#2a2a2a] hover:border-[#3a3a3a] hover:bg-[#1f1f1f] transition-colors group"
        >
          <Search className="w-4 h-4 text-[#6a6a6a] group-hover:text-[#9a9a9a]" />
          <span className="hidden sm:inline text-sm text-[#6a6a6a] group-hover:text-[#9a9a9a]">Search</span>
          <div className="hidden sm:flex items-center gap-1 ml-2 px-1.5 py-0.5 bg-[#2a2a2a] text-[10px] text-[#6a6a6a]">
            <Command className="w-3 h-3" />K
          </div>
        </button>

        {/* Notifications */}
        <button 
          onClick={onNotificationsClick}
          className="relative p-2 bg-[#1a1a1a] border border-[#2a2a2a] hover:border-[#3a3a3a] hover:bg-[#1f1f1f] transition-colors group"
        >
          <Bell className="w-5 h-5 text-[#6a6a6a] group-hover:text-[#fafafa]" />
          {notificationCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-[#ff2d2d] text-white text-[10px] font-bold flex items-center justify-center">
              {notificationCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
