"use client"

import { usePathname } from "next/navigation"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Menu, FileText, Upload, History, LayoutDashboard, LogOut, Home, Command } from "lucide-react"
import { useState } from "react"
import { useAuth } from "@/context/auth-context"

import { ThemeToggle } from "@/components/theme-toggle"
interface SidebarProps extends React.HTMLAttributes<HTMLDivElement> { }

export function DashboardSidebar({ className }: SidebarProps) {
    const pathname = usePathname()
    const [open, setOpen] = useState(false)
    const { user, logout } = useAuth()

    const routes = [
        {
            label: "Dashboard",
            icon: LayoutDashboard,
            href: "/dashboard",
            active: pathname === "/dashboard",
        },
        {
            label: "Score",
            icon: History,
            href: "/dashboard/score",
            active: pathname.startsWith("/dashboard/score"),
        },
        {
            label: "Resumes",
            icon: FileText,
            href: "/dashboard/resumes",
            active: pathname === "/dashboard/resumes",
        },
        {
            label: "Job Descriptions",
            icon: Upload,
            href: "/dashboard/jds",
            active: pathname === "/dashboard/jds",
        },
        {
            label: "Score History",
            icon: History,
            href: "/dashboard/history",
            active: pathname.startsWith("/dashboard/history"),
        },
    ]

    const SidebarContent = () => (
        <div className="space-y-4 py-4 h-full flex flex-col">
            <div className="px-3 py-2 flex-1">
                <Link href="/" className="flex items-center pl-2 mb-14" onClick={() => setOpen(false)}>
                    <div className="flex items-center">
                        <Command className="mr-2 " />
                        <h2 className="text-2xl font-bold tracking-tight">
                            Rizzume
                        </h2>
                    </div>
                </Link>
                <div className="flex flex-col space-y-1">
                    {routes.map((route) => (
                        <Link
                            key={route.href}
                            href={route.href}
                            onClick={() => setOpen(false)}
                        >
                            <Button
                                variant={route.active ? "secondary" : "ghost"}
                                className={cn("w-full justify-start", route.active && "bg-secondary")}
                            >
                                <route.icon className="mr-2 h-4 w-4" />
                                {route.label}
                            </Button>
                        </Link>
                    ))}
                </div>
            </div>
            <div className="mt-auto px-3 py-2 border-t">
                <div className="flex items-center gap-2 px-2 py-2 mb-2">
                    <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <span className="text-xs font-medium text-primary">
                            {user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || "U"}
                        </span>
                    </div>
                    <div className="flex flex-col">
                        <span className="text-sm font-medium">{user?.name || "User"}</span>
                        <span className="text-xs text-muted-foreground truncate w-32">
                            {user?.email}
                        </span>
                    </div>
                    <div className="ml-auto">
                        <ThemeToggle />
                    </div>
                </div>
                <Link href="/home" onClick={() => setOpen(false)}>
                    <Button variant="ghost" className="w-full justify-start text-muted-foreground hover:text-foreground">
                        <Home className="mr-2 h-4 w-4" />
                        Back to Home
                    </Button>
                </Link>
                <Button
                    variant="ghost"
                    className="w-full justify-start text-destructive hover:text-destructive hover:bg-destructive/10"
                    onClick={logout}
                >
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                </Button>
            </div>
        </div>
    )

    return (
        <>
            {/* Mobile Sidebar */}
            <Sheet open={open} onOpenChange={setOpen}>
                <SheetTrigger asChild>
                    <Button variant="ghost" className="md:hidden fixed left-4 top-4 z-40">
                        <Menu className="h-5 w-5" />
                    </Button>
                </SheetTrigger>
                <SheetContent side="left" className="p-0 bg-background w-72">
                    <SidebarContent />
                </SheetContent>
            </Sheet>

            {/* Desktop Sidebar */}
            <div className={cn("hidden md:flex h-screen w-72 flex-col fixed left-0 top-0 border-r bg-background z-30", className)}>
                <SidebarContent />
            </div>
        </>
    )
}
