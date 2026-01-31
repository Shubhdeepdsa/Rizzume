"use client"

import { useEffect, useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Loader2, Search, Filter, Plus, FileText, Briefcase, X } from "lucide-react"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { cn } from "@/lib/utils"
// API
import {
    resumesApi, jdsApi,
    resumeTagsApi, jdTagsApi,
    Resume, JobDescription, ResumeTag, JDTag
} from "@/lib/api-client"
// Components
import { UploadResumeDialog } from "../upload-resume-dialog"
import { JDUploadDialog } from "../jd-upload-dialog"

interface SelectionPanelProps {
    type: "resume" | "jd"
    selectedIds: string[]
    onSelectionChange: (ids: string[]) => void
}

export function SelectionPanel({ type, selectedIds, onSelectionChange }: SelectionPanelProps) {
    // Data state
    const [items, setItems] = useState<(Resume | JobDescription)[]>([])
    const [tags, setTags] = useState<(ResumeTag | JDTag)[]>([])
    const [loading, setLoading] = useState(true)

    // Filter state
    const [searchTerm, setSearchTerm] = useState("")
    const [selectedTagIds, setSelectedTagIds] = useState<string[]>([])

    // Dialog state
    const [openDialog, setOpenDialog] = useState(false)

    useEffect(() => {
        fetchInitialData()
    }, [])

    // Debounce search
    useEffect(() => {
        const timer = setTimeout(() => {
            fetchFilteredItems()
        }, 300)
        return () => clearTimeout(timer)
    }, [searchTerm, selectedTagIds])

    const fetchInitialData = async () => {
        setLoading(true)
        try {
            if (type === "resume") {
                const [itemsData, tagsData] = await Promise.all([
                    resumesApi.getAll(),
                    resumeTagsApi.getAll()
                ])
                setItems(itemsData)
                setTags(tagsData)
            } else {
                const [itemsData, tagsData] = await Promise.all([
                    jdsApi.getAll(),
                    jdTagsApi.getAll()
                ])
                setItems(itemsData)
                setTags(tagsData)
            }
        } catch (error) {
            console.error("Failed to load data", error)
        } finally {
            setLoading(false)
        }
    }

    const fetchFilteredItems = async () => {
        try {
            if (type === "resume") {
                const filter: any = {}
                if (searchTerm) filter.name_contains = searchTerm
                if (selectedTagIds.length > 0) filter.tags = selectedTagIds
                const data = await resumesApi.search(filter)
                setItems(data)
            } else {
                const filter: any = {}
                // JDs search might differ slightly based on valid fields
                if (searchTerm) filter.role_contains = searchTerm // Fallback to role? Or implement generic search
                // Actually JDFilter has role_contains and company_contains. Let's send search to role for simple UI
                if (selectedTagIds.length > 0) filter.tags = selectedTagIds

                // NOTE: Simple search implementation. 
                // Ideally backend supports "text_contains" or we decide searching role vs company.
                // Re-using role_contains for now for simple name search behavior.
                const data = await jdsApi.search(filter)
                setItems(data)
            }
        } catch (error) {
            console.error(`Failed to filter ${type}s`, error)
        }
    }

    const toggleSelection = (id: string) => {
        if (selectedIds.includes(id)) {
            onSelectionChange(selectedIds.filter(i => i !== id))
        } else {
            onSelectionChange([...selectedIds, id])
        }
    }

    const toggleAll = () => {
        if (selectedIds.length === items.length) {
            onSelectionChange([])
        } else {
            onSelectionChange(items.map(i => i.id))
        }
    }

    const toggleTag = (tagId: string) => {
        setSelectedTagIds(prev =>
            prev.includes(tagId)
                ? prev.filter(t => t !== tagId)
                : [...prev, tagId]
        )
    }

    const getDisplayName = (item: Resume | JobDescription) => {
        if (type === "resume") {
            return (item as Resume).name
        } else {
            const jd = item as JobDescription
            return `${jd.role_name} at ${jd.company_name}`
        }
    }

    const getTagMap = () => {
        return tags.reduce((acc, tag) => {
            acc[tag.id] = tag.label
            return acc
        }, {} as Record<string, string>)
    }

    const tagMap = getTagMap()

    // Tag Filtering UI
    const renderTagFilter = () => (
        <Popover>
            <PopoverTrigger asChild>
                <Button variant="outline" size="sm" className="h-9 border-dashed">
                    <Filter className="mr-2 h-4 w-4" />
                    Tags
                    {selectedTagIds.length > 0 && (
                        <Badge variant="secondary" className="ml-2 rounded-sm px-1 font-normal">
                            {selectedTagIds.length}
                        </Badge>
                    )}
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[200px] p-0" align="start">
                <Command>
                    <CommandInput placeholder="Filter tags..." />
                    <CommandList>
                        <CommandEmpty>No tags found.</CommandEmpty>
                        <CommandGroup>
                            {tags.map((tag) => {
                                const isSelected = selectedTagIds.includes(tag.id)
                                return (
                                    <CommandItem
                                        key={tag.id}
                                        onSelect={() => toggleTag(tag.id)}
                                    >
                                        <div
                                            className={cn(
                                                "mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                                                isSelected
                                                    ? "bg-primary text-primary-foreground"
                                                    : "opacity-50 [&_svg]:invisible"
                                            )}
                                        >
                                            <span className="h-3 w-3" />
                                        </div>
                                        {tag.label}
                                    </CommandItem>
                                )
                            })}
                        </CommandGroup>
                    </CommandList>
                </Command>
            </PopoverContent>
        </Popover>
    )

    return (
        <Card className="flex flex-col h-full border-0 shadow-lg bg-card/50">
            <CardHeader className="pb-4">
                <div className="flex items-center justify-between mb-2">
                    <CardTitle className="text-xl flex items-center">
                        {type === "resume" ? <FileText className="mr-2 h-5 w-5 text-blue-500" /> : <Briefcase className="mr-2 h-5 w-5 text-purple-500" />}
                        {type === "resume" ? "Select Resumes" : "Select Job Descriptions"}
                    </CardTitle>
                    <Badge variant="secondary">
                        {selectedIds.length} Selected
                    </Badge>
                </div>

                <div className="flex flex-col gap-2">
                    <div className="flex gap-2">
                        <div className="relative flex-1">
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder={type === "resume" ? "Search by name..." : "Search by role..."}
                                className="pl-9"
                                value={searchTerm}
                                onChange={e => setSearchTerm(e.target.value)}
                            />
                        </div>
                        {renderTagFilter()}
                    </div>

                    <Button
                        size="sm"
                        variant="ghost"
                        className="self-start px-2 py-1 h-auto text-muted-foreground hover:text-foreground"
                        onClick={toggleAll}
                    >
                        {selectedIds.length === items.length && items.length > 0 ? "Deselect All" : "Select All"}
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="flex-1 min-h-0 p-0">
                <ScrollArea className="h-[400px] md:h-[calc(100vh-350px)] px-6 pb-4">
                    {loading ? (
                        <div className="flex items-center justify-center h-32">
                            <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        </div>
                    ) : items.length === 0 ? (
                        <p className="text-center text-muted-foreground py-8">No items found.</p>
                    ) : (
                        <div className="space-y-2">
                            {items.map(item => (
                                <div
                                    key={item.id}
                                    className={cn(
                                        "flex items-start space-x-3 p-3 rounded-lg  cursor-pointer shadow-sm border border-black/10 transition-colors hover:bg-accent",
                                        selectedIds.includes(item.id) ? "bg-accent border-primary" : "bg-card"
                                    )}
                                    onClick={() => toggleSelection(item.id)}
                                >
                                    <Checkbox
                                        checked={selectedIds.includes(item.id)}
                                        onCheckedChange={() => toggleSelection(item.id)}
                                    />
                                    <div className="flex-1 min-w-0 grid gap-1">
                                        <p className="font-medium truncate leading-none">
                                            {getDisplayName(item)}
                                        </p>
                                        <div className="flex flex-wrap gap-1 mt-1">
                                            {item.tags && item.tags.length > 0 ? (
                                                item.tags.map(tagId => (
                                                    <Badge key={tagId} variant="outline" className="text-[10px] px-1 py-0 h-5">
                                                        {tagMap[tagId] || "Tag"}
                                                    </Badge>
                                                ))
                                            ) : (
                                                <span className="text-xs text-muted-foreground">No tags</span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </ScrollArea>

                <div className="px-6 py-4 border-t bg-card/50">
                    <Button className="w-full" variant="outline" onClick={() => setOpenDialog(true)}>
                        <Plus className="mr-2 h-4 w-4" />
                        Add New {type === "resume" ? "Resume" : "JD"}
                    </Button>
                </div>
            </CardContent>

            {/* Dialogs */}
            {type === "resume" ? (
                <UploadResumeDialog
                    open={openDialog}
                    onOpenChange={setOpenDialog}
                    onUploadSuccess={() => {
                        fetchFilteredItems()
                        resumeTagsApi.getAll().then(setTags)
                    }}
                />
            ) : (
                <JDUploadDialog
                    open={openDialog}
                    onOpenChange={setOpenDialog}
                    onSuccess={() => {
                        fetchFilteredItems()
                        jdTagsApi.getAll().then(setTags)
                    }}
                />
            )}
        </Card>
    )
}
