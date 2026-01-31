"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { scoringApi, ScoringRecord } from "@/lib/api-client"
import { Loader2, ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"

export default function ScoreDetailPage() {
    const { id } = useParams()
    const [record, setRecord] = useState<ScoringRecord | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (id) {
            fetchDetail(id as string)
        }
    }, [id])

    const fetchDetail = async (recordId: string) => {
        try {
            setLoading(true)
            const data = await scoringApi.getDetail(recordId)
            setRecord(data)
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

    const result = record.result || {}
    const questions = (result.questions || {}) as Record<string, any[]>

    return (
        <div className="space-y-6 max-w-5xl mx-auto">
            <div className="flex items-center space-x-4">
                <Link href="/dashboard/history">
                    <Button variant="ghost" size="icon"><ArrowLeft className="h-4 w-4" /></Button>
                </Link>
                <div>
                    <h1 className="text-2xl font-bold">Scoring Analysis</h1>
                    <p className="text-muted-foreground">
                        {record.expand?.resume?.name} vs {record.expand?.jd?.role_name}
                    </p>
                </div>
                <div className="ml-auto">
                    <Badge className="text-lg px-4 py-1">
                        Score: {record.score.toFixed(1)} / 10
                    </Badge>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Resume Details</CardTitle>
                    </CardHeader>
                    <CardContent className="text-sm">
                        <p><strong>Name:</strong> {record.expand?.resume?.name}</p>
                        <p><strong>Token Estimate:</strong> {result.resume_token_estimate}</p>
                        <div className="mt-4">
                            <h4 className="font-semibold mb-2">Extracted Text Preview</h4>
                            <ScrollArea className="h-[200px] w-full rounded-md border p-4">
                                <pre className="text-xs whitespace-pre-wrap">{result.resume_text}</pre>
                            </ScrollArea>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader>
                        <CardTitle>Job Description Details</CardTitle>
                    </CardHeader>
                    <CardContent className="text-sm">
                        <p><strong>Role:</strong> {record.expand?.jd?.role_name}</p>
                        <p><strong>Company:</strong> {record.expand?.jd?.company_name}</p>
                        <p><strong>Token Estimate:</strong> {result.jd_token_estimate}</p>
                        <div className="mt-4">
                            <h4 className="font-semibold mb-2">Original Text Preview</h4>
                            <ScrollArea className="h-[200px] w-full rounded-md border p-4">
                                <pre className="text-xs whitespace-pre-wrap">{result.jd_text}</pre>
                            </ScrollArea>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Detailed Breakdown */}
            <div className="space-y-6">
                <h2 className="text-xl font-semibold">Category Breakdown</h2>

                {Object.entries(questions).map(([category, qList]) => (
                    <Card key={category}>
                        <CardHeader className="capitalize">
                            <CardTitle>{category.replace('_', ' ')}</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            {qList.map((q, idx) => (
                                <div key={idx} className="border-b pb-4 last:border-0 last:pb-0">
                                    <div className="flex justify-between items-start mb-2">
                                        <h3 className="font-medium text-base">{q.question}</h3>
                                        <Badge variant={q.score > 0 ? "default" : "destructive"}>
                                            {q.score} / 10
                                        </Badge>
                                    </div>
                                    <p className="text-sm text-muted-foreground mb-2"><strong>Answer:</strong> {q.answer}</p>
                                    <p className="text-sm"><strong>Reasoning:</strong> {q.reasoning}</p>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    )
}
