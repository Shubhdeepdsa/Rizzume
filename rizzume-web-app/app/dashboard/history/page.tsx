"use client"

import { useEffect, useState, useRef } from "react"
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
    const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null)

    // Ref to track if component is mounted to prevent state updates after unmount
    // Ref to track if component is mounted to prevent state updates after unmount
    const isMountedRef = useRef(true)

    useEffect(() => {
        isMountedRef.current = true
        return () => {
            isMountedRef.current = false
        }
    }, [])

    // Cleanup polling on changes
    useEffect(() => {
        return () => {
            if (pollInterval) clearTimeout(pollInterval)
        }
    }, [pollInterval])

    const [filters, setFilters] = useState({
        resume_id: "all",
        jd_id: "all"
    })

    useEffect(() => {
        fetchInitialData()
    }, [])

    useEffect(() => {
        fetchHistory(false)
        // Cleanup existing poll on filter change
        if (pollInterval) {
            clearTimeout(pollInterval)
            setPollInterval(null)
        }
    }, [filters])

    const fetchInitialData = async () => {
        try {
            const [rData, jData] = await Promise.all([
                resumesApi.getAll(),
                jdsApi.getAll()
            ])
            if (isMountedRef.current) {
                setResumes(rData)
                setJds(jData)
            }
        } catch (e) {
            console.error("Failed to load filters data", e)
        }
    }

    const fetchHistory = async (isBackground: boolean = false) => {
        console.log(`[History] Fetching data. Background: ${isBackground}, Mounted: ${isMountedRef.current}`)
        if (!isMountedRef.current) return;

        try {
            if (!isBackground) setLoading(true)

            const historyData = await scoringApi.getResults({
                resume_id: filters.resume_id === "all" ? undefined : filters.resume_id,
                jd_id: filters.jd_id === "all" ? undefined : filters.jd_id
            })

            if (!isMountedRef.current) return;

            setData(historyData)
            setError(null)

            // Smart Polling Logic
            // Check if any job is queued or processing
            const hasPendingJobs = historyData.some(
                item => item.status === 'queued' || item.status === 'processing'
            )

            if (hasPendingJobs) {
                const timeoutId = setTimeout(() => {
                    fetchHistory(true)
                }, 5000) // Poll every 5 seconds
                setPollInterval(timeoutId)
            } else {
                setPollInterval(null)
            }

        } catch (err) {
            console.error("[History] Error fetching:", err)
            if (!isMountedRef.current) return;
            setError("Failed to load scoring history.")
        } finally {
            if (isMountedRef.current && !isBackground) {
                console.log("[History] Loading finished")
                setLoading(false)
            }
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
                    <Button variant="outline" onClick={() => fetchHistory(false)}>
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
