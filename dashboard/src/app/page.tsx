"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Cpu,
  Zap,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle,
  AlertCircle,
  Clock,
  Server,
  Database,
  Shield,
  MessageSquare,
  X,
} from "lucide-react";

import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { CommandPalette } from "@/components/ai/CommandPalette";
import { ChatInterface } from "@/components/ai/ChatInterface";
import { NotificationsPanel } from "@/components/ai/NotificationsPanel";
import { AgentsView } from "@/components/views/AgentsView";
import { TerminalView } from "@/components/views/TerminalView";
import { SettingsView } from "@/components/views/SettingsView";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Progress, CircularProgress } from "@/components/ui/Progress";
import { StatCard } from "@/components/dashboard/StatCard";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { SystemStatus } from "@/components/dashboard/StatusIndicator";
import { DataTable } from "@/components/dashboard/DataTable";
import { AreaChart } from "@/components/charts/AreaChart";
import { BarChart } from "@/components/charts/BarChart";
import { LineChart } from "@/components/charts/LineChart";
import { DonutChart, DonutLegend } from "@/components/charts/DonutChart";
import { cn } from "@/utils/cn";

// Sample data
const performanceData = [
  { name: "00:00", value: 45, value2: 32 },
  { name: "04:00", value: 52, value2: 38 },
  { name: "08:00", value: 78, value2: 56 },
  { name: "12:00", value: 95, value2: 72 },
  { name: "16:00", value: 88, value2: 68 },
  { name: "20:00", value: 72, value2: 54 },
  { name: "24:00", value: 65, value2: 48 },
];

const taskData = [
  { name: "Mon", value: 120 },
  { name: "Tue", value: 180 },
  { name: "Wed", value: 150 },
  { name: "Thu", value: 220 },
  { name: "Fri", value: 190 },
  { name: "Sat", value: 80 },
  { name: "Sun", value: 60 },
];

const resourceData = [
  { name: "CPU", value: 67, color: "#0066ff" },
  { name: "Memory", value: 45, color: "#00d26a" },
  { name: "Storage", value: 78, color: "#a855f7" },
  { name: "Network", value: 23, color: "#00e5ff" },
];

const agentDistribution = [
  { name: "Code Agent", value: 35, color: "#0066ff" },
  { name: "Research Agent", value: 28, color: "#00d26a" },
  { name: "Analysis Agent", value: 22, color: "#a855f7" },
  { name: "Task Agent", value: 15, color: "#ffd700" },
];

const recentActivity = [
  {
    id: "1",
    title: "Code Agent completed task",
    description: "Refactored authentication module with 98% test coverage",
    timestamp: "2m ago",
    type: "success" as const,
    icon: <CheckCircle className="w-4 h-4" />,
  },
  {
    id: "2",
    title: "Security scan initiated",
    description: "Automated vulnerability assessment started",
    timestamp: "15m ago",
    type: "info" as const,
    icon: <Shield className="w-4 h-4" />,
  },
  {
    id: "3",
    title: "High memory usage detected",
    description: "Research Agent consuming 89% of allocated memory",
    timestamp: "32m ago",
    type: "warning" as const,
    icon: <AlertCircle className="w-4 h-4" />,
  },
  {
    id: "4",
    title: "Database optimization complete",
    description: "Query performance improved by 45%",
    timestamp: "1h ago",
    type: "success" as const,
    icon: <Database className="w-4 h-4" />,
  },
  {
    id: "5",
    title: "New agent deployed",
    description: "Analysis Agent v2.1 now active",
    timestamp: "2h ago",
    type: "info" as const,
    icon: <Bot className="w-4 h-4" />,
  },
];

const systemsData = [
  { name: "Core Engine", status: "online" as const, uptime: "99.99%" },
  { name: "Agent Controller", status: "online" as const, uptime: "99.95%" },
  { name: "Task Scheduler", status: "online" as const, uptime: "99.98%" },
  { name: "Memory Pool", status: "warning" as const, uptime: "98.50%" },
  { name: "API Gateway", status: "online" as const, uptime: "99.99%" },
];

