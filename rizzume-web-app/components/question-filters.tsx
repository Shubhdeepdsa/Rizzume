"use client"

interface QuestionFiltersProps {
  categories: {
    education: number
    experience: number
    technical_skills: number
    soft_skills: number
    mandatory: number
  }
  selected: string
  onSelect: (category: string) => void
}

export function QuestionFilters({ categories, selected, onSelect }: QuestionFiltersProps) {
  const filters = [
    { id: "all", label: "All", count: categories.education + categories.experience + categories.technical_skills + categories.soft_skills },
    { id: "mandatory", label: "Required", count: categories.mandatory, highlight: true },
    { id: "education", label: "Education", count: categories.education },
    { id: "experience", label: "Experience", count: categories.experience },
    { id: "technical_skills", label: "Technical skills", count: categories.technical_skills },
    { id: "soft_skills", label: "Soft skills", count: categories.soft_skills },
  ]

  return (
    <div className="flex flex-wrap gap-2">
      {filters.map((filter) => (
        <button
          key={filter.id}
          onClick={() => onSelect(filter.id)}
          className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
            selected === filter.id
              ? filter.highlight
                ? "bg-red-500 text-white shadow-md"
                : "bg-primary text-primary-foreground shadow-md"
              : filter.highlight
                ? "bg-red-100 text-red-700 hover:bg-red-200 border border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800"
                : "bg-muted/50 text-foreground hover:bg-muted border border-border/50"
          }`}
        >
          {filter.label}
          {filter.count > 0 && <span className="ml-2 text-xs opacity-75">· {filter.count}</span>}
        </button>
      ))}
    </div>
  )
}
