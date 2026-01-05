"use client"

import { useState } from "react"
import type { QuestionItem } from "@/lib/api"
import { Card } from "@/components/ui/card"
import { ResumeViewer } from "./resume-viewer"

interface QuestionDetailPanelProps {
  question: QuestionItem
  resumeText?: string
}

export function QuestionDetailPanel({ question, resumeText }: QuestionDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<"reasoning" | "evidence" | "resume">("reasoning")

  const getAnswerColor = (answer: string) => {
    if (answer.toLowerCase().startsWith("yes")) {
      return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
    } else if (answer.toLowerCase().startsWith("no") || answer.toLowerCase().includes("no evidence")) {
      return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
    } else {
      return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="sticky top-0 bg-background/95 backdrop-blur-sm z-10 pb-4 -mx-6 px-6 pt-4 border-b border-border/50">
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-foreground text-balance leading-snug pr-4">{question.question}</h2>

          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-3 py-1.5 rounded-full text-xs font-medium bg-muted/50 text-muted-foreground">
              {question.category.replace(/_/g, " ")}
            </span>
            <span className={`px-3 py-1.5 rounded-full text-xs font-medium ${getAnswerColor(question.answer)}`}>
              {question.answer}
            </span>
            <span className="ml-auto text-base font-bold text-foreground">{question.score.toFixed(1)} / 10</span>
          </div>
        </div>
      </div>

      <div className="flex gap-1 border-b border-border/50">
        {(["reasoning", "evidence", "resume"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab === "reasoning" ? "Reasoning" : tab === "evidence" ? "Evidence from resume" : "Resume highlights"}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="space-y-4 pb-8">
        {activeTab === "reasoning" ? (
          <>
            <Card className="p-6 border border-border/50 bg-card/50">
              <p className="text-foreground leading-relaxed">{question.reasoning}</p>
            </Card>
            <div className="text-xs text-muted-foreground">
              Evidence coverage: {question.evidence_chars.toLocaleString()} characters
            </div>
          </>
        ) : activeTab === "evidence" ? (
          <div className="space-y-3">
            {question.retrieved_chunks.length > 0 ? (
              question.retrieved_chunks.map((chunk, idx) => (
                <Card key={idx} className="p-4 border border-border/50 bg-card/50">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                      Chunk #{chunk.chunk_id} — Similarity: {(chunk.similarity * 100).toFixed(1)}%
                    </h4>
                  </div>
                  <p className="text-sm text-foreground font-mono leading-relaxed bg-muted/30 p-3 rounded border border-border/50 whitespace-pre-wrap break-words">
                    {chunk.text}
                  </p>
                </Card>
              ))
            ) : (
              <Card className="p-6 border border-border/50 bg-card/50">
                <p className="text-sm text-muted-foreground text-center">No evidence chunks available</p>
              </Card>
            )}
          </div>
        ) : resumeText ? (
          <ResumeViewer resumeText={resumeText} chunks={question.retrieved_chunks} />
        ) : (
          <Card className="p-6 border border-border/50 bg-card/50">
            <p className="text-sm text-muted-foreground text-center">Resume text not available</p>
          </Card>
        )}
      </div>
    </div>
  )
}
