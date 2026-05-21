"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/auth-store";
import { cn } from "@/lib/utils";
import {
  Home,
  ScrollText,
  Trophy,
  Users,
  Settings,
  LogOut,
  Zap,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { href: "/dashboard", icon: Home, label: "Главная" },
  { href: "/dashboard/scrolls", icon: ScrollText, label: "Мои свитки" },
  { href: "/dashboard/achievements", icon: Trophy, label: "Достижения" },
  { href: "/dashboard/parent", icon: Users, label: "Родителям" },
];

export function DashboardSidebar() {
  const pathname = usePathname();
  const { user, logout, studentProfile } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);

  const beltColors = {
    white: "bg-gray-100 text-gray-800",
    yellow: "bg-yellow-400 text-yellow-900",
    green: "bg-primary text-white",
    black: "bg-gray-900 text-white",
  };

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-border bg-card transition-all duration-300",
        collapsed ? "w-20" : "w-64"
      )}
    >
      {/* Collapse button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-6 z-10 flex h-6 w-6 items-center justify-center rounded-full border border-border bg-card shadow-sm hover:bg-muted"
      >
        {collapsed ? (
          <ChevronRight className="h-4 w-4" />
        ) : (
          <ChevronLeft className="h-4 w-4" />
        )}
      </button>

      {/* Logo */}
      <div className="flex h-16 items-center border-b border-border px-4">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-jade-dark">
            <Zap className="h-5 w-5 text-white" />
          </div>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="font-bold text-foreground"
            >
              Мастер Кват
            </motion.span>
          )}
        </Link>
      </div>

      {/* User info */}
      {user && (
        <div className={cn("border-b border-border p-4", collapsed && "px-2")}>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <span className="text-lg font-bold">
                {user.name.charAt(0).toUpperCase()}
              </span>
            </div>
            {!collapsed && (
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-foreground">{user.name}</p>
                {studentProfile && (
                  <span
                    className={cn(
                      "inline-block rounded-full px-2 py-0.5 text-xs font-medium",
                      beltColors[studentProfile.beltLevel]
                    )}
                  >
                    {studentProfile.beltLevel === "white" && "Белый пояс"}
                    {studentProfile.beltLevel === "yellow" && "Жёлтый пояс"}
                    {studentProfile.beltLevel === "green" && "Зелёный пояс"}
                    {studentProfile.beltLevel === "black" && "Чёрный пояс"}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors",
                    isActive
                      ? "bg-primary text-white"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    collapsed && "justify-center px-2"
                  )}
                >
                  <item.icon className="h-5 w-5 shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Bottom actions */}
      <div className="border-t border-border p-4">
        <div className={cn("space-y-2", collapsed && "flex flex-col items-center")}>
          <Link
            href="/dashboard/settings"
            className={cn(
              "flex items-center gap-3 rounded-xl px-3 py-2.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
              collapsed && "justify-center px-2"
            )}
          >
            <Settings className="h-5 w-5 shrink-0" />
            {!collapsed && <span>Настройки</span>}
          </Link>
          <Button
            variant="ghost"
            onClick={logout}
            className={cn(
              "w-full justify-start gap-3 text-muted-foreground hover:bg-destructive/10 hover:text-destructive",
              collapsed && "justify-center px-2"
            )}
          >
            <LogOut className="h-5 w-5 shrink-0" />
            {!collapsed && <span>Выйти</span>}
          </Button>
        </div>
      </div>
    </aside>
  );
}
