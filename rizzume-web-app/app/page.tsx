"use client"

import { useState } from "react"
import { LandingHero } from "@/components/landing-hero"
import { DataInputStep } from "@/components/data-input-step"
import { LoadingState } from "@/components/loading-state"
import { AnalysisLayout } from "@/components/analysis-layout"
import { ThemeToggle } from "@/components/theme-toggle"
import { scoreResumeApi, type ScoreResponse } from "@/lib/api"

type AppStep = "landing" | "input" | "loading" | "analysis"

interface AppState {
  step: AppStep
  scoreResult?: ScoreResponse
}

export default function App() {
  const [appState, setAppState] = useState<AppState>({ step: "landing" })
  const [isLoading, setIsLoading] = useState(false)

  const handleGetStarted = () => {
    setAppState({ step: "input" })
  }

  const handleAnalyze = async (resumeFile: File | null, resumeText: string, jdFile: File | null, jdText: string) => {
    setIsLoading(true)
    setAppState({ step: "loading" })

    try {
      const response = await scoreResumeApi({
        resumeFile: resumeFile || undefined,
        jdFile: jdFile || undefined,
      })

      setAppState({
        step: "analysis",
        scoreResult: response,
      })
    } catch (error) {
      console.error("Analysis error:", error)
      setAppState({ step: "input" })
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-background text-foreground min-h-screen">
      {/* Theme toggle */}
      <div className="fixed top-4 right-4 z-50">
        <ThemeToggle />
      </div>

      {/* Main content */}
      {appState.step === "landing" && <LandingHero onGetStarted={handleGetStarted} />}

      {appState.step === "input" && <DataInputStep onAnalyze={handleAnalyze} isLoading={isLoading} />}

      {appState.step === "loading" && <LoadingState />}

      {appState.step === "analysis" && appState.scoreResult && (
        <AnalysisLayout result={appState.scoreResult.result} resumeText={appState.scoreResult.resume_text} />
      )}
    </div>
  )
}
