import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  Shield,
  BarChart3,
  FileCheck,
  MessageSquare,
  Users,
  Menu,
  X,
  Bell,
  Settings
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navigationItems = [
  {
    name: "Dashboard",
    href: "/",
    icon: BarChart3,
  },
  {
    name: "Content Verification",
    href: "/verification",
    icon: FileCheck,
  },
  {
    name: "Social Media Monitor",
    href: "/social-monitor",
    icon: MessageSquare,
  },
  {
    name: "Advisor Verification",
    href: "/advisor-verification",
    icon: Users,
  },
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background flex">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-foreground/20 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-72 transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
          "bg-gradient-to-b from-primary to-primary-dark shadow-2xl",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center gap-3 px-6 border-b border-white/20">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm shadow-lg">
              <Shield className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">SEBI Monitor</h1>
              <p className="text-xs text-white/80">Regulatory Dashboard</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-2 px-4 py-6">
            {navigationItems.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200 hover:bg-white/20 hover:shadow-lg hover:scale-[1.02] active:scale-[0.98]",
                    isActive
                      ? "bg-white/25 text-white shadow-lg backdrop-blur-sm border border-white/30"
                      : "text-white/90 hover:text-white"
                  )
                }
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </NavLink>
            ))}
          </nav>

          {/* User section */}
          <div className="border-t border-white/20 p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="h-8 w-8 rounded-full bg-white/25 flex items-center justify-center backdrop-blur-sm border border-white/30">
                <span className="text-sm font-medium text-white">A</span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-white">Admin User</p>
                <p className="text-xs text-white/70">Compliance Officer</p>
              </div>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              className="w-full justify-start gap-2 border-white/50 text-white bg-white/10 hover:bg-white/20 hover:text-white hover:border-white/70 transition-all duration-200"
            >
              <Settings className="h-4 w-4" />
              Settings
            </Button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1">
        {/* Mobile menu button - only shown on mobile */}
        <div className="lg:hidden sticky top-0 z-10 flex h-12 items-center gap-4 border-b border-border bg-gradient-to-r from-background to-primary/5 backdrop-blur-md px-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(true)}
            className="hover:bg-primary/10 hover:text-primary"
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div className="flex-1" />
          <Button variant="ghost" size="sm" className="relative hover:bg-primary/10 hover:text-primary">
            <Bell className="h-5 w-5" />
            <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-gradient-to-r from-error to-warning shadow-lg animate-pulse"></span>
          </Button>
        </div>

        {/* Page content */}
        <main className="p-6 bg-gradient-to-br from-background via-background to-primary/5 min-h-screen">
          <Outlet />
        </main>
      </div>
    </div>
  );
}