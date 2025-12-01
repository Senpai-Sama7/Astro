"use client";

import { cn } from "@/utils/cn";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useRef, useEffect } from "react";
import {
  Send,
  Sparkles,
  Bot,
  User,
  Copy,
  Check,
  RefreshCw,
  Settings,
  ChevronDown,
  Zap,
  Brain,
  Cpu,
  MoreHorizontal,
} from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  status?: "sending" | "sent" | "error";
}

interface ModelConfig {
  model: string;
  temperature: number;
  maxTokens: number;
  contextWindow: string;
}

const models = [
  { id: "astro-4", name: "ASTRO-4", description: "Most capable", tokens: "128K" },
  { id: "astro-4-turbo", name: "ASTRO-4 Turbo", description: "Fastest", tokens: "64K" },
  { id: "astro-3.5", name: "ASTRO-3.5", description: "Balanced", tokens: "32K" },
];

const sampleResponses = [
  "I've analyzed your request. Based on the current system state, I recommend optimizing the memory allocation for the Research Agent. Would you like me to proceed with the optimization?",
  "The code review agent has identified 3 potential issues in the authentication module. I can fix them automatically or provide detailed explanations for manual review.",
  "I've created a new agent configuration based on your specifications. The agent is optimized for high-throughput task processing with 99.5% reliability.",
  "System analysis complete. CPU usage is trending upward due to increased task parallelization. I can suggest load balancing strategies if needed.",
];

