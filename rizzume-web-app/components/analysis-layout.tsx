"use client"

import { useState, useMemo } from "react"
import type { ScoreResult } from "@/lib/api"
import { QuestionFilters } from "./question-filters"
import { QuestionCard } from "./question-card"
import { QuestionDetailPanel } from "./question-detail-panel"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

interface AnalysisLayoutProps {
  result: ScoreResult
  resumeText?: string
}

export function AnalysisLayout({ result, resumeText }: AnalysisLayoutProps) {
  const [selectedFilter, setSelectedFilter] = useState("all")
  const [selectedQuestionId, setSelectedQuestionId] = useState(0)

  const categories = useMemo(() => {
    return {
      education: result.questions.filter((q) => q.category === "education").length,
      experience: result.questions.filter((q) => q.category === "experience").length,
      technical_skills: result.questions.filter((q) => q.category === "technical_skills").length,
      soft_skills: result.questions.filter((q) => q.category === "soft_skills").length,
    }
  }, [result.questions])

  const filteredQuestions = useMemo(() => {
    if (selectedFilter === "all") return result.questions
    return result.questions.filter((q) => q.category === selectedFilter)
  }, [result.questions, selectedFilter])

  const chartData = useMemo(() => {
    return [
      {
        name: "Average",
        score: Math.round(result.average_score * 10) / 10,
      },
    ]
  }, [result.average_score])

  const selectedQuestion = filteredQuestions[selectedQuestionId] || result.questions[0]

  return (
    <div className="min-h-screen py-12 px-4 bg-background">
      <div className="max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
        {/* Header with score */}
        <div className="mb-8 space-y-6">
          <div>
            <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Analysis complete</p>
            <h1 className="text-4xl md:text-5xl font-bold text-foreground mt-2">Your results</h1>
          </div>

          {/* Score visualization */}
          <div className="grid md:grid-cols-3 gap-6">
            <div className="md:col-span-2 bg-card border border-border/50 rounded-lg p-8">
              <div className="space-y-4">
                <h2 className="text-lg font-semibold text-foreground">Average Match Score</h2>
                <div className="h-32">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                      <XAxis dataKey="name" stroke="var(--color-muted-foreground)" />
                      <YAxis domain={[0, 10]} stroke="var(--color-muted-foreground)" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "var(--color-card)",
                          border: "1px solid var(--color-border)",
                          borderRadius: "8px",
                        }}
                        formatter={(value) => `${value} / 10`}
                      />
                      <Bar dataKey="score" fill="var(--color-primary)" radius={[8, 8, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <p className="text-sm text-muted-foreground">Based on {result.questions.length} evaluated criteria</p>
              </div>
            </div>

            <div className="bg-card border border-border/50 rounded-lg p-6 flex flex-col justify-center">
              <p className="text-sm text-muted-foreground mb-2">Overall Score</p>
              <p className="text-5xl font-bold text-primary">{result.average_score.toFixed(1)}</p>
              <p className="text-xs text-muted-foreground mt-2">out of 10</p>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-8">
          <QuestionFilters categories={categories} selected={selectedFilter} onSelect={setSelectedFilter} />
        </div>

        {/* Two-column layout */}
        <div className="grid lg:grid-cols-5 gap-8">
          {/* Left column - Questions list */}
          <div className="lg:col-span-2 space-y-3 max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
            {filteredQuestions.length > 0 ? (
              filteredQuestions.map((question, idx) => (
                <QuestionCard
                  key={idx}
                  question={question}
                  index={idx}
                  isSelected={selectedQuestion === question}
                  onClick={() => setSelectedQuestionId(idx)}
                />
              ))
            ) : (
              <div className="text-center py-8 text-muted-foreground">No questions in this category</div>
            )}
          </div>

          {/* Right column - Detail view */}
          <div className="lg:col-span-3 max-h-[calc(100vh-200px)] overflow-y-auto">
            <QuestionDetailPanel question={selectedQuestion} resumeText={resumeText} />
          </div>
        </div>
      </div>
    </div>
  )
}
