"use client"

import type { QuestionItem } from "@/lib/api"
import { Card } from "@/components/ui/card"

interface QuestionCardProps {
  question: QuestionItem
  index: number
  isSelected: boolean
  onClick: () => void
}

export function QuestionCard({ question, index, isSelected, onClick }: QuestionCardProps) {
  const getAnswerColor = (answer: string) => {
    if (answer.toLowerCase().startsWith("yes")) {
      return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
    } else if (answer.toLowerCase().startsWith("no") || answer.toLowerCase().includes("no evidence")) {
      return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
    } else {
      return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
    }
  }

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      education: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
      experience: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
      technical_skills: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400",
      soft_skills: "bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400",
    }
    return colors[category] || colors.experience
  }

  return (
    <Card
      onClick={onClick}
      className={`p-4 cursor-pointer transition-all border ${
        isSelected
          ? "border-primary/50 bg-primary/5 shadow-md"
          : "border-border/50 hover:border-primary/30 hover:bg-card/50"
      }`}
    >
      <div className="space-y-3">
        {/* Header pills */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getCategoryColor(question.category)}`}>
            {question.category.replace(/_/g, " ")}
          </span>
          <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getAnswerColor(question.answer)}`}>
            {question.answer}
          </span>
          <span className="ml-auto text-sm font-semibold text-foreground">{question.score.toFixed(1)} / 10</span>
        </div>

        {/* Question */}
        <p className="text-sm text-foreground line-clamp-2 font-medium">{question.question}</p>

        {/* Reasoning preview */}
        <p className="text-xs text-muted-foreground line-clamp-1">{question.reasoning}</p>
      </div>
    </Card>
  )
}
