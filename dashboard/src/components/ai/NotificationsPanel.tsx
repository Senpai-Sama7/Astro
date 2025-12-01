"use client";

import { cn } from "@/utils/cn";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Bell,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  Info,
  Trash2,
  CheckCheck,
} from "lucide-react";

interface Notification {
  id: string;
  title: string;
  message: string;
  type: "success" | "error" | "warning" | "info";
  timestamp: Date;
  read: boolean;
}

interface NotificationsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  notifications: Notification[];
  onMarkRead: (id: string) => void;
  onMarkAllRead: () => void;
  onDelete: (id: string) => void;
}

export function NotificationsPanel({
  isOpen,
  onClose,
  notifications,
  onMarkRead,
  onMarkAllRead,
  onDelete,
}: NotificationsPanelProps) {
  const unreadCount = notifications.filter((n) => !n.read).length;

  const getIcon = (type: Notification["type"]) => {
    switch (type) {
      case "success":
        return <CheckCircle className="w-4 h-4 text-[#00d26a]" />;
      case "error":
        return <AlertCircle className="w-4 h-4 text-[#ff2d2d]" />;
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-[#ffd700]" />;
      case "info":
        return <Info className="w-4 h-4 text-[#0066ff]" />;
    }
  };

  const getTypeColor = (type: Notification["type"]) => {
    switch (type) {
      case "success":
        return "border-l-[#00d26a]";
      case "error":
        return "border-l-[#ff2d2d]";
      case "warning":
        return "border-l-[#ffd700]";
      case "info":
        return "border-l-[#0066ff]";
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[90]"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            initial={{ opacity: 0, x: 20, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 20, scale: 0.95 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="fixed top-16 right-4 w-[400px] max-h-[600px] bg-[#0f0f0f] border border-[#2a2a2a] shadow-2xl shadow-black/50 z-[100] flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-[#1a1a1a]">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-[#6a6a6a]" />
                <span className="text-sm font-semibold text-[#fafafa]">Notifications</span>
                {unreadCount > 0 && (
                  <span className="px-1.5 py-0.5 bg-[#0066ff] text-white text-[10px] font-bold">
                    {unreadCount}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <button
                    onClick={onMarkAllRead}
                    className="p-1.5 text-[#6a6a6a] hover:text-[#fafafa] hover:bg-[#1a1a1a] transition-colors"
                    title="Mark all as read"
                  >
                    <CheckCheck className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={onClose}
                  className="p-1.5 text-[#6a6a6a] hover:text-[#fafafa] hover:bg-[#1a1a1a] transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Notifications List */}
            <div className="flex-1 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="px-4 py-12 text-center">
                  <Bell className="w-8 h-8 text-[#2a2a2a] mx-auto mb-3" />
                  <p className="text-sm text-[#6a6a6a]">No notifications</p>
                  <p className="text-xs text-[#4a4a4a] mt-1">You're all caught up!</p>
                </div>
              ) : (
                <div>
                  {notifications.map((notification, index) => (
                    <motion.div
                      key={notification.id}
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      onClick={() => onMarkRead(notification.id)}
                      className={cn(
                        "px-4 py-3 border-b border-[#1a1a1a] border-l-2 cursor-pointer transition-colors hover:bg-[#1a1a1a] group",
                        getTypeColor(notification.type),
                        !notification.read && "bg-[#0066ff]/5"
                      )}
                    >
                      <div className="flex items-start gap-3">
                        <div className="mt-0.5">{getIcon(notification.type)}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className={cn(
                              "text-sm font-medium truncate",
                              notification.read ? "text-[#9a9a9a]" : "text-[#fafafa]"
                            )}>
                              {notification.title}
                            </span>
                            {!notification.read && (
                              <span className="w-2 h-2 bg-[#0066ff] rounded-full flex-shrink-0" />
                            )}
                          </div>
                          <p className="text-xs text-[#6a6a6a] mt-1 line-clamp-2">
                            {notification.message}
                          </p>
                          <span className="text-[10px] text-[#4a4a4a] mt-2 block">
                            {notification.timestamp.toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDelete(notification.id);
                          }}
                          className="p-1 text-[#4a4a4a] hover:text-[#ff2d2d] opacity-0 group-hover:opacity-100 transition-all"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            {notifications.length > 0 && (
              <div className="px-4 py-3 border-t border-[#1a1a1a] bg-[#0a0a0a]">
                <button className="w-full py-2 text-xs text-[#0066ff] hover:text-[#3385ff] font-medium transition-colors">
                  View all notifications
                </button>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
