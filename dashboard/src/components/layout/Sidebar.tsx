"use client";

import { cn } from "@/utils/cn";
import { motion } from "framer-motion";
import { ReactNode, useState } from "react";
import {
  LayoutDashboard,
  Activity,
  Bot,
  Settings,
  Terminal,
  Database,
  Shield,
  LineChart,
  ChevronLeft,
  ChevronRight,
  Zap,
} from "lucide-react";

interface NavItem {
  id: string;
  label: string;
  icon: ReactNode;
  badge?: number;
  active?: boolean;
}

interface SidebarProps {
  activeItem?: string;
  onItemClick?: (id: string) => void;
  collapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
  className?: string;
}

const navItems: NavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: <LayoutDashboard className="w-5 h-5" /> },
  { id: "agents", label: "Agents", icon: <Bot className="w-5 h-5" />, badge: 4 },
  { id: "activity", label: "Activity", icon: <Activity className="w-5 h-5" /> },
  { id: "analytics", label: "Analytics", icon: <LineChart className="w-5 h-5" /> },
  { id: "terminal", label: "Terminal", icon: <Terminal className="w-5 h-5" /> },
  { id: "database", label: "Database", icon: <Database className="w-5 h-5" /> },
  { id: "security", label: "Security", icon: <Shield className="w-5 h-5" /> },
  { id: "settings", label: "Settings", icon: <Settings className="w-5 h-5" /> },
];

export function Sidebar({
  activeItem = "dashboard",
  onItemClick,
  collapsed = false,
  onCollapsedChange,
  className,
}: SidebarProps) {
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 72 : 240 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "fixed left-0 top-0 h-screen bg-[#0f0f0f] border-r border-[#1a1a1a] flex flex-col z-50",
        className
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-[#1a1a1a]">
        <motion.div
          className="flex items-center gap-3"
          animate={{ opacity: 1 }}
        >
          <div className="w-8 h-8 bg-[#0066ff] flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              className="font-bold text-lg tracking-tight text-[#fafafa] whitespace-nowrap"
            >
              ASTRO
            </motion.span>
          )}
        </motion.div>
        <button
          onClick={() => onCollapsedChange?.(!collapsed)}
          className="p-1.5 text-[#6a6a6a] hover:text-[#fafafa] hover:bg-[#1a1a1a] transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto">
        <ul className="space-y-1 px-3">
          {navItems.map((item) => {
            const isActive = activeItem === item.id;
            const isHovered = hoveredItem === item.id;

            return (
              <li key={item.id}>
                <button
                  onClick={() => onItemClick?.(item.id)}
                  onMouseEnter={() => setHoveredItem(item.id)}
                  onMouseLeave={() => setHoveredItem(null)}
                  className={cn(
                    "relative w-full flex items-center gap-3 px-3 py-2.5 transition-all duration-200 group",
                    isActive
                      ? "text-[#fafafa] bg-[#1a1a1a]"
                      : "text-[#6a6a6a] hover:text-[#fafafa] hover:bg-[#151515]"
                  )}
                >
                  {/* Active indicator */}
                  {isActive && (
                    <motion.div
                      layoutId="activeIndicator"
                      className="absolute left-0 top-0 bottom-0 w-[2px] bg-[#0066ff]"
                      transition={{ duration: 0.2 }}
                    />
                  )}

                  {/* Icon */}
                  <span className={cn(isActive && "text-[#0066ff]")}>{item.icon}</span>

                  {/* Label */}
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-sm font-medium flex-1 text-left"
                    >
                      {item.label}
                    </motion.span>
                  )}

                  {/* Badge */}
                  {!collapsed && item.badge && (
                    <span className="px-1.5 py-0.5 text-[10px] font-bold bg-[#0066ff] text-white">
                      {item.badge}
                    </span>
                  )}

                  {/* Tooltip for collapsed state */}
                  {collapsed && isHovered && (
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="absolute left-full ml-2 px-3 py-1.5 bg-[#1a1a1a] border border-[#2a2a2a] text-sm text-[#fafafa] whitespace-nowrap z-50"
                    >
                      {item.label}
                      {item.badge && (
                        <span className="ml-2 px-1.5 py-0.5 text-[10px] font-bold bg-[#0066ff] text-white">
                          {item.badge}
                        </span>
                      )}
                    </motion.div>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-[#1a1a1a]">
        <div
          className={cn(
            "flex items-center gap-3 p-3 bg-[#1a1a1a] border border-[#2a2a2a]",
            collapsed && "justify-center"
          )}
        >
          <div className="w-8 h-8 bg-[#2a2a2a] flex items-center justify-center text-[#fafafa] text-sm font-bold">
            A
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[#fafafa] truncate">Admin</p>
              <p className="text-xs text-[#6a6a6a] truncate">System Operator</p>
            </div>
          )}
        </div>
      </div>
    </motion.aside>
  );
}
