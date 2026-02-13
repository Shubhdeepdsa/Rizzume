'use client'

import { useState, useEffect, useMemo, useCallback } from 'react'
import {
    Dialog, DialogContent, DialogHeader, DialogTitle,
    DialogFooter, DialogDescription
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import {
    Collapsible, CollapsibleContent, CollapsibleTrigger
} from '@/components/ui/collapsible'
import { toast } from 'sonner'
import {
    ScoringConfig, ScoringConfigInput,
    scoringConfigApi
} from '@/lib/api-client'
import {
    AlertTriangle, ChevronDown, RotateCcw, Scale, Settings2, Sparkles
} from 'lucide-react'

interface ScoringConfigDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    config?: ScoringConfig | null // null = create mode
    onSaved?: (config: ScoringConfig) => void
}

const CATEGORIES = [
    { key: 'education_weight', label: 'Education', color: 'hsl(210, 70%, 55%)' },
    { key: 'experience_weight', label: 'Experience', color: 'hsl(150, 60%, 45%)' },
    { key: 'technical_weight', label: 'Technical Skills', color: 'hsl(280, 60%, 55%)' },
    { key: 'soft_skills_weight', label: 'Soft Skills', color: 'hsl(30, 80%, 55%)' },
] as const

type WeightKey = typeof CATEGORIES[number]['key']

