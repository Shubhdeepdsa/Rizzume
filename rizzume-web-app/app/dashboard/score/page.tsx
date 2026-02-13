"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { SelectionPanel } from "@/components/dashboard/scoring/selection-panel"
import { Button } from "@/components/ui/button"
import { Loader2, Zap, Info, AlertTriangle, TrendingDown } from "lucide-react"
import { scoringApi, BatchTokenEstimateResponse } from "@/lib/api-client"
import { useToast } from "@/components/ui/use-toast"
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import { Badge } from "@/components/ui/badge"

type Strategy = "rag" | "full"

export default function ScorePage() {
    const router = useRouter()
    const { toast } = useToast()

    const [selectedResumeIds, setSelectedResumeIds] = useState<string[]>([])
    const [selectedJdIds, setSelectedJdIds] = useState<string[]>([])
    const [isScoring, setIsScoring] = useState(false)

    // Strategy toggle
    const [strategy, setStrategy] = useState<Strategy>("rag")

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
                setEstimate(prev => prev
                    ? { ...prev, loading: true }
                    : {
                        details: {
                            resume_count: 0, jd_count: 0, total_combinations: 0, total_questions: 0,
                            rag_strategy: { name: "RAG (Chunks)", total_tokens: 0, tokens_per_question: 0, context_tokens: 0, context_type: "" },
                            full_resume_strategy: { name: "Full Resume", total_tokens: 0, tokens_per_question: 0, context_tokens: 0, context_type: "" },
                            savings_tokens: 0, savings_percentage: 0, warnings: []
                        },
                        loading: true
                    }
                )
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

    const activeStrategy = estimate?.details
        ? (strategy === "rag" ? estimate.details.rag_strategy : estimate.details.full_resume_strategy)
        : null

    const hasWarnings = (estimate?.details?.warnings?.length ?? 0) > 0

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
                    <div className="flex flex-col items-end mr-2 gap-1">
                        <div className="text-sm text-muted-foreground hidden md:block">
                            {selectedResumeIds.length} Resumes x {selectedJdIds.length} JDs = {selectedResumeIds.length * selectedJdIds.length} Combinations
                        </div>
                        {selectedResumeIds.length > 0 && selectedJdIds.length > 0 && (
                            <div className="flex items-center gap-2">
                                {/* Strategy Toggle */}
                                <div className="flex items-center bg-muted rounded-lg p-0.5 text-xs">
                                    <button
                                        onClick={() => setStrategy("rag")}
                                        className={`px-2 py-1 rounded-md transition-all font-medium ${strategy === "rag"
                                            ? "bg-background shadow-sm text-green-600"
                                            : "text-muted-foreground hover:text-foreground"
                                            }`}
                                    >
                                        RAG
                                    </button>
                                    <button
                                        onClick={() => setStrategy("full")}
                                        className={`px-2 py-1 rounded-md transition-all font-medium ${strategy === "full"
                                            ? "bg-background shadow-sm text-orange-600"
                                            : "text-muted-foreground hover:text-foreground"
                                            }`}
                                    >
                                        Full Resume
                                    </button>
                                </div>

                                {/* Token Count Display */}
                                <div className="text-xs font-medium flex items-center gap-1">
                                    {estimate?.loading ? (
                                        <Loader2 className="h-3 w-3 animate-spin mr-1" />
                                    ) : (
                                        <>
                                            <span className={strategy === "rag" ? "text-green-600" : "text-orange-600"}>
                                                ~{activeStrategy?.total_tokens.toLocaleString()} Tokens
                                            </span>

                                            {/* Savings Badge (only shown for RAG) */}
                                            {strategy === "rag" && estimate?.details && estimate.details.savings_percentage > 0 && (
                                                <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-green-500/30 text-green-600 bg-green-50 dark:bg-green-950/20">
                                                    <TrendingDown className="h-2.5 w-2.5 mr-0.5" />
                                                    {estimate.details.savings_percentage}% saved
                                                </Badge>
                                            )}

                                            {/* Warnings Icon */}
                                            {hasWarnings && (
                                                <TooltipProvider delayDuration={0}>
                                                    <Tooltip>
                                                        <TooltipTrigger>
                                                            <AlertTriangle className="h-3.5 w-3.5 text-amber-500 cursor-help" />
                                                        </TooltipTrigger>
                                                        <TooltipContent align="end" className="w-[280px] p-3 text-xs">
                                                            <h4 className="font-semibold mb-1">⚠️ Warnings</h4>
                                                            <ul className="space-y-1 text-muted-foreground">
                                                                {estimate?.details?.warnings.map((w, i) => (
                                                                    <li key={i}>• {w}</li>
                                                                ))}
                                                            </ul>
                                                        </TooltipContent>
                                                    </Tooltip>
                                                </TooltipProvider>
                                            )}

                                            {/* Info Breakdown Tooltip */}
                                            <TooltipProvider delayDuration={0}>
                                                <Tooltip>
                                                    <TooltipTrigger>
                                                        <Info className="h-3 w-3 text-muted-foreground cursor-help" />
                                                    </TooltipTrigger>
                                                    <TooltipContent align="end" className="w-[340px] p-4 text-xs bg-background border-2">
                                                        <div className="space-y-3">
                                                            <h4 className="font-semibold text-primary border-b pb-1">Token Estimation Breakdown</h4>

                                                            {/* Summary */}
                                                            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-muted-foreground">
                                                                <span>Total Questions:</span>
                                                                <span className="font-mono text-right">{estimate?.details?.total_questions}</span>
                                                                <span>Combinations:</span>
                                                                <span className="font-mono text-right">{estimate?.details?.total_combinations}</span>
                                                            </div>

                                                            {/* Strategy Comparison */}
                                                            <div className="border rounded-md overflow-hidden">
                                                                <div className="grid grid-cols-3 bg-muted/50 px-2 py-1 font-semibold">
                                                                    <span></span>
                                                                    <span className="text-center text-green-600">RAG</span>
                                                                    <span className="text-center text-orange-600">Full</span>
                                                                </div>
                                                                <div className="grid grid-cols-3 px-2 py-1 border-t text-muted-foreground">
                                                                    <span>Context/Q</span>
                                                                    <span className="text-center font-mono">{estimate?.details?.rag_strategy.context_tokens}</span>
                                                                    <span className="text-center font-mono">{estimate?.details?.full_resume_strategy.context_tokens}</span>
                                                                </div>
                                                                <div className="grid grid-cols-3 px-2 py-1 border-t text-muted-foreground">
                                                                    <span>Tokens/Q</span>
                                                                    <span className="text-center font-mono">{estimate?.details?.rag_strategy.tokens_per_question}</span>
                                                                    <span className="text-center font-mono">{estimate?.details?.full_resume_strategy.tokens_per_question}</span>
                                                                </div>
                                                                <div className="grid grid-cols-3 px-2 py-1 border-t font-semibold">
                                                                    <span>Total</span>
                                                                    <span className="text-center font-mono text-green-600">
                                                                        {estimate?.details?.rag_strategy.total_tokens.toLocaleString()}
                                                                    </span>
                                                                    <span className="text-center font-mono text-orange-600">
                                                                        {estimate?.details?.full_resume_strategy.total_tokens.toLocaleString()}
                                                                    </span>
                                                                </div>
                                                            </div>

                                                            {/* Savings Summary */}
                                                            {estimate?.details && estimate.details.savings_tokens > 0 && (
                                                                <div className="bg-green-50 dark:bg-green-950/20 rounded-md px-2 py-1.5 text-green-700 dark:text-green-400 flex items-center gap-1.5">
                                                                    <TrendingDown className="h-3.5 w-3.5" />
                                                                    <span>
                                                                        RAG saves <strong>{estimate.details.savings_tokens.toLocaleString()}</strong> tokens ({estimate.details.savings_percentage}%)
                                                                    </span>
                                                                </div>
                                                            )}

                                                            {/* Context Type Explanation */}
                                                            <div className="text-[10px] text-muted-foreground/70 pt-1 border-t">
                                                                <p><strong>RAG:</strong> {estimate?.details?.rag_strategy.context_type}</p>
                                                                <p><strong>Full:</strong> {estimate?.details?.full_resume_strategy.context_type}</p>
                                                            </div>
                                                        </div>
                                                    </TooltipContent>
                                                </Tooltip>
                                            </TooltipProvider>
                                        </>
                                    )}
                                </div>
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
