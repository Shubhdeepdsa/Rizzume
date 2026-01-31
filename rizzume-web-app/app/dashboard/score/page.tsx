"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { SelectionPanel } from "@/components/dashboard/scoring/selection-panel"
import { Button } from "@/components/ui/button"
import { Loader2, Zap } from "lucide-react"
import { scoringApi } from "@/lib/api-client"
import { useToast } from "@/components/ui/use-toast"

export default function ScorePage() {
    const router = useRouter()
    const { toast } = useToast()

    const [selectedResumeIds, setSelectedResumeIds] = useState<string[]>([])
    const [selectedJdIds, setSelectedJdIds] = useState<string[]>([])
    const [isScoring, setIsScoring] = useState(false)

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
                    <div className="text-sm text-muted-foreground hidden md:block">
                        {selectedResumeIds.length} Resumes x {selectedJdIds.length} JDs = {selectedResumeIds.length * selectedJdIds.length} Combinations
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
