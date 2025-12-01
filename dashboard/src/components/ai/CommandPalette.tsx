"use client";

import { cn } from "@/utils/cn";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import {
  Search,
  Command,
  Bot,
  Zap,
  Terminal,
  FileCode,
  Database,
  Settings,
  ArrowRight,
  Sparkles,
  X,
} from "lucide-react";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate?: (page: string) => void;
}

const commands = [
  { id: "agents", label: "Go to Agents", icon: Bot, category: "Navigation", shortcut: "G A" },
  { id: "analytics", label: "Go to Analytics", icon: Zap, category: "Navigation", shortcut: "G N" },
  { id: "terminal", label: "Open Terminal", icon: Terminal, category: "Navigation", shortcut: "G T" },
  { id: "database", label: "Browse Database", icon: Database, category: "Navigation", shortcut: "G D" },
  { id: "settings", label: "Open Settings", icon: Settings, category: "Navigation", shortcut: "G S" },
  { id: "new-agent", label: "Create New Agent", icon: Bot, category: "Actions", shortcut: "N A" },
  { id: "run-task", label: "Run Task", icon: Zap, category: "Actions", shortcut: "R T" },
  { id: "generate-code", label: "Generate Code", icon: FileCode, category: "AI", shortcut: "A C" },
  { id: "analyze", label: "Analyze Codebase", icon: Sparkles, category: "AI", shortcut: "A A" },
];

export function CommandPalette({ isOpen, onClose, onNavigate }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const filteredCommands = commands.filter(
    (cmd) =>
      cmd.label.toLowerCase().includes(query.toLowerCase()) ||
      cmd.category.toLowerCase().includes(query.toLowerCase())
  );

  const groupedCommands = filteredCommands.reduce((acc, cmd) => {
    if (!acc[cmd.category]) acc[cmd.category] = [];
    acc[cmd.category].push(cmd);
    return acc;
  }, {} as Record<string, typeof commands>);

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
      setQuery("");
      setSelectedIndex(0);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((i) => Math.min(i + 1, filteredCommands.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === "Enter" && filteredCommands[selectedIndex]) {
        e.preventDefault();
        const cmd = filteredCommands[selectedIndex];
        if (cmd.category === "Navigation") {
          onNavigate?.(cmd.id);
        }
        onClose();
      } else if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, selectedIndex, filteredCommands, onClose, onNavigate]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100]"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="fixed top-[15%] left-1/2 -translate-x-1/2 w-full max-w-2xl z-[101]"
          >
            <div className="bg-[#0f0f0f] border border-[#2a2a2a] shadow-2xl shadow-black/50 overflow-hidden">
              {/* Search Input */}
              <div className="flex items-center gap-3 px-4 py-4 border-b border-[#1a1a1a]">
                <Search className="w-5 h-5 text-[#6a6a6a]" />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setSelectedIndex(0);
                  }}
                  placeholder="Search commands, actions, or type a question..."
                  className="flex-1 bg-transparent text-[#fafafa] text-lg placeholder:text-[#4a4a4a] outline-none"
                />
                <div className="flex items-center gap-1 px-2 py-1 bg-[#1a1a1a] border border-[#2a2a2a]">
                  <span className="text-[10px] text-[#6a6a6a]">ESC</span>
                </div>
              </div>

              {/* AI Hint */}
              <div className="px-4 py-3 bg-gradient-to-r from-[#0066ff]/10 to-transparent border-b border-[#1a1a1a]">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-[#0066ff]" />
                  <span className="text-xs text-[#6a6a6a]">
                    Try: "Create a new agent for code review" or "Show me CPU usage trends"
                  </span>
                </div>
              </div>

              {/* Commands List */}
              <div className="max-h-[400px] overflow-y-auto py-2">
                {Object.entries(groupedCommands).map(([category, cmds]) => (
                  <div key={category} className="px-2 py-1">
                    <div className="px-2 py-2 text-[10px] font-semibold uppercase tracking-wider text-[#4a4a4a]">
                      {category}
                    </div>
                    {cmds.map((cmd) => {
                      const globalIndex = filteredCommands.indexOf(cmd);
                      const isSelected = globalIndex === selectedIndex;
                      const Icon = cmd.icon;

                      return (
                        <button
                          key={cmd.id}
                          onClick={() => {
                            if (cmd.category === "Navigation") {
                              onNavigate?.(cmd.id);
                            }
                            onClose();
                          }}
                          onMouseEnter={() => setSelectedIndex(globalIndex)}
                          className={cn(
                            "w-full flex items-center gap-3 px-3 py-2.5 transition-all duration-100",
                            isSelected
                              ? "bg-[#0066ff] text-white"
                              : "text-[#9a9a9a] hover:bg-[#1a1a1a]"
                          )}
                        >
                          <Icon className="w-4 h-4" />
                          <span className="flex-1 text-left text-sm">{cmd.label}</span>
                          <span
                            className={cn(
                              "text-[10px] font-mono",
                              isSelected ? "text-white/60" : "text-[#4a4a4a]"
                            )}
                          >
                            {cmd.shortcut}
                          </span>
                          {isSelected && <ArrowRight className="w-4 h-4" />}
                        </button>
                      );
                    })}
                  </div>
                ))}

                {filteredCommands.length === 0 && (
                  <div className="px-4 py-8 text-center">
                    <p className="text-sm text-[#6a6a6a]">No commands found</p>
                    <p className="text-xs text-[#4a4a4a] mt-1">
                      Try asking a question instead
                    </p>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="px-4 py-3 border-t border-[#1a1a1a] flex items-center justify-between bg-[#0a0a0a]">
                <div className="flex items-center gap-4 text-[10px] text-[#4a4a4a]">
                  <span className="flex items-center gap-1">
                    <span className="px-1.5 py-0.5 bg-[#1a1a1a] border border-[#2a2a2a]">↑↓</span>
                    Navigate
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="px-1.5 py-0.5 bg-[#1a1a1a] border border-[#2a2a2a]">↵</span>
                    Select
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Command className="w-3 h-3 text-[#4a4a4a]" />
                  <span className="text-[10px] text-[#4a4a4a]">ASTRO AI</span>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
