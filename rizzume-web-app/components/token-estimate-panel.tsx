"use client"

import { Card } from "@/components/ui/card"
import type { TokenEstimate } from "@/lib/api"
import { Loader2 } from "lucide-react"

interface TokenEstimatePanelProps {
  estimate: TokenEstimate | null
  isLoading: boolean
}

export function TokenEstimatePanel({ estimate, isLoading }: TokenEstimatePanelProps) {
  if (!estimate && !isLoading) return null

  return (
    <Card className="p-6 border border-border/50 bg-card/50">
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-foreground">Token estimate</h3>
          {isLoading && <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />}
        </div>

        {estimate && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">JD Length</p>
              <p className="text-lg font-semibold text-foreground">{estimate.jd_text_length.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">characters</p>
            </div>

            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Resume Length</p>
              <p className="text-lg font-semibold text-foreground">{estimate.resume_text_length.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">characters</p>
            </div>

            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">JD Tokens</p>
              <p className="text-lg font-semibold text-foreground">{estimate.jd_token_estimate.toLocaleString()}</p>
              <div className="w-full bg-muted/30 rounded-full h-1.5">
                <div
                  className="bg-primary h-1.5 rounded-full"
                  style={{
                    width: `${Math.min(
                      (estimate.jd_token_estimate / (estimate.jd_token_estimate + estimate.resume_token_estimate)) *
                        100,
                      100,
                    )}%`,
                  }}
                />
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Resume Tokens</p>
              <p className="text-lg font-semibold text-foreground">{estimate.resume_token_estimate.toLocaleString()}</p>
              <div className="w-full bg-muted/30 rounded-full h-1.5">
                <div
                  className="bg-accent h-1.5 rounded-full"
                  style={{
                    width: `${Math.min(
                      (estimate.resume_token_estimate / (estimate.jd_token_estimate + estimate.resume_token_estimate)) *
                        100,
                      100,
                    )}%`,
                  }}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}
