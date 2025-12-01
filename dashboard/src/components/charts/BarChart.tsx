"use client";

import { cn } from "@/utils/cn";
import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface DataPoint {
  name: string;
  value: number;
  color?: string;
}

interface BarChartProps {
  data: DataPoint[];
  height?: number;
  color?: string;
  showGrid?: boolean;
  showAxis?: boolean;
  horizontal?: boolean;
  className?: string;
}

export function BarChart({
  data,
  height = 200,
  color = "#0066ff",
  showGrid = true,
  showAxis = true,
  horizontal = false,
  className,
}: BarChartProps) {
  return (
    <div className={cn("w-full", className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsBarChart
          data={data}
          layout={horizontal ? "vertical" : "horizontal"}
          margin={{ top: 10, right: 10, left: horizontal ? 60 : -20, bottom: 0 }}
        >
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#2a2a2a"
              horizontal={!horizontal}
              vertical={horizontal}
            />
          )}
          {showAxis && (
            <>
              {horizontal ? (
                <>
                  <XAxis
                    type="number"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "#6a6a6a", fontSize: 10 }}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "#6a6a6a", fontSize: 10 }}
                    width={50}
                  />
                </>
              ) : (
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
            cursor={{ fill: "rgba(255,255,255,0.05)" }}
          />
          <Bar dataKey="value" radius={[2, 2, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color || color} />
            ))}
          </Bar>
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
}