export function ScoringConfigDialog({
    open, onOpenChange, config, onSaved
}: ScoringConfigDialogProps) {
    const isEditing = !!config

    // Form state
    const [name, setName] = useState('')
    const [weights, setWeights] = useState<Record<WeightKey, number>>({
        education_weight: 25,
        experience_weight: 25,
        technical_weight: 25,
        soft_skills_weight: 25,
    })
    const [mandatoryWeight, setMandatoryWeight] = useState(2.0)
    const [optionalWeight, setOptionalWeight] = useState(1.0)
    const [capWeight, setCapWeight] = useState(0.5)
    const [isDefault, setIsDefault] = useState(false)
    const [advancedOpen, setAdvancedOpen] = useState(false)
    const [saving, setSaving] = useState(false)

    // Populate form when editing
    useEffect(() => {
        if (config) {
            setName(config.name)
            setWeights({
                education_weight: config.education_weight,
                experience_weight: config.experience_weight,
                technical_weight: config.technical_weight,
                soft_skills_weight: config.soft_skills_weight,
            })
            setMandatoryWeight(config.mandatory_question_weight)
            setOptionalWeight(config.optional_question_weight)
            setCapWeight(config.mandatory_cap_weight)
            setIsDefault(config.is_default)
        } else {
            // Reset for create mode
            setName('')
            setWeights({ education_weight: 25, experience_weight: 25, technical_weight: 25, soft_skills_weight: 25 })
            setMandatoryWeight(2.0)
            setOptionalWeight(1.0)
            setCapWeight(0.5)
            setIsDefault(false)
            setAdvancedOpen(false)
        }
    }, [config, open])

    // Computed values
    const total = useMemo(
        () => Object.values(weights).reduce((a, b) => a + b, 0),
        [weights]
    )
    const isValid = total === 100 && name.trim().length > 0
    const isShared = isEditing && config && (config.usage_count ?? 0) > 1

    // Handlers
    const handleWeightChange = useCallback((key: WeightKey, value: number) => {
        setWeights(prev => ({ ...prev, [key]: value }))
    }, [])

    const handleNormalize = useCallback(() => {
        const keys = Object.keys(weights) as WeightKey[]
        const nonZeroKeys = keys.filter(k => weights[k] > 0)

        if (nonZeroKeys.length === 0) {
            // All zero — set equal
            const each = Math.floor(100 / keys.length)
            const remainder = 100 - each * keys.length
            const newWeights = { ...weights }
            keys.forEach((k, i) => {
                newWeights[k] = each + (i === keys.length - 1 ? remainder : 0)
            })
            setWeights(newWeights)
            return
        }

        // Remainder allocation: scale non-zero keys proportionally
        const currentTotal = nonZeroKeys.reduce((a, k) => a + weights[k], 0)
        const newWeights = { ...weights }
        let allocated = 0

        nonZeroKeys.forEach((k, i) => {
            if (i === nonZeroKeys.length - 1) {
                // Last gets remainder
                newWeights[k] = 100 - allocated
            } else {
                newWeights[k] = Math.floor((weights[k] / currentTotal) * 100)
                allocated += newWeights[k]
            }
        })

        // Zero out the zero keys
        keys.filter(k => weights[k] === 0).forEach(k => { newWeights[k] = 0 })

        setWeights(newWeights)
    }, [weights])

    const handleResetEqual = useCallback(() => {
        setWeights({ education_weight: 25, experience_weight: 25, technical_weight: 25, soft_skills_weight: 25 })
    }, [])

    const handleSave = async () => {
        if (!isValid) return
        setSaving(true)

        try {
            const payload: ScoringConfigInput = {
                name: name.trim(),
                ...weights,
                mandatory_question_weight: mandatoryWeight,
                optional_question_weight: optionalWeight,
                mandatory_cap_weight: capWeight,
                is_default: isDefault,
            }

            let saved: ScoringConfig
            if (isEditing && config) {
                saved = await scoringConfigApi.update(config.id, payload)
                toast.success('Configuration updated')
            } else {
                saved = await scoringConfigApi.create(payload)
                toast.success('Configuration created')
            }

            onSaved?.(saved)
            onOpenChange(false)
        } catch (error: any) {
            toast.error(error?.response?.data?.detail || 'Failed to save configuration')
        } finally {
            setSaving(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[520px] max-h-[85vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Settings2 className="h-5 w-5 text-primary" />
                        {isEditing ? 'Edit Configuration' : 'New Scoring Configuration'}
                    </DialogTitle>
                    <DialogDescription>
                        Customize how resume scores are calculated by adjusting category weights.
                    </DialogDescription>
                </DialogHeader>

                {/* Shared config warning */}
                {isShared && (
                    <div className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm">
                        <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
                        <div>
                            <p className="font-medium text-amber-600 dark:text-amber-400">Shared Configuration</p>
                            <p className="text-muted-foreground">
                                This config is used by {config!.usage_count} JDs. Changes will affect all of them.
                            </p>
                        </div>
                    </div>
                )}

                <div className="space-y-5 py-2">
                    {/* Name */}
                    <div className="space-y-2">
                        <Label htmlFor="config-name">Configuration Name</Label>
                        <Input
                            id="config-name"
                            placeholder="e.g., Technical Heavy, Entry-Level..."
                            value={name}
                            onChange={e => setName(e.target.value)}
                        />
                    </div>

                    <Separator />

                    {/* Category Weights */}
                    <div className="space-y-1">
                        <div className="flex items-center justify-between">
                            <Label className="text-base">Category Weights</Label>
                            <div className="flex items-center gap-1.5">
                                <Badge
                                    variant={total === 100 ? 'default' : 'destructive'}
                                    className="tabular-nums font-mono text-xs px-2"
                                >
                                    {total}%
                                </Badge>
                                {total === 100 && (
                                    <span className="text-xs text-green-500">✓</span>
                                )}
                            </div>
                        </div>
                        <p className="text-xs text-muted-foreground mb-3">
                            Adjust how much each category contributes to the final score. Must sum to 100%.
                        </p>

                        <div className="space-y-4">
                            {CATEGORIES.map(({ key, label, color }) => (
                                <div key={key} className="space-y-1.5">
                                    <div className="flex items-center justify-between">
                                        <Label className="text-sm flex items-center gap-2">
                                            <span
                                                className="w-2.5 h-2.5 rounded-full inline-block"
                                                style={{ backgroundColor: color }}
                                            />
                                            {label}
                                        </Label>
                                        <span className="text-sm font-mono tabular-nums text-muted-foreground w-10 text-right">
                                            {weights[key]}%
                                        </span>
                                    </div>
                                    <Slider
                                        value={[weights[key]]}
                                        onValueChange={([v]) => handleWeightChange(key, v)}
                                        min={0}
                                        max={100}
                                        step={1}
                                        className="**:data-[slot=slider-range]:transition-all"
                                    />
                                </div>
                            ))}
                        </div>

                        {/* Normalize / Reset buttons */}
                        <div className="flex gap-2 mt-3">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleNormalize}
                                disabled={total === 100}
                                className="gap-1.5"
                            >
                                <Scale className="h-3.5 w-3.5" />
                                Normalize
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleResetEqual}
                                className="gap-1.5"
                            >
                                <RotateCcw className="h-3.5 w-3.5" />
                                Reset to Equal
                            </Button>
                        </div>
                    </div>

                    <Separator />

                    {/* Advanced Controls */}
                    <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
                        <CollapsibleTrigger asChild>
                            <Button variant="ghost" size="sm" className="w-full justify-between gap-2 px-2">
                                <span className="flex items-center gap-2 text-sm">
                                    <Sparkles className="h-4 w-4" />
                                    Advanced Scoring Parameters
                                </span>
                                <ChevronDown className={`h-4 w-4 transition-transform ${advancedOpen ? 'rotate-180' : ''}`} />
                            </Button>
                        </CollapsibleTrigger>
                        <CollapsibleContent className="space-y-4 pt-3">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="mandatory-w" className="text-xs">Mandatory Question Weight</Label>
                                    <Input
                                        id="mandatory-w"
                                        type="number"
                                        step={0.1}
                                        min={0}
                                        value={mandatoryWeight}
                                        onChange={e => setMandatoryWeight(parseFloat(e.target.value) || 0)}
                                        className="h-8 text-sm"
                                    />
                                    <p className="text-[10px] text-muted-foreground">
                                        Multiplier for mandatory questions (default: 2.0)
                                    </p>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="optional-w" className="text-xs">Optional Question Weight</Label>
                                    <Input
                                        id="optional-w"
                                        type="number"
                                        step={0.1}
                                        min={0}
                                        value={optionalWeight}
                                        onChange={e => setOptionalWeight(parseFloat(e.target.value) || 0)}
                                        className="h-8 text-sm"
                                    />
                                    <p className="text-[10px] text-muted-foreground">
                                        Multiplier for optional questions (default: 1.0)
                                    </p>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="cap-w" className="text-xs">Mandatory Cap Weight</Label>
                                <div className="flex items-center gap-3">
                                    <Slider
                                        value={[capWeight * 100]}
                                        onValueChange={([v]) => setCapWeight(v / 100)}
                                        min={0}
                                        max={100}
                                        step={5}
                                        className="flex-1"
                                    />
                                    <span className="text-sm font-mono tabular-nums w-12 text-right">
                                        {(capWeight * 100).toFixed(0)}%
                                    </span>
                                </div>
                                <p className="text-[10px] text-muted-foreground">
                                    Score penalty when mandatory question avg &lt; 5.0 (default: 50%)
                                </p>
                            </div>
                        </CollapsibleContent>
                    </Collapsible>

                    <Separator />

                    {/* Default toggle */}
                    <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                            <Label className="text-sm">Set as Default</Label>
                            <p className="text-xs text-muted-foreground">
                                Automatically use for new JDs
                            </p>
                        </div>
                        <Switch checked={isDefault} onCheckedChange={setIsDefault} />
                    </div>
                </div>

                <DialogFooter className="gap-2 sm:gap-0">
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        Cancel
                    </Button>
                    <Button onClick={handleSave} disabled={!isValid || saving}>
                        {saving ? 'Saving...' : isEditing ? 'Update' : 'Create'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
