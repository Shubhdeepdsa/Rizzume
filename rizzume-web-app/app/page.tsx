"use client"

import { useRouter } from "next/navigation"
import { LandingHero } from "@/components/landing-hero"
import { ThemeToggle } from "@/components/theme-toggle"
import { useAuth } from "@/context/auth-context"

export default function App() {
  const router = useRouter()
  const { isAuthenticated } = useAuth()

  const handleGetStarted = () => {
    if (isAuthenticated) {
      router.push("/home")
    } else {
      router.push("/auth?view=login")
    }
  }

  return (
    <div className="bg-background text-foreground min-h-screen">
      {/* Theme toggle */}
      <div className="fixed top-4 right-4 z-50">
        <ThemeToggle />
      </div>

      {/* Main content */}
      <LandingHero onGetStarted={handleGetStarted} />
    </div>
  )
}
