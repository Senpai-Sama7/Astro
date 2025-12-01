"use client";

import { motion } from "framer-motion";
import { Bot, Plus, Play, Pause, Settings, Trash2, MoreVertical, Activity } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { cn } from "@/utils/cn";
import { useState } from "react";

const agents = [
  {
    id: "AG-001",
    name: "Code Agent",
    description: "Handles code generation, refactoring, and review tasks",
    status: "active",
    tasks: 156,
    successRate: 98.2,
    load: 67,
    uptime: "99.9%",
    memory: "2.4 GB",
    lastActive: "Just now",
  },
  {
    id: "AG-002",
    name: "Research Agent",
    description: "Analyzes documentation and gathers information",
    status: "active",
    tasks: 89,
    successRate: 95.5,
    load: 45,
    uptime: "99.5%",
    memory: "1.8 GB",
    lastActive: "2m ago",
  },
  {
    id: "AG-003",
    name: "Analysis Agent",
    description: "Performs data analysis and generates insights",
    status: "idle",
    tasks: 234,
    successRate: 99.1,
    load: 12,
    uptime: "99.8%",
    memory: "0.8 GB",
    lastActive: "15m ago",
  },
  {
    id: "AG-004",
    name: "Task Agent",
    description: "Orchestrates and manages task workflows",
    status: "active",
    tasks: 412,
    successRate: 97.8,
    load: 78,
    uptime: "99.7%",
    memory: "3.2 GB",
    lastActive: "Just now",
  },
  {
    id: "AG-005",
    name: "Security Agent",
    description: "Monitors security and performs vulnerability scans",
    status: "active",
    tasks: 67,
    successRate: 100,
    load: 34,
    uptime: "100%",
    memory: "1.2 GB",
    lastActive: "5m ago",
  },
];

export function AgentsView() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#fafafa]">Agents</h1>
          <p className="text-sm text-[#6a6a6a] mt-1">Manage and monitor your AI agents</p>
        </div>
        <Button variant="primary" icon={<Plus className="w-4 h-4" />}>
          New Agent
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total Agents", value: "5", color: "#0066ff" },
          { label: "Active", value: "4", color: "#00d26a" },
          { label: "Idle", value: "1", color: "#6a6a6a" },
          { label: "Avg. Success Rate", value: "98.1%", color: "#a855f7" },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="p-4 bg-[#1a1a1a] border border-[#2a2a2a]"
          >
            <div className="text-xs uppercase tracking-wider text-[#6a6a6a] mb-2">{stat.label}</div>
            <div className="text-2xl font-bold font-mono" style={{ color: stat.color }}>
              {stat.value}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {agents.map((agent, index) => (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + index * 0.05 }}
          >
            <div
              onClick={() => setSelectedAgent(selectedAgent === agent.id ? null : agent.id)}
              className={cn(
                "p-5 bg-[#1a1a1a] border transition-all cursor-pointer group",
                selectedAgent === agent.id
                  ? "border-[#0066ff] shadow-[0_0_30px_rgba(0,102,255,0.15)]"
                  : "border-[#2a2a2a] hover:border-[#3a3a3a]"
              )}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "w-10 h-10 flex items-center justify-center",
                    agent.status === "active" ? "bg-[#0066ff]" : "bg-[#2a2a2a]"
                  )}>
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-[#fafafa]">{agent.name}</span>
                      <Badge
                        variant={agent.status === "active" ? "success" : "default"}
                        pulse={agent.status === "active"}
                      >
                        {agent.status}
                      </Badge>
                    </div>
                    <span className="text-xs text-[#6a6a6a]">{agent.id}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {agent.status === "active" ? (
                    <button className="p-1.5 text-[#6a6a6a] hover:text-[#ffd700] hover:bg-[#2a2a2a]">
                      <Pause className="w-4 h-4" />
                    </button>
                  ) : (
                    <button className="p-1.5 text-[#6a6a6a] hover:text-[#00d26a] hover:bg-[#2a2a2a]">
                      <Play className="w-4 h-4" />
                    </button>
                  )}
                  <button className="p-1.5 text-[#6a6a6a] hover:text-[#fafafa] hover:bg-[#2a2a2a]">
                    <Settings className="w-4 h-4" />
                  </button>
                  <button className="p-1.5 text-[#6a6a6a] hover:text-[#ff2d2d] hover:bg-[#2a2a2a]">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <p className="text-sm text-[#6a6a6a] mb-4">{agent.description}</p>

              <div className="grid grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-lg font-bold font-mono text-[#fafafa]">{agent.tasks}</div>
                  <div className="text-[10px] uppercase tracking-wider text-[#4a4a4a]">Tasks</div>
                </div>
                <div>
                  <div className="text-lg font-bold font-mono text-[#00d26a]">{agent.successRate}%</div>
                  <div className="text-[10px] uppercase tracking-wider text-[#4a4a4a]">Success</div>
                </div>
                <div>
                  <div className="text-lg font-bold font-mono text-[#fafafa]">{agent.uptime}</div>
                  <div className="text-[10px] uppercase tracking-wider text-[#4a4a4a]">Uptime</div>
                </div>
                <div>
                  <div className="text-lg font-bold font-mono text-[#a855f7]">{agent.memory}</div>
                  <div className="text-[10px] uppercase tracking-wider text-[#4a4a4a]">Memory</div>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-[#2a2a2a]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-[#6a6a6a]">Load</span>
                  <span className="text-xs font-mono text-[#fafafa]">{agent.load}%</span>
                </div>
                <Progress
                  value={agent.load}
                  variant={agent.load > 70 ? "warning" : "default"}
                  size="sm"
                  animate={false}
                />
                <div className="flex items-center justify-between mt-3">
                  <span className="text-[10px] text-[#4a4a4a]">Last active: {agent.lastActive}</span>
                  <Activity className="w-3 h-3 text-[#00d26a]" />
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
