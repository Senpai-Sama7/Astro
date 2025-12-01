"use client";

import { cn } from "@/utils/cn";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { motion } from "framer-motion";

interface DataPoint {
  name: string;
  value: number;
  color: string;
  [key: string]: string | number;
}

interface DonutChartProps {
  data: DataPoint[];
  size?: number;
  innerRadius?: number;
  outerRadius?: number;
  centerLabel?: string;
  centerValue?: string | number;
  className?: string;
}

export function DonutChart({
  data,
  size = 200,
  innerRadius = 60,
  outerRadius = 80,
  centerLabel,
  centerValue,
  className,
}: DonutChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className={cn("relative", className)} style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            paddingAngle={2}
            dataKey="value"
            strokeWidth={0}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: "#1a1a1a",
              border: "1px solid #2a2a2a",
              borderRadius: 0,
              padding: "12px",
            }}
            labelStyle={{ color: "#fafafa", fontWeight: 600 }}
            itemStyle={{ color: "#9a9a9a" }}
            formatter={(value: number) => [
              `${value} (${((value / total) * 100).toFixed(1)}%)`,
              "",
            ]}
          />
        </PieChart>
      </ResponsiveContainer>
      {(centerLabel || centerValue) && (
        <motion.div
          className="absolute inset-0 flex flex-col items-center justify-center"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3, duration: 0.4 }}
        >
          {centerValue && (
            <span className="text-2xl font-bold text-[#fafafa] font-mono">
              {centerValue}
            </span>
          )}
          {centerLabel && (
            <span className="text-[10px] uppercase tracking-wider text-[#6a6a6a]">
              {centerLabel}
            </span>
          )}
        </motion.div>
      )}
    </div>
  );
}

interface DonutLegendProps {
  data: DataPoint[];
  className?: string;
}

export function DonutLegend({ data, className }: DonutLegendProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className={cn("space-y-2", className)}>
      {data.map((item, index) => (
        <motion.div
          key={item.name}
          className="flex items-center justify-between"
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 * index, duration: 0.3 }}
        >
          <div className="flex items-center gap-2">
            <div
              className="w-3 h-3"
              style={{ backgroundColor: item.color }}
            />
            <span className="text-sm text-[#9a9a9a]">{item.name}</span>
          </div>
          <span className="text-sm font-mono text-[#fafafa]">
            {((item.value / total) * 100).toFixed(1)}%
          </span>
        </motion.div>
      ))}
    </div>
  );
}
