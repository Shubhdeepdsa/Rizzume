"use client"

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { MoreHorizontal, Download, Trash2, FileText, Eye, Filter, Calendar as CalendarIcon, Check, X, Settings2, RefreshCw } from "lucide-react"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command"
import { Calendar } from "@/components/ui/calendar"
import { Input } from "@/components/ui/input"
import { JobDescription, jdsApi, JDTag, jdTagsApi, JDFilter, ScoringConfig, scoringConfigApi } from "@/lib/api-client"
import { format } from "date-fns"
import { useState, useEffect, useCallback } from "react"
import { useToast } from "@/components/ui/use-toast"
import { cn } from "@/lib/utils"
import { ScoringConfigDialog } from "./scoring/scoring-config-dialog"
import { DropdownMenuSeparator } from "@/components/ui/dropdown-menu"
import { toast as sonnerToast } from "sonner"

interface JDTableProps {
    data: JobDescription[]
    onRefresh: () => void
    filters: JDFilter
    onFilterChange: (filters: JDFilter) => void
    availableTags: JDTag[]
    availableCompanies: string[]
}

export function JDTable({ data, onRefresh, filters, onFilterChange, availableTags, availableCompanies }: JDTableProps) {
    const { toast } = useToast()
    const [deletingId, setDeletingId] = useState<string | null>(null)
    const [viewingJD, setViewingJD] = useState<JobDescription | null>(null)
    const [previewUrl, setPreviewUrl] = useState<string | null>(null)
    // Scoring config state
    const [configDialogOpen, setConfigDialogOpen] = useState(false)
    const [editingConfig, setEditingConfig] = useState<ScoringConfig | null>(null)
    const [scoringConfigs, setScoringConfigs] = useState<ScoringConfig[]>([])
    const [assigningJdId, setAssigningJdId] = useState<string | null>(null)

    // Fetch configs list
    const loadConfigs = useCallback(async () => {
        try {
            const configs = await scoringConfigApi.getAll()
            setScoringConfigs(configs)
        } catch (e) {
            console.error("Failed to load scoring configs", e)
        }
    }, [])

    useEffect(() => { loadConfigs() }, [loadConfigs])

    // Handle Preview URL creation/cleanup
    useEffect(() => {
        if (viewingJD) {
            let active = true
            jdsApi.download(viewingJD.id).then(blob => {
                if (active) {
                    const url = URL.createObjectURL(blob)
                    setPreviewUrl(url)
                }
            }).catch(e => console.error("Failed to load preview", e))

            return () => {
                active = false
                if (previewUrl) URL.revokeObjectURL(previewUrl)
                setPreviewUrl(null)
            }
        }
    }, [viewingJD])

    const tagMap = availableTags.reduce((acc, tag) => {
        acc[tag.id] = tag.label
        return acc
    }, {} as Record<string, string>)

    const handleDownload = async (jd: JobDescription) => {
        if (jd.filename) {
            try {
                const blob = await jdsApi.download(jd.id)
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = jd.filename
                document.body.appendChild(a)
                a.click()
                document.body.removeChild(a)
                URL.revokeObjectURL(url)
            } catch (e) {
                console.error("Download failed", e)
            }
        } else {
            // Download text
            jdsApi.downloadText(jd)
        }
    }

    const handleDelete = async (id: string) => {
        try {
            setDeletingId(id)
            await jdsApi.delete(id)
            toast({
                title: "Success",
                description: "Job Description deleted successfully",
            })
            onRefresh()
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to delete Job Description",
                variant: "destructive",
            })
            console.error(error)
        } finally {
            setDeletingId(null)
        }
    }

    const handleAssignConfig = async (jdId: string, configId: string) => {
        try {
            const result = await scoringConfigApi.assignToJd(configId, jdId)
            sonnerToast.success(
                result.affected_count > 0
                    ? `Config assigned. Recalculating ${result.affected_count} scores...`
                    : 'Config assigned'
            )
            onRefresh()
        } catch (e) {
            sonnerToast.error('Failed to assign config')
        }
    }

    const handleRecalculate = async (jdId: string) => {
        try {
            const result = await scoringConfigApi.recalculateJd(jdId)
            sonnerToast.success(
                result.affected_count > 0
                    ? `Recalculating ${result.affected_count} scores...`
                    : 'No completed scores to recalculate'
            )
        } catch (e) {
            sonnerToast.error('Failed to start recalculation')
        }
    }

    // Build config name map
    const configMap = scoringConfigs.reduce((acc, cfg) => {
        acc[cfg.id] = cfg.name
        return acc
    }, {} as Record<string, string>)

    return (
        <>
            <div className="">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Role</TableHead>
                            <TableHead>
                                <Popover>
                                    <PopoverTrigger asChild>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className={cn(
                                                "-ml-3 h-8 data-[state=open]:bg-accent",
                                                filters.company_contains && "text-primary"
                                            )}
                                        >
                                            Company
                                            <Filter className="ml-2 h-4 w-4" />
                                        </Button>
                                    </PopoverTrigger>
                                    <PopoverContent className="w-[200px] p-0" align="start">
                                        <Command>
                                            <CommandInput placeholder="Filter company..." />
                                            <CommandList>
                                                <CommandEmpty>No company found.</CommandEmpty>
                                                <CommandGroup>
                                                    {availableCompanies.map((company) => {
                                                        const isSelected = filters.company_contains === company
                                                        return (
                                                            <CommandItem
                                                                key={company}
                                                                onSelect={() => {
                                                                    onFilterChange({
                                                                        ...filters,
                                                                        company_contains: isSelected ? undefined : company
                                                                    })
                                                                }}
                                                            >
                                                                <div
                                                                    className={cn(
                                                                        "mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                                                                        isSelected
                                                                            ? "bg-primary text-primary-foreground"
                                                                            : "opacity-50 [&_svg]:invisible"
                                                                    )}
                                                                >
                                                                    <Check className="h-4 w-4" />
                                                                </div>
                                                                {company}
                                                            </CommandItem>
                                                        )
                                                    })}
                                                </CommandGroup>
                                                {filters.company_contains && (
                                                    <CommandGroup>
                                                        <CommandItem
                                                            onSelect={() => onFilterChange({ ...filters, company_contains: undefined })}
                                                            className="justify-center text-center"
                                                        >
                                                            Clear Filter
                                                        </CommandItem>
                                                    </CommandGroup>
                                                )}
                                            </CommandList>
                                        </Command>
                                    </PopoverContent>
                                </Popover>
                            </TableHead>
                            <TableHead>
                                <Popover>
                                    <PopoverTrigger asChild>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className={cn(
                                                "-ml-3 h-8 data-[state=open]:bg-accent",
                                                (filters.created_after || filters.created_before) && "text-primary"
                                            )}
                                        >
                                            Date Added
                                            <CalendarIcon className="ml-2 h-4 w-4" />
                                        </Button>
                                    </PopoverTrigger>
                                    <PopoverContent className="w-auto p-0" align="start">
                                        <Calendar
                                            mode="single"
                                            selected={filters.created_after ? new Date(filters.created_after) : undefined}
                                            onSelect={(date) => {
                                                if (date) {
                                                    const start = new Date(date)
                                                    start.setHours(0, 0, 0, 0)
                                                    const end = new Date(date)
                                                    end.setHours(23, 59, 59, 999)
                                                    onFilterChange({
                                                        ...filters,
                                                        created_after: start.toISOString(),
                                                        created_before: end.toISOString()
                                                    })
                                                } else {
                                                    onFilterChange({
                                                        ...filters,
                                                        created_after: undefined,
                                                        created_before: undefined
                                                    })
                                                }
                                            }}
                                            initialFocus
                                        />
                                    </PopoverContent>
                                </Popover>
                            </TableHead>
                            <TableHead>
                                <Popover>
                                    <PopoverTrigger asChild>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className={cn(
                                                "-ml-3 h-8 data-[state=open]:bg-accent",
                                                (filters.tags && filters.tags.length > 0) && "text-primary"
                                            )}
                                        >
                                            Tags
                                            <Filter className="ml-2 h-4 w-4" />
                                        </Button>
                                    </PopoverTrigger>
                                    <PopoverContent className="w-[200px] p-0" align="start">
                                        <Command>
                                            <CommandInput placeholder="Filter tags..." />
                                            <CommandList>
                                                <CommandEmpty>No tags found.</CommandEmpty>
                                                <CommandGroup>
                                                    {availableTags.map((tag) => {
                                                        const isSelected = filters.tags?.includes(tag.id)
                                                        return (
                                                            <CommandItem
                                                                key={tag.id}
                                                                onSelect={() => {
                                                                    const current = filters.tags || []
                                                                    const next = current.includes(tag.id)
                                                                        ? current.filter(id => id !== tag.id)
                                                                        : [...current, tag.id]
                                                                    onFilterChange({ ...filters, tags: next })
                                                                }}
                                                            >
                                                                <div
                                                                    className={cn(
                                                                        "mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                                                                        isSelected
                                                                            ? "bg-primary text-primary-foreground"
                                                                            : "opacity-50 [&_svg]:invisible"
                                                                    )}
                                                                >
                                                                    <Check className="h-4 w-4" />
                                                                </div>
                                                                {tag.label}
                                                            </CommandItem>
                                                        )
                                                    })}
                                                </CommandGroup>
                                                {(filters.tags && filters.tags.length > 0) && (
                                                    <CommandGroup>
                                                        <CommandItem
                                                            onSelect={() => onFilterChange({ ...filters, tags: undefined })}
                                                            className="justify-center text-center"
                                                        >
                                                            Clear Filters
                                                        </CommandItem>
                                                    </CommandGroup>
                                                )}
                                            </CommandList>
                                        </Command>
                                    </PopoverContent>
                                </Popover>
                            </TableHead>
                            <TableHead className="w-[70px]"></TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {data.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={5} className="h-24 text-center">
                                    No job descriptions found.
                                </TableCell>
                            </TableRow>
                        ) : (
                            data.map((jd) => (
                                <TableRow key={jd.id}>
                                    <TableCell className="font-medium">
                                        <div className="flex items-center space-x-2">
                                            <FileText className="h-4 w-4 text-muted-foreground" />
                                            <span>{jd.role_name}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell>{jd.company_name}</TableCell>
                                    <TableCell>
                                        {jd.created ? format(new Date(jd.created), 'PP') : 'N/A'}
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex flex-wrap gap-1">
                                            {jd.tags?.slice(0, 3).map((tagId) => (
                                                <Badge key={tagId} variant="secondary" className="text-xs">
                                                    {tagMap[tagId] || tagId}
                                                </Badge>
                                            ))}
                                            {jd.tags && jd.tags.length > 3 && (
                                                <Badge variant="secondary" className="text-xs">
                                                    +{jd.tags.length - 3}
                                                </Badge>
                                            )}
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button variant="ghost" className="h-8 w-8 p-0">
                                                    <span className="sr-only">Open menu</span>
                                                    <MoreHorizontal className="h-4 w-4" />
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                                <DropdownMenuItem onClick={() => setViewingJD(jd)}>
                                                    <Eye className="mr-2 h-4 w-4" />
                                                    View
                                                </DropdownMenuItem>
                                                <DropdownMenuItem onClick={() => handleDownload(jd)}>
                                                    <Download className="mr-2 h-4 w-4" />
                                                    Download
                                                </DropdownMenuItem>
                                                <DropdownMenuSeparator />
                                                {/* Scoring Config Sub-menu */}
                                                <DropdownMenuItem
                                                    onClick={() => {
                                                        setAssigningJdId(jd.id)
                                                        setConfigDialogOpen(true)
                                                        setEditingConfig(null)
                                                    }}
                                                >
                                                    <Settings2 className="mr-2 h-4 w-4" />
                                                    New Scoring Config
                                                </DropdownMenuItem>
                                                {scoringConfigs.length > 0 && (
                                                    <>
                                                        {scoringConfigs.slice(0, 5).map(cfg => (
                                                            <DropdownMenuItem
                                                                key={cfg.id}
                                                                onClick={() => handleAssignConfig(jd.id, cfg.id)}
                                                                className="pl-8"
                                                            >
                                                                {jd.scoring_config === cfg.id && (
                                                                    <Check className="mr-2 h-3 w-3" />
                                                                )}
                                                                <span className="truncate">{cfg.name}</span>
                                                            </DropdownMenuItem>
                                                        ))}
                                                    </>
                                                )}
                                                <DropdownMenuItem
                                                    onClick={() => handleRecalculate(jd.id)}
                                                >
                                                    <RefreshCw className="mr-2 h-4 w-4" />
                                                    Recalculate Scores
                                                </DropdownMenuItem>
                                                <DropdownMenuSeparator />
                                                <DropdownMenuItem
                                                    onClick={() => handleDelete(jd.id)}
                                                    className="text-destructive focus:text-destructive"
                                                    disabled={deletingId === jd.id}
                                                >
                                                    <Trash2 className="mr-2 h-4 w-4" />
                                                    Delete
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>

            <Dialog open={!!viewingJD} onOpenChange={(open) => !open && setViewingJD(null)}>
                <DialogContent className="max-w-4xl h-[80vh] flex flex-col p-6 gap-2">
                    <DialogHeader>
                        <DialogTitle>{viewingJD?.role_name} at {viewingJD?.company_name}</DialogTitle>
                    </DialogHeader>
                    <div className="flex-1 overflow-hidden rounded-md border bg-muted mt-2">
                        {viewingJD && previewUrl && (
                            <iframe
                                src={previewUrl}
                                className="w-full h-full"
                                title="JD Preview"
                            />
                        )}
                    </div>
                </DialogContent>
            </Dialog>

            {/* Scoring Config Dialog */}
            <ScoringConfigDialog
                open={configDialogOpen}
                onOpenChange={setConfigDialogOpen}
                config={editingConfig}
                onSaved={async (saved) => {
                    await loadConfigs()
                    // Auto-assign to JD if we were assigning
                    if (assigningJdId) {
                        await handleAssignConfig(assigningJdId, saved.id)
                        setAssigningJdId(null)
                    }
                }}
            />
        </>
    )
}