const agentTableData = [
  { id: "AG-001", name: "Code Agent", status: "active", tasks: 156, success: 98.2, load: 67 },
  { id: "AG-002", name: "Research Agent", status: "active", tasks: 89, success: 95.5, load: 45 },
  { id: "AG-003", name: "Analysis Agent", status: "idle", tasks: 234, success: 99.1, load: 12 },
  { id: "AG-004", name: "Task Agent", status: "active", tasks: 412, success: 97.8, load: 78 },
  { id: "AG-005", name: "Security Agent", status: "active", tasks: 67, success: 100, load: 34 },
];

const agentColumns = [
  { key: "id", header: "ID", width: "100px" },
  { key: "name", header: "Agent Name" },
  {
    key: "status",
    header: "Status",
    render: (value: unknown) => (
      <Badge
        variant={value === "active" ? "success" : "default"}
        pulse={value === "active"}
      >
        {String(value)}
      </Badge>
    ),
  },
  { key: "tasks", header: "Tasks", align: "right" as const },
  {
    key: "success",
    header: "Success Rate",
    align: "right" as const,
    render: (value: unknown) => <span className="font-mono">{String(value)}%</span>,
  },
  {
    key: "load",
    header: "Load",
    width: "120px",
    render: (value: unknown) => (
      <Progress
        value={Number(value)}
        variant={Number(value) > 70 ? "warning" : "default"}
        size="sm"
        animate={false}
      />
    ),
  },
];

// Initial notifications
const initialNotifications = [
  {
    id: "1",
    title: "Code Agent completed task",
    message: "Refactored authentication module with 98% test coverage",
    type: "success" as const,
    timestamp: new Date(Date.now() - 2 * 60 * 1000),
    read: false,
  },
  {
    id: "2",
    title: "Security scan initiated",
    message: "Automated vulnerability assessment started for all modules",
    type: "info" as const,
    timestamp: new Date(Date.now() - 15 * 60 * 1000),
    read: false,
  },
  {
    id: "3",
    title: "High memory usage detected",
    message: "Research Agent consuming 89% of allocated memory. Consider optimization.",
    type: "warning" as const,
    timestamp: new Date(Date.now() - 32 * 60 * 1000),
    read: true,
  },
];

