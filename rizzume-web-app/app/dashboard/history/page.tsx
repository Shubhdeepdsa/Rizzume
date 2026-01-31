"use client"

import { useEffect, useState } from "react"
import {
    ScoringRecord,
    Resume,
    JobDescription,
    scoringApi,
    resumesApi,
    jdsApi
} from "@/lib/api-client"
import { HistoryTable } from "@/components/dashboard/history-table"
import { Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function HistoryPage() {
    const [data, setData] = useState<ScoringRecord[]>([])
    const [resumes, setResumes] = useState<Resume[]>([])
    const [jds, setJds] = useState<JobDescription[]>([])

    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const [filters, setFilters] = useState({
        resume_id: "all",
        jd_id: "all"
    })

    useEffect(() => {
        fetchInitialData()
    }, [])

    useEffect(() => {
        fetchHistory()
    }, [filters])

    const fetchInitialData = async () => {
        try {
            const [rData, jData] = await Promise.all([
                resumesApi.getAll(),
                jdsApi.getAll()
            ])
            setResumes(rData)
            setJds(jData)
        } catch (e) {
            console.error("Failed to load filters data", e)
        }
    }

    const fetchHistory = async () => {
        try {
            setLoading(true)
            const historyData = await scoringApi.getResults({
                resume_id: filters.resume_id === "all" ? undefined : filters.resume_id,
                jd_id: filters.jd_id === "all" ? undefined : filters.jd_id
            })
            setData(historyData)
            setError(null)
        } catch (err) {
            setError("Failed to load scoring history.")
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleFilterChange = (key: string, value: string) => {
        setFilters(prev => ({ ...prev, [key]: value }))
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Score History</h1>
                <p className="text-muted-foreground">
                    View past scoring runs and detailed analysis.
                </p>
            </div>

            {loading && data.length === 0 ? (
                <div className="flex h-64 items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
            ) : error ? (
                <div className="flex h-64 flex-col items-center justify-center space-y-4 text-center">
                    <p className="text-destructive">{error}</p>
                    <Button variant="outline" onClick={fetchHistory}>
                        Try Again
                    </Button>
                </div>
            ) : (
                <HistoryTable
                    data={data}
                    resumes={resumes}
                    jds={jds}
                    filters={filters}
                    onFilterChange={handleFilterChange}
                />
            )}
        </div>
    )
}
