"use client";

import { motion } from "framer-motion";
import { Terminal, Plus, X, Maximize2, Minimize2, Copy, Check } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { cn } from "@/utils/cn";

interface TerminalLine {
  id: string;
  type: "input" | "output" | "error" | "success" | "info";
  content: string;
  timestamp: Date;
}

const initialLines: TerminalLine[] = [
  { id: "1", type: "info", content: "ASTRO Terminal v2.1.0", timestamp: new Date() },
  { id: "2", type: "info", content: "Type 'help' for available commands", timestamp: new Date() },
  { id: "3", type: "input", content: "$ astro status", timestamp: new Date() },
  { id: "4", type: "success", content: "✓ All systems operational", timestamp: new Date() },
  { id: "5", type: "output", content: "  Agents: 4 active, 1 idle", timestamp: new Date() },
  { id: "6", type: "output", content: "  Tasks: 1,247 completed today", timestamp: new Date() },
  { id: "7", type: "output", content: "  Memory: 9.4 GB / 16 GB", timestamp: new Date() },
  { id: "8", type: "input", content: "$ astro agents list", timestamp: new Date() },
  { id: "9", type: "output", content: "ID        NAME              STATUS    LOAD", timestamp: new Date() },
  { id: "10", type: "output", content: "AG-001    Code Agent        active    67%", timestamp: new Date() },
  { id: "11", type: "output", content: "AG-002    Research Agent    active    45%", timestamp: new Date() },
  { id: "12", type: "output", content: "AG-003    Analysis Agent    idle      12%", timestamp: new Date() },
  { id: "13", type: "output", content: "AG-004    Task Agent        active    78%", timestamp: new Date() },
  { id: "14", type: "output", content: "AG-005    Security Agent    active    34%", timestamp: new Date() },
];

const commands: Record<string, string[]> = {
  help: [
    "Available commands:",
    "  status          - Show system status",
    "  agents list     - List all agents",
    "  agents start    - Start an agent",
    "  agents stop     - Stop an agent",
    "  tasks list      - List recent tasks",
    "  clear           - Clear terminal",
    "  exit            - Close terminal",
  ],
  status: [
    "✓ All systems operational",
    "  Agents: 4 active, 1 idle",
    "  Tasks: 1,247 completed today",
    "  Memory: 9.4 GB / 16 GB",
    "  CPU: 67% utilized",
  ],
  "agents list": [
    "ID        NAME              STATUS    LOAD",
    "AG-001    Code Agent        active    67%",
    "AG-002    Research Agent    active    45%",
    "AG-003    Analysis Agent    idle      12%",
    "AG-004    Task Agent        active    78%",
    "AG-005    Security Agent    active    34%",
  ],
  "tasks list": [
    "Recent tasks:",
    "  #1247  Code review completed      2m ago",
    "  #1246  Documentation generated    5m ago",
    "  #1245  Security scan passed       12m ago",
    "  #1244  API tests executed         18m ago",
    "  #1243  Database optimized         25m ago",
  ],
};

export function TerminalView() {
  const [lines, setLines] = useState<TerminalLine[]>(initialLines);
  const [input, setInput] = useState("");
  const [isMaximized, setIsMaximized] = useState(false);
  const [copied, setCopied] = useState(false);
  const terminalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    terminalRef.current?.scrollTo({ top: terminalRef.current.scrollHeight, behavior: "smooth" });
  }, [lines]);

  const handleCommand = (cmd: string) => {
    const trimmed = cmd.trim().toLowerCase();
    
    // Add input line
    const inputLine: TerminalLine = {
      id: Date.now().toString(),
      type: "input",
      content: `$ ${cmd}`,
      timestamp: new Date(),
    };
    
    if (trimmed === "clear") {
      setLines([
        { id: Date.now().toString(), type: "info", content: "Terminal cleared", timestamp: new Date() },
      ]);
      return;
    }

    const output = commands[trimmed];
    if (output) {
      const outputLines: TerminalLine[] = output.map((line, i) => ({
        id: `${Date.now()}-${i}`,
        type: line.startsWith("✓") ? "success" : "output",
        content: line,
        timestamp: new Date(),
      }));
      setLines((prev) => [...prev, inputLine, ...outputLines]);
    } else {
      setLines((prev) => [
        ...prev,
        inputLine,
        {
          id: `${Date.now()}-err`,
          type: "error",
          content: `Command not found: ${trimmed}. Type 'help' for available commands.`,
          timestamp: new Date(),
        },
      ]);
    }
  };

  const handleCopy = () => {
    const text = lines.map((l) => l.content).join("\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getLineColor = (type: TerminalLine["type"]) => {
    switch (type) {
      case "input":
        return "text-[#00e5ff]";
      case "error":
        return "text-[#ff2d2d]";
      case "success":
        return "text-[#00d26a]";
      case "info":
        return "text-[#6a6a6a]";
      default:
        return "text-[#9a9a9a]";
    }
  };

  return (
    <div className={cn(
      "p-6",
      isMaximized && "fixed inset-0 z-50 bg-[#0a0a0a] p-0"
    )}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          "bg-[#0a0a0a] border border-[#2a2a2a] flex flex-col",
          isMaximized ? "h-full" : "h-[calc(100vh-180px)]"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2 bg-[#1a1a1a] border-b border-[#2a2a2a]">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-[#00e5ff]" />
            <span className="text-sm font-medium text-[#fafafa]">Terminal</span>
            <span className="text-xs text-[#4a4a4a]">— ASTRO Shell</span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={handleCopy}
              className="p-1.5 text-[#6a6a6a] hover:text-[#fafafa] hover:bg-[#2a2a2a] transition-colors"
            >
              {copied ? <Check className="w-4 h-4 text-[#00d26a]" /> : <Copy className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setIsMaximized(!isMaximized)}
              className="p-1.5 text-[#6a6a6a] hover:text-[#fafafa] hover:bg-[#2a2a2a] transition-colors"
            >
              {isMaximized ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Terminal Content */}
        <div
          ref={terminalRef}
          onClick={() => inputRef.current?.focus()}
          className="flex-1 p-4 font-mono text-sm overflow-y-auto cursor-text"
        >
          {lines.map((line) => (
            <div key={line.id} className={cn("py-0.5", getLineColor(line.type))}>
              {line.content}
            </div>
          ))}
          
          {/* Input Line */}
          <div className="flex items-center py-0.5">
            <span className="text-[#00e5ff]">$ </span>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && input.trim()) {
                  handleCommand(input);
                  setInput("");
                }
              }}
              className="flex-1 bg-transparent text-[#fafafa] outline-none ml-1"
              autoFocus
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-[#2a2a2a] bg-[#0f0f0f] flex items-center justify-between text-[10px] text-[#4a4a4a]">
          <span>ASTRO Shell v2.1.0</span>
          <span>{lines.filter((l) => l.type === "input").length} commands executed</span>
        </div>
      </motion.div>
    </div>
  );
}
