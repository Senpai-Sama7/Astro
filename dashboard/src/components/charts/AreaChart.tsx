"use client";

import { cn } from "@/utils/cn";
import {
  AreaChart as RechartsAreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface DataPoint {
  name: string;
  value: number;
  value2?: number;
}

interface AreaChartProps {
  data: DataPoint[];
  height?: number;
  gradient?: boolean;
  color?: string;
  color2?: string;
  showGrid?: boolean;
  showAxis?: boolean;
  className?: string;
}

export function AreaChart({
  data,
  height = 200,
  gradient = true,
  color = "#0066ff",
  color2 = "#a855f7",
  showGrid = true,
  showAxis = true,
  className,
}: AreaChartProps) {
  const hasSecondValue = data.some((d) => d.value2 !== undefined);
  const gradientId = `gradient-${color.replace("#", "")}`;
  const gradientId2 = `gradient-${color2.replace("#", "")}`;

  return (
    <div className={cn("w-full", className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsAreaChart
          data={data}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.4} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
            <linearGradient id={gradientId2} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color2} stopOpacity={0.4} />
              <stop offset="100%" stopColor={color2} stopOpacity={0} />
            </linearGradient>
          </defs>
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#2a2a2a"
              vertical={false}
            />
          )}
          {showAxis && (
            <>
              <XAxis
                dataKey="name"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#6a6a6a", fontSize: 10 }}
                dy={10}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#6a6a6a", fontSize: 10 }}
                dx={-10}
              />
            </>
          )}
          <Tooltip
            contentStyle={{
              backgroundColor: "#1a1a1a",
              border: "1px solid #2a2a2a",
              borderRadius: 0,
              padding: "12px",
            }}
            labelStyle={{ color: "#fafafa", fontWeight: 600, marginBottom: 8 }}
            itemStyle={{ color: "#9a9a9a" }}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            fill={gradient ? `url(#${gradientId})` : color}
            fillOpacity={gradient ? 1 : 0.1}
          />
          {hasSecondValue && (
            <Area
              type="monotone"
              dataKey="value2"
              stroke={color2}
              strokeWidth={2}
              fill={gradient ? `url(#${gradientId2})` : color2}
              fillOpacity={gradient ? 1 : 0.1}
            />
          )}
        </RechartsAreaChart>
      </ResponsiveContainer>
    </div>
  );
}