export function ChatInterface({ className }: { className?: string }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! I'm ASTRO, your AI assistant. I can help you manage agents, analyze system performance, generate code, and more. What would you like to do?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [config, setConfig] = useState<ModelConfig>({
    model: "astro-4",
    temperature: 0.7,
    maxTokens: 4096,
    contextWindow: "Last 10 messages",
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
      status: "sending",
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const response: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: sampleResponses[Math.floor(Math.random() * sampleResponses.length)],
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, response]);
      setIsTyping(false);
    }, 1500 + Math.random() * 1000);
  };

  const handleCopy = (id: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const selectedModel = models.find((m) => m.id === config.model) || models[0];

  return (
    <div className={cn("flex flex-col h-full bg-[#0a0a0a]", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#1a1a1a] bg-[#0f0f0f]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-[#0066ff] to-[#a855f7] flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[#fafafa]">ASTRO AI</h3>
            <p className="text-[10px] text-[#6a6a6a]">Natural Language Interface</p>
          </div>
        </div>
        <button
          onClick={() => setShowSettings(!showSettings)}
          className={cn(
            "p-2 transition-colors",
            showSettings ? "bg-[#1a1a1a] text-[#fafafa]" : "text-[#6a6a6a] hover:text-[#fafafa]"
          )}
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>

      {/* Settings Panel */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-b border-[#1a1a1a] overflow-hidden"
          >
            <div className="p-4 space-y-4 bg-[#0f0f0f]">
              {/* Model Selection */}
              <div>
                <label className="text-[10px] font-semibold uppercase tracking-wider text-[#6a6a6a] block mb-2">
                  Model
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {models.map((model) => (
                    <button
                      key={model.id}
                      onClick={() => setConfig({ ...config, model: model.id })}
                      className={cn(
                        "p-3 border text-left transition-all",
                        config.model === model.id
                          ? "border-[#0066ff] bg-[#0066ff]/10"
                          : "border-[#2a2a2a] hover:border-[#3a3a3a]"
                      )}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Brain className="w-3 h-3 text-[#0066ff]" />
                        <span className="text-xs font-medium text-[#fafafa]">{model.name}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-[#6a6a6a]">{model.description}</span>
                        <span className="text-[10px] text-[#4a4a4a]">{model.tokens}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Temperature */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-[10px] font-semibold uppercase tracking-wider text-[#6a6a6a]">
                    Temperature
                  </label>
                  <span className="text-xs font-mono text-[#fafafa]">{config.temperature}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.temperature}
                  onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                  className="w-full h-1 bg-[#2a2a2a] appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-[#0066ff]"
                />
                <div className="flex justify-between mt-1">
                  <span className="text-[10px] text-[#4a4a4a]">Precise</span>
                  <span className="text-[10px] text-[#4a4a4a]">Creative</span>
                </div>
              </div>

              {/* Context */}
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-[10px] font-semibold uppercase tracking-wider text-[#6a6a6a] block">
                    Context Window
                  </label>
                  <span className="text-xs text-[#9a9a9a]">{config.contextWindow}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Cpu className="w-3 h-3 text-[#6a6a6a]" />
                  <span className="text-xs font-mono text-[#fafafa]">{config.maxTokens}</span>
                  <span className="text-[10px] text-[#4a4a4a]">tokens</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
              "flex gap-3",
              message.role === "user" ? "flex-row-reverse" : ""
            )}
          >
            <div
              className={cn(
                "w-8 h-8 flex-shrink-0 flex items-center justify-center",
                message.role === "assistant"
                  ? "bg-gradient-to-br from-[#0066ff] to-[#a855f7]"
                  : "bg-[#2a2a2a]"
              )}
            >
              {message.role === "assistant" ? (
                <Bot className="w-4 h-4 text-white" />
              ) : (
                <User className="w-4 h-4 text-[#9a9a9a]" />
              )}
            </div>
            <div
              className={cn(
                "flex-1 max-w-[80%]",
                message.role === "user" ? "text-right" : ""
              )}
            >
              <div
                className={cn(
                  "inline-block p-4 text-sm",
                  message.role === "assistant"
                    ? "bg-[#1a1a1a] border border-[#2a2a2a] text-[#e8e8e8]"
                    : "bg-[#0066ff] text-white"
                )}
              >
                {message.content}
              </div>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-[10px] text-[#4a4a4a]">
                  {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
                {message.role === "assistant" && (
                  <button
                    onClick={() => handleCopy(message.id, message.content)}
                    className="p-1 text-[#4a4a4a] hover:text-[#9a9a9a] transition-colors"
                  >
                    {copiedId === message.id ? (
                      <Check className="w-3 h-3 text-[#00d26a]" />
                    ) : (
                      <Copy className="w-3 h-3" />
                    )}
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        ))}

        {isTyping && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3"
          >
            <div className="w-8 h-8 flex-shrink-0 bg-gradient-to-br from-[#0066ff] to-[#a855f7] flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="p-4 bg-[#1a1a1a] border border-[#2a2a2a]">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-[#6a6a6a] rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 bg-[#6a6a6a] rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 bg-[#6a6a6a] rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-[#1a1a1a] bg-[#0f0f0f]">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[10px] text-[#4a4a4a]">Using</span>
          <span className="px-2 py-0.5 bg-[#1a1a1a] border border-[#2a2a2a] text-[10px] text-[#0066ff] font-medium">
            {selectedModel.name}
          </span>
          <span className="text-[10px] text-[#4a4a4a]">•</span>
          <span className="text-[10px] text-[#4a4a4a]">{messages.length} messages in context</span>
        </div>
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask anything or give a command..."
              rows={1}
              className="w-full px-4 py-3 bg-[#1a1a1a] border border-[#2a2a2a] text-[#fafafa] text-sm placeholder:text-[#4a4a4a] resize-none outline-none focus:border-[#0066ff] transition-colors"
            />
          </div>
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className={cn(
              "px-4 py-3 flex items-center justify-center transition-all",
              input.trim() && !isTyping
                ? "bg-[#0066ff] text-white"
                : "bg-[#1a1a1a] text-[#4a4a4a] cursor-not-allowed"
            )}
          >
            <Send className="w-4 h-4" />
          </motion.button>
        </div>
      </div>
    </div>
  );
}
