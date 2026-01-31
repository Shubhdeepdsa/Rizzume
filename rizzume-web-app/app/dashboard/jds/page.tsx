"use client"

import { useEffect, useState } from "react"
import { JobDescription, jdsApi } from "@/lib/api-client"
import { JDTable } from "@/components/dashboard/jd-table"
import { JDUploadDialog } from "@/components/dashboard/jd-upload-dialog"
import { Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function JDsPage() {
    const [jds, setJds] = useState<JobDescription[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const fetchJds = async () => {
        try {
            setLoading(true)
            const data = await jdsApi.getAll()
            setJds(data)
            setError(null)
        } catch (err) {
            setError("Failed to load job descriptions.")
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchJds()
    }, [])

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Job Descriptions</h1>
                    <p className="text-muted-foreground">
                        Manage your job descriptions and usage.
                    </p>
                </div>
                <JDUploadDialog onSuccess={fetchJds} />
            </div>

            {loading ? (
                <div className="flex h-64 items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
            ) : error ? (
                <div className="flex h-64 flex-col items-center justify-center space-y-4 text-center">
                    <p className="text-destructive">{error}</p>
                    <Button variant="outline" onClick={fetchJds}>
                        Try Again
                    </Button>
                </div>
            ) : (
                <JDTable data={jds} onRefresh={fetchJds} />
            )}
        </div>
    )
}
