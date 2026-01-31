"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { SelectionPanel } from "@/components/dashboard/scoring/selection-panel"
import { Button } from "@/components/ui/button"
import { Loader2, Zap, Info } from "lucide-react"
import { scoringApi, BatchTokenEstimateResponse } from "@/lib/api-client"
import { useToast } from "@/components/ui/use-toast"
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"

export default function ScorePage() {
    const router = useRouter()
    const { toast } = useToast()

    const [selectedResumeIds, setSelectedResumeIds] = useState<string[]>([])
    const [selectedJdIds, setSelectedJdIds] = useState<string[]>([])
    const [isScoring, setIsScoring] = useState(false)

    // Estimate state
    const [estimate, setEstimate] = useState<{ details: BatchTokenEstimateResponse, loading: boolean } | null>(null)

    // Fetch estimate when selections change
    useEffect(() => {
        const fetchEstimate = async () => {
            if (selectedResumeIds.length === 0 || selectedJdIds.length === 0) {
                setEstimate(null)
                return
            }

            try {
                setEstimate(prev => prev ? { ...prev, loading: true } : { details: { total_tokens: 0, resume_count: 0, jd_count: 0, resume_tokens_sum: 0, jd_tokens_sum: 0, overhead_tokens: 0 }, loading: true })
                const res = await scoringApi.estimateBatch(selectedResumeIds, selectedJdIds)
                setEstimate({ details: res, loading: false })
            } catch (error) {
                console.error("Failed to estimate tokens", error)
                setEstimate(null)
            }
        }

        // Debounce
        const timeout = setTimeout(fetchEstimate, 500)
        return () => clearTimeout(timeout)
    }, [selectedResumeIds, selectedJdIds])

    const handleStartScoring = async () => {
        if (selectedResumeIds.length === 0 || selectedJdIds.length === 0) {
            toast({
                title: "Selection Required",
                description: "Please select at least one Resume and one Job Description.",
                variant: "destructive"
            })
            return
        }

        try {
            setIsScoring(true)
            await scoringApi.batchScore(selectedResumeIds, selectedJdIds)

            toast({
                title: "Scoring Started",
                description: "Your batch scoring job has been queued successfully."
            })

            // Redirect to history
            router.push("/dashboard/history")
        } catch (error) {
            console.error(error)
            toast({
                title: "Scoring Failed",
                description: "Failed to start batch scoring. Please try again.",
                variant: "destructive"
            })
        } finally {
            setIsScoring(false)
        }
    }

    return (
        <div className="flex flex-col h-[calc(100vh-6rem)] gap-4">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Score Resumes</h1>
                    <p className="text-muted-foreground">
                        Select resumes and job descriptions to compare them.
                    </p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex flex-col items-end mr-2">
                        <div className="text-sm text-muted-foreground hidden md:block">
                            {selectedResumeIds.length} Resumes x {selectedJdIds.length} JDs = {selectedResumeIds.length * selectedJdIds.length} Combinations
                        </div>
                        {selectedResumeIds.length > 0 && selectedJdIds.length > 0 && (
                            <div className="text-xs font-medium text-blue-600 flex items-center gap-1">
                                {estimate?.loading ? (
                                    <Loader2 className="h-3 w-3 animate-spin mr-1" />
                                ) : (
                                    <>
                                        <span>~{estimate?.details?.total_tokens.toLocaleString()} Tokens</span>
                                        <TooltipProvider delayDuration={0}>
                                            <Tooltip>
                                                <TooltipTrigger>
                                                    <Info className="h-3 w-3 text-muted-foreground cursor-help" />
                                                </TooltipTrigger>
                                                <TooltipContent align="end" className="w-[300px] p-4 text-xs">
                                                    <div className="space-y-2">
                                                        <h4 className="font-semibold border-b pb-1 mb-2">Token Estimation Breakdown</h4>

                                                        <div className="flex justify-between">
                                                            <span>Resume Content:</span>
                                                            <span className="font-mono text-muted-foreground">
                                                                {estimate?.details?.resume_tokens_sum.toLocaleString()} Tok × {estimate?.details?.jd_count} JDs
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span>JD Content:</span>
                                                            <span className="font-mono text-muted-foreground">
                                                                {estimate?.details?.jd_tokens_sum.toLocaleString()} Tok × {estimate?.details?.resume_count} Resumes
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between border-b pb-2">
                                                            <span>Prompt Overhead:</span>
                                                            <span className="font-mono text-muted-foreground">
                                                                +{estimate?.details?.overhead_tokens.toLocaleString()}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between font-bold pt-1">
                                                            <span>Total Estimated:</span>
                                                            <span className="text-blue-500">
                                                                {estimate?.details?.total_tokens.toLocaleString()}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </TooltipContent>
                                            </Tooltip>
                                        </TooltipProvider>
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                    <Button
                        size="lg"
                        onClick={handleStartScoring}
                        disabled={isScoring || selectedResumeIds.length === 0 || selectedJdIds.length === 0}
                        className="bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 transition-all shadow-md hover:shadow-lg"
                    >
                        {isScoring ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Scoring...
                            </>
                        ) : (
                            <>
                                <Zap className="mr-2 h-4 w-4 fill-current" />
                                Start Scoring
                            </>
                        )}
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1 min-h-0">
                <div className="h-full min-h-0">
                    <SelectionPanel
                        type="resume"
                        selectedIds={selectedResumeIds}
                        onSelectionChange={setSelectedResumeIds}
                    />
                </div>
                <div className="h-full min-h-0">
                    <SelectionPanel
                        type="jd"
                        selectedIds={selectedJdIds}
                        onSelectionChange={setSelectedJdIds}
                    />
                </div>
            </div>
        </div>
    )
}
