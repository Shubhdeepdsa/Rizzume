"use client"

import { useState, useMemo } from "react"
import type { ScoreResult } from "@/lib/api"
import type { ScoringConfig } from "@/lib/api-client"
import { QuestionFilters } from "./question-filters"
import { QuestionCard } from "./question-card"
import { QuestionDetailPanel } from "./question-detail-panel"
import { ActionPlanCard } from "./dashboard/scoring/action-plan-card"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from "recharts"
import {
  Tooltip as TooltipUI,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { Badge } from "@/components/ui/badge"
import { Settings2, Info } from "lucide-react"

interface AnalysisLayoutProps {
  result: ScoreResult
  resumeText?: string
  scoringConfig?: ScoringConfig | null
}

export function AnalysisLayout({ result, resumeText, scoringConfig }: AnalysisLayoutProps) {
  const [selectedFilter, setSelectedFilter] = useState("all")
  const [selectedQuestionId, setSelectedQuestionId] = useState(0)

  const categories = useMemo(() => {
    console.log("DEBUG: AnalysisLayout received result:", result)
    const stats = {
      education: result.questions.filter((q) => q.category === "education").length,
      experience: result.questions.filter((q) => q.category === "experience").length,
      technical_skills: result.questions.filter((q) => q.category === "technical_skills").length,
      soft_skills: result.questions.filter((q) => q.category === "soft_skills").length,
      mandatory: result.questions.filter((q) => q.is_mandatory).length,
    }
    console.log("DEBUG: Computed categories stats:", stats)
    return stats
  }, [result.questions])

  const filteredQuestions = useMemo(() => {
    let filtered = []
    if (selectedFilter === "all") filtered = result.questions
    else if (selectedFilter === "mandatory") filtered = result.questions.filter((q) => q.is_mandatory)
    else filtered = result.questions.filter((q) => q.category === selectedFilter)

    console.log(`DEBUG: Filtered questions (filter=${selectedFilter}):`, filtered)
    return filtered
  }, [result.questions, selectedFilter])

  const chartData = useMemo(() => {
    const categoryDefs = [
      { key: "education", displayName: "Education", weightKey: "education_weight" as const, color: "hsl(210, 70%, 55%)" },
      { key: "experience", displayName: "Experience", weightKey: "experience_weight" as const, color: "hsl(150, 60%, 45%)" },
      { key: "technical_skills", displayName: "Technical Skills", weightKey: "technical_weight" as const, color: "hsl(280, 60%, 55%)" },
      { key: "soft_skills", displayName: "Soft Skills", weightKey: "soft_skills_weight" as const, color: "hsl(30, 80%, 55%)" },
    ]

    return categoryDefs.map(({ key, displayName, weightKey, color }) => {
      const categoryQuestions = result.questions.filter((q) => q.category === key)
      const mandatoryQuestions = categoryQuestions.filter((q) => q.is_mandatory)

      const overallScore = categoryQuestions.length > 0
        ? categoryQuestions.reduce((sum, q) => sum + q.score, 0) / categoryQuestions.length
        : 0

      const mandatoryScore = mandatoryQuestions.length > 0
        ? mandatoryQuestions.reduce((sum, q) => sum + q.score, 0) / mandatoryQuestions.length
        : 0

      const weight = scoringConfig ? (scoringConfig as any)[weightKey] ?? 25 : 25

      return {
        category: displayName,
        overallScore: Math.round(overallScore * 10) / 10,
        mandatoryScore: Math.round(mandatoryScore * 10) / 10,
        questionCount: categoryQuestions.length,
        mandatoryCount: mandatoryQuestions.length,
        weight,
        color,
      }
    }).filter(item => item.questionCount > 0) // Only show categories with questions
  }, [result.questions, scoringConfig])

  const mandatoryInsights = useMemo(() => {
    const allMandatory = result.questions.filter((q) => q.is_mandatory)
    const passed = allMandatory.filter((q) => q.score >= 7)
    const failed = allMandatory.filter((q) => q.score < 7)

    return {
      total: allMandatory.length,
      passed: passed.length,
      failed: failed.length,
      passRate: allMandatory.length > 0 ? Math.round((passed.length / allMandatory.length) * 100) : 0,
    }
  }, [result.questions])

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
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-foreground">Category-wise Performance</h2>
                  <div className="flex gap-4 text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded bg-primary"></div>
                      <span className="text-muted-foreground">Overall Score</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded bg-amber-500"></div>
                      <span className="text-muted-foreground">Mandatory Score</span>
                    </div>
                    {scoringConfig && (
                      <div className="flex items-center gap-2">
                        <Settings2 className="w-3 h-3 text-muted-foreground" />
                        <span className="text-muted-foreground">{scoringConfig.name}</span>
                      </div>
                    )}
                  </div>
                </div>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} barGap={4}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                      <XAxis
                        dataKey="category"
                        stroke="var(--color-muted-foreground)"
                        fontSize={12}
                        angle={-15}
                        textAnchor="end"
                        height={60}
                      />
                      <YAxis domain={[0, 10]} stroke="var(--color-muted-foreground)" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "var(--color-card)",
                          border: "1px solid var(--color-border)",
                          borderRadius: "8px",
                        }}
                        formatter={(value: number, name: string, props: any) => {
                          const displayName = name === 'overallScore' ? 'Overall' : 'Mandatory'
                          const weight = props.payload?.weight
                          const weightLabel = scoringConfig ? ` (Weight: ${weight}%)` : ''
                          return [`${value} / 10${weightLabel}`, displayName]
                        }}
                        labelFormatter={(label) => `${label}`}
                      />
                      <Bar dataKey="overallScore" fill="var(--color-primary)" radius={[8, 8, 0, 0]}>
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-overall-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                      <Bar dataKey="mandatoryScore" fill="rgb(245, 158, 11)" radius={[8, 8, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                {scoringConfig ? (
                  <div className="flex items-center gap-4 mt-2">
                    <div className="w-16 h-16 flex-shrink-0">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={chartData.map(d => ({ name: d.category, value: d.weight, color: d.color }))}
                            cx="50%"
                            cy="50%"
                            innerRadius={16}
                            outerRadius={28}
                            paddingAngle={3}
                            dataKey="value"
                            strokeWidth={0}
                          >
                            {chartData.map((entry, index) => (
                              <Cell key={`pie-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="flex flex-wrap gap-x-4 gap-y-1">
                      {chartData.map((d, i) => (
                        <div key={i} className="flex items-center gap-1.5 text-xs">
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                          <span className="text-muted-foreground">{d.category}</span>
                          <span className="font-semibold text-foreground">{d.weight}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Showing {chartData.length} categories with {result.questions.length} total criteria
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-4">
              {/* Overall Score Card */}
              <div className="bg-card border border-border/50 rounded-lg p-6 flex flex-col justify-center">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-muted-foreground mb-2">Overall Score</p>
                  {scoringConfig && (
                    <TooltipProvider>
                      <TooltipUI>
                        <TooltipTrigger>
                          <Badge variant="outline" className="gap-1 text-xs cursor-help">
                            <Settings2 className="h-3 w-3" />
                            {scoringConfig.name}
                          </Badge>
                        </TooltipTrigger>
                        <TooltipContent side="left" className="max-w-xs bg-background border-2">
                          <div className="space-y-2 text-xs">
                            <p className="font-semibold text-foreground">Scoring Configuration</p>
                            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-foreground">
                              <span className="text-muted-foreground">Education</span>
                              <span className="font-mono">{scoringConfig.education_weight}%</span>
                              <span className="text-muted-foreground">Experience</span>
                              <span className="font-mono">{scoringConfig.experience_weight}%</span>
                              <span className="text-muted-foreground">Technical</span>
                              <span className="font-mono">{scoringConfig.technical_weight}%</span>
                              <span className="text-muted-foreground">Soft Skills</span>
                              <span className="font-mono">{scoringConfig.soft_skills_weight}%</span>
                            </div>
                            <div className="border-t border-border pt-1 mt-1 grid grid-cols-2 text-foreground gap-x-4 gap-y-1">
                              <span className="text-muted-foreground">Mandatory Wt</span>
                              <span className="font-mono">{scoringConfig.mandatory_question_weight}×</span>
                              <span className="text-muted-foreground">Optional Wt</span>
                              <span className="font-mono">{scoringConfig.optional_question_weight}×</span>
                              <span className="text-muted-foreground">Cap Penalty</span>
                              <span className="font-mono">{(scoringConfig.mandatory_cap_weight * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                        </TooltipContent>
                      </TooltipUI>
                    </TooltipProvider>
                  )}
                </div>
                <p className="text-5xl font-bold text-primary">{result.average_score.toFixed(1)}</p>
                <p className="text-xs text-muted-foreground mt-2">out of 10</p>
              </div>

              {/* Mandatory Insights Card */}
              <div className="bg-card border border-border/50 rounded-lg p-6">
                <h3 className="text-sm font-semibold text-foreground mb-4">Mandatory Requirements</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-muted-foreground">Total</span>
                    <span className="text-sm font-semibold text-foreground">{mandatoryInsights.total}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-muted-foreground">Passed (≥7)</span>
                    <span className="text-sm font-semibold text-green-600">{mandatoryInsights.passed}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-muted-foreground">Failed (&lt;7)</span>
                    <span className="text-sm font-semibold text-red-600">{mandatoryInsights.failed}</span>
                  </div>
                  <div className="pt-3 border-t border-border">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-medium text-foreground">Pass Rate</span>
                      <span className={`text-lg font-bold ${mandatoryInsights.passRate >= 70 ? 'text-green-600' : mandatoryInsights.passRate >= 50 ? 'text-amber-600' : 'text-red-600'}`}>
                        {mandatoryInsights.passRate}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>



        {/* Action Plan Section */}
        {
          result.action_plan && (
            <div className="mb-12">
              <ActionPlanCard plan={result.action_plan} />
            </div>
          )
        }

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
            {selectedQuestion ? (
              <QuestionDetailPanel question={selectedQuestion} resumeText={resumeText} />
            ) : (
              <div className="flex h-full items-center justify-center p-8 text-muted-foreground border rounded-lg bg-card/50 border-dashed">
                <p>Select a question to view details</p>
              </div>
            )}
          </div>
        </div>
      </div >
    </div >
  )
}
