
import { DashboardSidebar } from "@/components/dashboard/sidebar"

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <div className="min-h-screen bg-background flex">
            {/* Sidebar */}
            <DashboardSidebar />

            {/* Main Content */}
            <main className="flex-1 md:ml-64 p-8 pt-16 md:pt-8 min-h-screen transition-all duration-300 ease-in-out">
                {children}
            </main>
        </div>
    )
}
