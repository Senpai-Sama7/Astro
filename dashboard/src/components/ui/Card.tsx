"use client";

import { cn } from "@/utils/cn";
import { motion } from "framer-motion";
import { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  variant?: "default" | "accent" | "glass" | "outline";
  hover?: boolean;
  glow?: "blue" | "green" | "red" | "none";
  animate?: boolean;
  delay?: number;
}

export function Card({
  children,
  className,
  variant = "default",
  hover = true,
  glow = "none",
  animate = true,
  delay = 0,
}: CardProps) {
  const variants = {
    default: "bg-[#1a1a1a] border border-[#2a2a2a]",
    accent: "bg-[#1a1a1a] border-2 border-[#0066ff]",
    glass: "bg-[#1a1a1a]/60 backdrop-blur-xl border border-[#2a2a2a]/50",
    outline: "bg-transparent border-2 border-[#3a3a3a]",
  };

  const glowStyles = {
    blue: "shadow-[0_0_30px_rgba(0,102,255,0.15)]",
    green: "shadow-[0_0_30px_rgba(0,210,106,0.15)]",
    red: "shadow-[0_0_30px_rgba(255,45,45,0.15)]",
    none: "",
  };

  const content = (
    <div
      className={cn(
        "relative overflow-hidden",
        variants[variant],
        glowStyles[glow],
        hover && "transition-all duration-300 hover:border-[#4a4a4a] hover:translate-y-[-2px]",
        className
      )}
    >
      {children}
    </div>
  );

  if (!animate) return content;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.16, 1, 0.3, 1] }}
    >
      {content}
    </motion.div>
  );
}

export function CardHeader({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "px-6 py-4 border-b border-[#2a2a2a] flex items-center justify-between",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardTitle({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <h3
      className={cn(
        "text-sm font-semibold uppercase tracking-wider text-[#9a9a9a]",
        className
      )}
    >
      {children}
    </h3>
  );
}

export function CardContent({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cn("p-6", className)}>{children}</div>;
}

export function CardFooter({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "px-6 py-4 border-t border-[#2a2a2a] bg-[#151515]",
        className
      )}
    >
      {children}
    </div>
  );
}
