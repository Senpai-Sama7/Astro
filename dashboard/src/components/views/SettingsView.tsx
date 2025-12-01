"use client";

import { motion } from "framer-motion";
import { 
  Settings, 
  User, 
  Bell, 
  Shield, 
  Palette, 
  Database, 
  Zap, 
  Save,
  Moon,
  Sun,
  Monitor,
  Check,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { cn } from "@/utils/cn";
import { useState } from "react";

const sections = [
  { id: "general", label: "General", icon: Settings },
  { id: "appearance", label: "Appearance", icon: Palette },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "security", label: "Security", icon: Shield },
  { id: "performance", label: "Performance", icon: Zap },
  { id: "data", label: "Data & Storage", icon: Database },
];

export function SettingsView() {
  const [activeSection, setActiveSection] = useState("general");
  const [theme, setTheme] = useState("dark");
  const [settings, setSettings] = useState({
    autoSave: true,
    notifications: true,
    soundEffects: false,
    animationsEnabled: true,
    compactMode: false,
    developerMode: false,
    autoRefresh: true,
    refreshInterval: 30,
    maxAgents: 10,
    memoryLimit: 16,
  });

  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[#fafafa]">Settings</h1>
          <p className="text-sm text-[#6a6a6a] mt-1">Manage your preferences and configuration</p>
        </div>
        <Button variant="primary" onClick={handleSave} icon={saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}>
          {saved ? "Saved" : "Save Changes"}
        </Button>
      </div>

      <div className="flex gap-6">
        {/* Sidebar */}
        <div className="w-56 flex-shrink-0">
          <nav className="space-y-1">
            {sections.map((section) => {
              const Icon = section.icon;
              const isActive = activeSection === section.id;
              return (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium transition-all",
                    isActive
                      ? "bg-[#0066ff] text-white"
                      : "text-[#6a6a6a] hover:text-[#fafafa] hover:bg-[#1a1a1a]"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {section.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 space-y-6">
          {activeSection === "general" && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-6"
            >
              <Card animate={false}>
                <CardHeader>
                  <CardTitle>General Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <SettingRow
                    label="Auto-save"
                    description="Automatically save changes"
                    checked={settings.autoSave}
                    onChange={(v) => setSettings({ ...settings, autoSave: v })}
                  />
                  <SettingRow
                    label="Animations"
                    description="Enable UI animations"
                    checked={settings.animationsEnabled}
                    onChange={(v) => setSettings({ ...settings, animationsEnabled: v })}
                  />
                  <SettingRow
                    label="Compact Mode"
                    description="Reduce spacing and padding"
                    checked={settings.compactMode}
                    onChange={(v) => setSettings({ ...settings, compactMode: v })}
                  />
                  <SettingRow
                    label="Developer Mode"
                    description="Enable advanced features"
                    checked={settings.developerMode}
                    onChange={(v) => setSettings({ ...settings, developerMode: v })}
                  />
                </CardContent>
              </Card>
            </motion.div>
          )}

          {activeSection === "appearance" && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-6"
            >
              <Card animate={false}>
                <CardHeader>
                  <CardTitle>Theme</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    {[
                      { id: "light", label: "Light", icon: Sun },
                      { id: "dark", label: "Dark", icon: Moon },
                      { id: "system", label: "System", icon: Monitor },
                    ].map((t) => {
                      const Icon = t.icon;
                      return (
                        <button
                          key={t.id}
                          onClick={() => setTheme(t.id)}
                          className={cn(
                            "p-4 border flex flex-col items-center gap-2 transition-all",
                            theme === t.id
                              ? "border-[#0066ff] bg-[#0066ff]/10"
                              : "border-[#2a2a2a] hover:border-[#3a3a3a]"
                          )}
                        >
                          <Icon className={cn("w-6 h-6", theme === t.id ? "text-[#0066ff]" : "text-[#6a6a6a]")} />
                          <span className={cn("text-sm", theme === t.id ? "text-[#fafafa]" : "text-[#6a6a6a]")}>
                            {t.label}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              <Card animate={false}>
                <CardHeader>
                  <CardTitle>Accent Color</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-3">
                    {["#0066ff", "#00d26a", "#a855f7", "#ff2d2d", "#ffd700", "#00e5ff"].map((color) => (
                      <button
                        key={color}
                        className="w-10 h-10 border-2 border-transparent hover:border-white/20 transition-colors"
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {activeSection === "performance" && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-6"
            >
              <Card animate={false}>
                <CardHeader>
                  <CardTitle>Performance</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <SettingRow
                    label="Auto-refresh"
                    description="Automatically refresh dashboard data"
                    checked={settings.autoRefresh}
                    onChange={(v) => setSettings({ ...settings, autoRefresh: v })}
                  />
                  
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="text-sm font-medium text-[#fafafa]">Refresh Interval</div>
                        <div className="text-xs text-[#6a6a6a]">How often to refresh data</div>
                      </div>
                      <span className="text-sm font-mono text-[#0066ff]">{settings.refreshInterval}s</span>
                    </div>
                    <input
                      type="range"
                      min="10"
                      max="120"
                      step="10"
                      value={settings.refreshInterval}
                      onChange={(e) => setSettings({ ...settings, refreshInterval: parseInt(e.target.value) })}
                      className="w-full h-1 bg-[#2a2a2a] appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-[#0066ff]"
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="text-sm font-medium text-[#fafafa]">Max Concurrent Agents</div>
                        <div className="text-xs text-[#6a6a6a]">Maximum number of active agents</div>
                      </div>
                      <span className="text-sm font-mono text-[#0066ff]">{settings.maxAgents}</span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="20"
                      value={settings.maxAgents}
                      onChange={(e) => setSettings({ ...settings, maxAgents: parseInt(e.target.value) })}
                      className="w-full h-1 bg-[#2a2a2a] appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-[#0066ff]"
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="text-sm font-medium text-[#fafafa]">Memory Limit</div>
                        <div className="text-xs text-[#6a6a6a]">Maximum memory allocation (GB)</div>
                      </div>
                      <span className="text-sm font-mono text-[#0066ff]">{settings.memoryLimit} GB</span>
                    </div>
                    <input
                      type="range"
                      min="4"
                      max="64"
                      step="4"
                      value={settings.memoryLimit}
                      onChange={(e) => setSettings({ ...settings, memoryLimit: parseInt(e.target.value) })}
                      className="w-full h-1 bg-[#2a2a2a] appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-[#0066ff]"
                    />
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}

function SettingRow({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between py-2">
      <div>
        <div className="text-sm font-medium text-[#fafafa]">{label}</div>
        <div className="text-xs text-[#6a6a6a]">{description}</div>
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={cn(
          "w-11 h-6 rounded-full transition-colors relative",
          checked ? "bg-[#0066ff]" : "bg-[#2a2a2a]"
        )}
      >
        <div
          className={cn(
            "absolute top-1 w-4 h-4 bg-white rounded-full transition-transform",
            checked ? "translate-x-6" : "translate-x-1"
          )}
        />
      </button>
    </div>
  );
}
