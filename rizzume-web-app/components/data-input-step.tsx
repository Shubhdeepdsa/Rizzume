"use client"

import { useEffect, useState } from "react"
import { DocumentInputCard } from "./document-input-card"
import { TokenEstimatePanel } from "./token-estimate-panel"
import { Button } from "@/components/ui/button"
import { estimateTokensApi, type TokenEstimate } from "@/lib/api"
import { AlertCircle } from "lucide-react"

interface DataInputStepProps {
  onAnalyze: (resumeFile: File | null, resumeText: string, jdFile: File | null, jdText: string) => Promise<void>
  isLoading: boolean
}

export function DataInputStep({ onAnalyze, isLoading }: DataInputStepProps) {
  const [resumeMode, setResumeMode] = useState<"file" | "text">("file")
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [resumeText, setResumeText] = useState("")

  const [jdMode, setJdMode] = useState<"file" | "text">("file")
  const [jdFile, setJdFile] = useState<File | null>(null)
  const [jdText, setJdText] = useState("")

  const [estimate, setEstimate] = useState<TokenEstimate | null>(null)
  const [estimateLoading, setEstimateLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const hasResumeData = resumeMode === "file" ? !!resumeFile : !!resumeText.trim()
  const hasJdData = jdMode === "file" ? !!jdFile : !!jdText.trim()
  const canAnalyze = hasResumeData && hasJdData && !isLoading

  // Auto-estimate tokens when both documents are ready
  useEffect(() => {
    const timeoutId = setTimeout(async () => {
      if (hasResumeData && hasJdData) {
        try {
          setEstimateLoading(true)
          setError(null)
          // For now, only file mode is wired up
          if (resumeMode === "file" && jdMode === "file") {
            const result = await estimateTokensApi({
              jdFile: jdFile || undefined,
              resumeFile: resumeFile || undefined,
            })
            setEstimate(result)
          }
        } catch (err) {
          console.error("Token estimate error:", err)
          setError("Failed to estimate tokens. Please try again.")
        } finally {
          setEstimateLoading(false)
        }
      }
    }, 500)

    return () => clearTimeout(timeoutId)
  }, [hasResumeData, hasJdData, resumeFile, jdFile, resumeMode, jdMode])

  const handleAnalyze = async () => {
    try {
      setError(null)
      await onAnalyze(resumeFile, resumeText, jdFile, jdText)
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
    }
  }

  return (
    <div className="min-h-screen py-12 px-4 bg-background">
      <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Step 1</p>
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mt-2">Provide your documents</h2>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-muted-foreground">1 / 2</p>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="flex items-center gap-3 p-4 rounded-lg bg-destructive/10 border border-destructive/20">
            <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        {/* Document cards */}
        <div className="grid md:grid-cols-2 gap-6">
          <DocumentInputCard
            title="Resume"
            description="Upload your resume file or paste the text."
            placeholder="Paste your resume text here…"
            type="resume"
            mode={resumeMode}
            onModeChange={setResumeMode}
            file={resumeFile}
            onFileChange={setResumeFile}
            text={resumeText}
            onTextChange={setResumeText}
          />

          <DocumentInputCard
            title="Job Description"
            description="Upload the job description or paste it here."
            placeholder="Paste the job description here…"
            type="jd"
            mode={jdMode}
            onModeChange={setJdMode}
            file={jdFile}
            onFileChange={setJdFile}
            text={jdText}
            onTextChange={setJdText}
          />
        </div>

        {/* Token estimate */}
        {(estimate || estimateLoading) && <TokenEstimatePanel estimate={estimate} isLoading={estimateLoading} />}

        {/* Bottom actions */}
        <div className="flex items-center justify-between pt-4 border-t border-border/50">
          <p className="text-sm text-muted-foreground max-w-md">
            Your documents are processed securely. We only use them to generate your analysis.
          </p>
          <Button onClick={handleAnalyze} disabled={!canAnalyze} size="lg" className="rounded-full px-8 h-12">
            {isLoading ? "Analyzing…" : "Analyze my resume"}
          </Button>
        </div>
      </div>
    </div>
  )
}
