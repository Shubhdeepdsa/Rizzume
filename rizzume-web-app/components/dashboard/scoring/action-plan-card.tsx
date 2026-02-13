"use client"

import * as React from "react"
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "@/components/ui/collapsible"
import type { ActionPlan } from "@/lib/api"
import { AlertCircle, ChevronsUpDown, Lightbulb, ListChecks } from "lucide-react"

interface ActionPlanCardProps {
    plan?: ActionPlan
}

export function ActionPlanCard({ plan }: ActionPlanCardProps) {
    const [isOpen, setIsOpen] = React.useState(false)

    if (!plan) return null

    // If both lists are empty, we can show a "Review Complete" state or nothing
    if (plan.critical_actions.length === 0 && plan.improvement_suggestions.length === 0) {
        return null
    }

    return (
        <Collapsible
            open={isOpen}
            onOpenChange={setIsOpen}
            className="space-y-4 border rounded-lg p-6 bg-card shadow-sm"
        >
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                    <ListChecks className="h-6 w-6 text-primary" />
                    Action Plan
                </h2>
                <CollapsibleTrigger asChild>
                    <Button variant="ghost" size="sm" className="w-9 p-0">
                        <ChevronsUpDown className="h-4 w-4" />
                        <span className="sr-only">Toggle</span>
                    </Button>
                </CollapsibleTrigger>
            </div>

            <CollapsibleContent className="space-y-6 animate-in slide-in-from-top-2">
                {/* Critical Actions - Red */}
                {plan.critical_actions.length > 0 && (
                    <div className="space-y-3">
                        <h3 className="text-lg font-semibold text-destructive flex items-center gap-2">
                            <AlertCircle className="h-5 w-5" />
                            Resume Blockers - Fix Immediately
                        </h3>
                        <div className="grid gap-3 py-4">
                            <Alert variant="destructive" className=" py-4  bg-destructive/10 border-destructive/20 text-destructive">
                                < AlertCircle className="animate-ping h-4 w-4" />
                                <div className="flex flex-col gap-2">

                                    <AlertTitle className="font-semibold mb-1">Critical Gap</AlertTitle>
                                    {plan.critical_actions.map((action, idx) => (
                                        <div className="border-b border-destructive border-r p-2 rounded-br-sm" key={idx}>
                                            <AlertDescription>{action}</AlertDescription>
                                        </div>
                                    ))}
                                </div>
                            </Alert>
                        </div>
                    </div>
                )
                }

                {/* Improvement Suggestions - Yellow/Amber */}
                {
                    plan.improvement_suggestions.length > 0 && (
                        <div className="space-y-3">
                            <h3 className="text-lg font-semibold text-amber-600 flex items-center gap-2">
                                <Lightbulb className="h-5 w-5" />
                                Missed Opportunities - Add Detail
                            </h3>
                            <div className="border rounded-lg bg-card shadow-sm">
                                <Accordion type="single" collapsible className="w-full">
                                    {plan.improvement_suggestions.map((suggestion, idx) => (
                                        <AccordionItem key={idx} value={`item-${idx}`}>
                                            <AccordionTrigger className="px-4 hover:no-underline hover:bg-muted/50 transition-colors">
                                                <div className="flex items-center gap-2 text-left">
                                                    <span className="h-6 w-6 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center text-xs font-bold shrink-0">
                                                        {idx + 1}
                                                    </span>
                                                    <span className="font-medium text-foreground">Suggestion #{idx + 1}</span>
                                                </div>
                                            </AccordionTrigger>
                                            <AccordionContent className="px-4 pb-4 pt-1 text-muted-foreground">
                                                <div className="pl-8">{suggestion}</div>
                                            </AccordionContent>
                                        </AccordionItem>
                                    ))}
                                </Accordion>
                            </div>
                        </div>
                    )
                }
            </CollapsibleContent>
        </Collapsible >
    )
}
