"use client"

import { Button } from "@/components/ui/button"

interface LandingHeroProps {
  onGetStarted: () => void
}

export function LandingHero({ onGetStarted }: LandingHeroProps) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-gradient-to-br from-background via-background to-secondary/5">
      <div className="flex flex-col items-center gap-8 max-w-2xl text-center animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div className="space-y-2">
          <p className="text-sm font-semibold tracking-widest text-muted-foreground uppercase">Rizzume</p>
          <h1 className="text-5xl md:text-6xl font-bold text-foreground leading-tight text-balance">
            Resume analysis powered by you.
          </h1>
        </div>

        <p className="text-lg text-muted-foreground leading-relaxed max-w-xl text-balance">
          Upload your resume and JD, and get transparent, evidence-backed insights into how well your experience matches
          the role.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 pt-4">
          <Button
            onClick={onGetStarted}
            size="lg"
            className="rounded-full px-8 h-12 text-base font-medium shadow-lg hover:shadow-xl transition-all hover:scale-105"
          >
            Get started
          </Button>
          <Button variant="outline" size="lg" className="rounded-full px-8 h-12 text-base font-medium bg-transparent">
            How it works
          </Button>
        </div>

        <div className="pt-8 text-xs text-muted-foreground">
          <p>Your documents are processed securely. We only use them to generate your analysis.</p>
        </div>
      </div>
    </div>
  )
}
