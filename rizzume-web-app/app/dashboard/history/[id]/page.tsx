"use client"

import { useEffect, useState, useRef } from "react"
import { useParams } from "next/navigation"
import { scoringApi, ScoringRecord, scoringConfigApi, ScoringConfig } from "@/lib/api-client"
import { Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { AnalysisLayout } from "@/components/analysis-layout"
import type { ScoreResult } from "@/lib/api"

export default function ScoreDetailPage() {
    const { id } = useParams()
    const [record, setRecord] = useState<ScoringRecord | null>(null)
    const [scoringConfig, setScoringConfig] = useState<ScoringConfig | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const fetchedRef = useRef(false) // Guard for double fetch

    useEffect(() => {
        if (id && !fetchedRef.current) {
            fetchedRef.current = true
            fetchDetail(id as string)
        }
    }, [id])

    const fetchDetail = async (recordId: string) => {
        try {
            setLoading(true)
            const data = await scoringApi.getDetail(recordId)
            console.log("DEBUG: Raw API Data:", data)
            setRecord(data)

            // Fetch scoring config if JD has one assigned
            const configId = data.expand?.jd?.scoring_config
            if (configId) {
                try {
                    const cfg = await scoringConfigApi.get(configId)
                    setScoringConfig(cfg)
                } catch (e) {
                    console.warn("Could not fetch scoring config", e)
                }
            }
        } catch (e) {
            console.error(e)
            setError("Failed to load details.")
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return <div className="flex h-screen items-center justify-center"><Loader2 className="h-8 w-8 animate-spin" /></div>
    }

    if (error || !record) {
        return (
            <div className="p-8">
                <p className="text-destructive mb-4">{error || "Record not found"}</p>
                <Link href="/dashboard/history"><Button>Back to History</Button></Link>
            </div>
        )
    }

    // Safe normalization to prevent runtime errors if result is malformed or from legacy data
    const normalizeResult = (rawResult: any): ScoreResult => {
        console.log("DEBUG: rawResult input to normalize:", rawResult)
        if (!rawResult) {
            return { questions: [], average_score: 0 }
        }

        let questions: any[] = []

        // Handle case where questions might be undefined
        if (!rawResult.questions) {
            questions = []
        }
        // Handle legacy case where questions might be an object grouped by category
        else if (typeof rawResult.questions === 'object' && !Array.isArray(rawResult.questions)) {
            // Flatten the object values into a single array
            questions = Object.values(rawResult.questions).flat()
        }
        // Handle correct case where questions is already an array
        else if (Array.isArray(rawResult.questions)) {
            questions = rawResult.questions
        }

        console.log("DEBUG: Normalized questions:", questions)

        return {
            average_score: typeof rawResult.average_score === 'number' ? rawResult.average_score : 0,
            questions: questions,
            action_plan: rawResult.action_plan
        }
    }

    const result = normalizeResult(record.analysis || record.result)
    // Prefer the top-level record.score — it's always up-to-date after recalculation
    if (typeof record.score === 'number' && record.score > 0) {
        result.average_score = record.score
    }
    console.log("DEBUG: Final result prop passed to AnalysisLayout:", result)

    return (
        <AnalysisLayout
            result={result}
            resumeText={record.expand?.resume?.original_text}
            scoringConfig={scoringConfig}
        />
    )
}
