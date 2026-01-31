"use client"

import { usePathname } from "next/navigation"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Menu, FileText, Upload, History, LayoutDashboard } from "lucide-react"
import { useState } from "react"

interface SidebarProps extends React.HTMLAttributes<HTMLDivElement> { }

export function DashboardSidebar({ className }: SidebarProps) {
    const pathname = usePathname()
    const [open, setOpen] = useState(false)

    const routes = [
        {
            label: "Dashboard",
            icon: LayoutDashboard,
            href: "/dashboard",
            active: pathname === "/dashboard",
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
            <div className="px-3 py-2">
                <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight">
                    Rizzume
                </h2>
                <div className="flex flex-col space-y-2 ">
                    {routes.map((route) => (
                        <Link
                            key={route.href}
                            href={route.href}
                            onClick={() => setOpen(false)}
                            className="my-1"
                        >
                            <Button
                                variant={route.active ? "secondary" : "ghost"}
                                className="w-full justify-start "
                            >
                                <route.icon className="mr-2 h-4 w-4" />
                                {route.label}
                            </Button>
                        </Link>
                    ))}
                </div>
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
                <SheetContent side="left" className="p-0 bg-background">
                    <SidebarContent />
                </SheetContent>
            </Sheet>

            {/* Desktop Sidebar */}
            <div className={cn("hidden md:flex h-screen w-64 flex-col fixed left-0 top-0 border-r bg-background z-30", className)}>
                <SidebarContent />
            </div>
        </>
    )
}
