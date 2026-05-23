"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";
import { DashboardSidebar } from "@/components/dashboard/sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, hasHydrated } = useAuthStore();

  useEffect(() => {
    if (hasHydrated && !isAuthenticated) {
      router.replace("/login");
    }
  }, [hasHydrated, isAuthenticated, router]);

  return (
    <div className="flex min-h-screen bg-background">
      {hasHydrated && isAuthenticated ? <DashboardSidebar /> : null}
      <main className="flex-1 overflow-auto">
        {!hasHydrated && (
          <div className="border-b border-border bg-muted/30 px-4 py-2 text-sm text-muted-foreground">
            Загрузка кабинета…
          </div>
        )}
        {children}
      </main>
    </div>
  );
}
