"use client";

import { cn } from "@/utils/cn";
import {
  LineChart as RechartsLineChart,
  Line,
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
  value3?: number;
}

interface LineChartProps {
  data: DataPoint[];
  height?: number;
  colors?: string[];
  showGrid?: boolean;
  showAxis?: boolean;
  showDots?: boolean;
  curved?: boolean;
  className?: string;
}

export function LineChart({
  data,
  height = 200,
  colors = ["#0066ff", "#00d26a", "#a855f7"],
  showGrid = true,
  showAxis = true,
  showDots = true,
  curved = true,
  className,
}: LineChartProps) {
  const dataKeys = ["value", "value2", "value3"].filter((key) =>
    data.some((d) => d[key as keyof DataPoint] !== undefined)
  );

  return (
    <div className={cn("w-full", className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsLineChart
          data={data}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
        >
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
          {dataKeys.map((key, index) => (
            <Line
              key={key}
              type={curved ? "monotone" : "linear"}
              dataKey={key}
              stroke={colors[index] || colors[0]}
              strokeWidth={2}
              dot={
                showDots
                  ? {
                      fill: colors[index] || colors[0],
                      strokeWidth: 0,
                      r: 3,
                    }
                  : false
              }
              activeDot={{
                r: 5,
                fill: colors[index] || colors[0],
                stroke: "#0a0a0a",
                strokeWidth: 2,
              }}
            />
          ))}
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
}