export default function Home() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeNav, setActiveNav] = useState("dashboard");
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [notifications, setNotifications] = useState(initialNotifications);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleNavigate = (page: string) => {
    setActiveNav(page);
  };

  const handleMarkRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const handleMarkAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const handleDeleteNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  const getPageTitle = () => {
    switch (activeNav) {
      case "dashboard":
        return { title: "Command Center", subtitle: "Real-time monitoring and control" };
      case "agents":
        return { title: "Agents", subtitle: "Manage and monitor AI agents" };
      case "terminal":
        return { title: "Terminal", subtitle: "System shell access" };
      case "settings":
        return { title: "Settings", subtitle: "Configure system preferences" };
      case "analytics":
        return { title: "Analytics", subtitle: "Performance metrics and insights" };
      case "activity":
        return { title: "Activity", subtitle: "System activity log" };
      case "database":
        return { title: "Database", subtitle: "Data management" };
      case "security":
        return { title: "Security", subtitle: "Security overview" };
      default:
        return { title: "Command Center", subtitle: "Real-time monitoring and control" };
    }
  };

  const pageInfo = getPageTitle();

  const renderDashboard = () => (
    <div className="p-6 space-y-6">
          {/* Top Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Active Agents"
              value="4"
              subtitle="of 5 total"
              icon={<Bot className="w-5 h-5" />}
              variant="accent"
              change={12}
              trend="up"
              delay={0}
            />
            <StatCard
              title="Tasks Completed"
              value="1,247"
              subtitle="Last 24 hours"
              icon={<CheckCircle className="w-5 h-5" />}
              variant="success"
              change={8.5}
              trend="up"
              delay={0.05}
            />
            <StatCard
              title="CPU Usage"
              value="67%"
              subtitle="4 cores active"
              icon={<Cpu className="w-5 h-5" />}
              variant="warning"
              change={-5}
              trend="down"
              delay={0.1}
            />
            <StatCard
              title="Response Time"
              value="23ms"
              subtitle="Avg. latency"
              icon={<Zap className="w-5 h-5" />}
              variant="default"
              change={-12}
              trend="down"
              delay={0.15}
            />
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Performance Chart - Spans 2 columns */}
            <Card className="lg:col-span-2" delay={0.2}>
              <CardHeader>
                <CardTitle>System Performance</CardTitle>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-[#0066ff]" />
                    <span className="text-xs text-[#6a6a6a]">CPU</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-[#a855f7]" />
                    <span className="text-xs text-[#6a6a6a]">Memory</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <AreaChart
                  data={performanceData}
                  height={280}
                  color="#0066ff"
                  color2="#a855f7"
                />
              </CardContent>
            </Card>

            {/* Resource Usage */}
            <Card delay={0.25}>
              <CardHeader>
                <CardTitle>Resource Allocation</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col items-center gap-6">
                <DonutChart
                  data={agentDistribution}
                  size={180}
                  innerRadius={55}
                  outerRadius={75}
                  centerValue="4"
                  centerLabel="Agents"
                />
                <DonutLegend data={agentDistribution} className="w-full" />
              </CardContent>
            </Card>
          </div>

          {/* Middle Row */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Task Distribution */}
            <Card className="lg:col-span-2" delay={0.3}>
              <CardHeader>
                <CardTitle>Task Distribution</CardTitle>
                <Badge variant="info">This Week</Badge>
              </CardHeader>
              <CardContent>
                <BarChart data={taskData} height={200} color="#0066ff" />
              </CardContent>
            </Card>

            {/* System Status */}
            <Card delay={0.35}>
              <CardHeader>
                <CardTitle>System Status</CardTitle>
              </CardHeader>
              <CardContent>
                <SystemStatus systems={systemsData} />
              </CardContent>
            </Card>

            {/* Activity Feed */}
            <Card delay={0.4}>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <Button variant="ghost" size="sm">
                  View All
                </Button>
              </CardHeader>
              <CardContent>
                <ActivityFeed items={recentActivity} maxItems={4} />
              </CardContent>
            </Card>
          </div>

          {/* Resource Metrics Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {resourceData.map((resource, index) => (
              <motion.div
                key={resource.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.45 + index * 0.05 }}
              >
                <Card animate={false} className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[#6a6a6a]">
                      {resource.name}
                    </span>
                    <span
                      className="text-lg font-bold font-mono"
                      style={{ color: resource.color }}
                    >
                      {resource.value}%
                    </span>
                  </div>
                  <Progress
                    value={resource.value}
                    variant={
                      resource.value > 80
                        ? "danger"
                        : resource.value > 60
                        ? "warning"
                        : "default"
                    }
                    size="sm"
                  />
                </Card>
              </motion.div>
            ))}
          </div>

          {/* Agent Table */}
          <Card delay={0.6}>
            <CardHeader>
              <CardTitle>Agent Overview</CardTitle>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm">
                  Export
                </Button>
                <Button variant="primary" size="sm">
                  Add Agent
                </Button>
              </div>
            </CardHeader>
            <DataTable columns={agentColumns} data={agentTableData} />
          </Card>

          {/* Bottom Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card delay={0.65}>
              <CardHeader>
                <CardTitle>Network Traffic</CardTitle>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <ArrowUpRight className="w-4 h-4 text-[#00d26a]" />
                    <span className="text-xs text-[#6a6a6a]">Upload</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <ArrowDownRight className="w-4 h-4 text-[#0066ff]" />
                    <span className="text-xs text-[#6a6a6a]">Download</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <LineChart
                  data={performanceData.map((d) => ({
                    name: d.name,
                    value: d.value * 1.2,
                    value2: d.value2 * 0.8,
                  }))}
                  height={220}
                  colors={["#00d26a", "#0066ff"]}
                />
              </CardContent>
            </Card>

            <Card delay={0.7}>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-6">
                  <div className="flex flex-col items-center">
                    <CircularProgress
                      value={98.5}
                      variant="success"
                      size={100}
                      strokeWidth={6}
                      label="Uptime"
                    />
                  </div>
                  <div className="flex flex-col items-center">
                    <CircularProgress
                      value={67}
                      variant="default"
                      size={100}
                      strokeWidth={6}
                      label="Efficiency"
                    />
                  </div>
                  <div className="flex flex-col items-center">
                    <CircularProgress
                      value={89}
                      variant="warning"
                      size={100}
                      strokeWidth={6}
                      label="Load"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Footer */}
          <div className="border-t border-[#1a1a1a] pt-6 flex items-center justify-between text-xs text-[#6a6a6a]">
            <div className="flex items-center gap-4">
              <span>ASTRO Command Center v2.1.0</span>
              <span className="w-1 h-1 bg-[#3a3a3a] rounded-full" />
              <span>Last sync: Just now</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-3 h-3" />
              <span>Auto-refresh: 30s</span>
            </div>
          </div>
        </div>
  );

  const renderContent = () => {
    if (activeNav === "dashboard") {
      return renderDashboard();
    }
    if (activeNav === "agents") {
      return <AgentsView />;
    }
    if (activeNav === "terminal") {
      return <TerminalView />;
    }
    if (activeNav === "settings") {
      return <SettingsView />;
    }
    // Placeholder for other views
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-[60vh]">
          <div className="text-center">
            <div className="w-16 h-16 bg-[#1a1a1a] border border-[#2a2a2a] flex items-center justify-center mx-auto mb-4">
              <Activity className="w-8 h-8 text-[#3a3a3a]" />
            </div>
            <h2 className="text-xl font-semibold text-[#fafafa] mb-2">{pageInfo.title}</h2>
            <p className="text-sm text-[#6a6a6a]">This section is under development</p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Command Palette */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onNavigate={handleNavigate}
      />

      {/* Notifications Panel */}
      <NotificationsPanel
        isOpen={notificationsOpen}
        onClose={() => setNotificationsOpen(false)}
        notifications={notifications}
        onMarkRead={handleMarkRead}
        onMarkAllRead={handleMarkAllRead}
        onDelete={handleDeleteNotification}
      />

      {/* AI Chat Panel */}
      <AnimatePresence>
        {chatOpen && (
          <motion.div
            initial={{ opacity: 0, x: 400 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 400 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="fixed right-0 top-0 bottom-0 w-[420px] border-l border-[#2a2a2a] shadow-2xl shadow-black/50 z-50"
          >
            <ChatInterface className="h-full" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating AI Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setChatOpen(!chatOpen)}
        className={cn(
          "fixed bottom-6 right-6 w-14 h-14 flex items-center justify-center shadow-lg z-50 transition-all",
          chatOpen
            ? "bg-[#ff2d2d] text-white"
            : "bg-gradient-to-br from-[#0066ff] to-[#a855f7] text-white"
        )}
        style={{
          boxShadow: chatOpen
            ? "0 0 30px rgba(255, 45, 45, 0.3)"
            : "0 0 30px rgba(0, 102, 255, 0.3)",
        }}
      >
        {chatOpen ? (
          <X className="w-6 h-6" />
        ) : (
          <MessageSquare className="w-6 h-6" />
        )}
      </motion.button>

      <Sidebar
        activeItem={activeNav}
        onItemClick={setActiveNav}
        collapsed={sidebarCollapsed}
        onCollapsedChange={setSidebarCollapsed}
      />

      <main
        className="transition-all duration-300"
        style={{ marginLeft: sidebarCollapsed ? 72 : 240 }}
      >
        <Header
          title={pageInfo.title}
          subtitle={pageInfo.subtitle}
          onSearchClick={() => setCommandPaletteOpen(true)}
          onNotificationsClick={() => setNotificationsOpen(true)}
          notificationCount={unreadCount}
        />

        {renderContent()}
      </main>
    </div>
  );
}
