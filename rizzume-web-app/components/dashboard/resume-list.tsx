"use client"

import { useEffect, useState } from "react"
import { Resume, resumesApi, ResumeTag, resumeTagsApi, ResumeFilter } from "@/lib/api-client"
import { useAuth } from "@/context/auth-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Loader2, FileText, Eye, Download, Calendar as CalendarIcon, Filter, X } from "lucide-react"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { format } from "date-fns"
import { cn } from "@/lib/utils"
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command"
import { UploadResumeDialog } from "./upload-resume-dialog"

export function ResumeList() {
    const { user } = useAuth()
    const [resumes, setResumes] = useState<Resume[]>([])
    const [tags, setTags] = useState<ResumeTag[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Filter State
    const [nameFilter, setNameFilter] = useState("")
    const [selectedTags, setSelectedTags] = useState<string[]>([])
    const [dateFilter, setDateFilter] = useState<Date | undefined>(undefined)

    // View State
    const [viewingResume, setViewingResume] = useState<Resume | null>(null)
    const [previewUrl, setPreviewUrl] = useState<string | null>(null)
    const [uploadOpen, setUploadOpen] = useState(false)

    useEffect(() => {
        fetchInitialData()
    }, [])

    // Debounce search
    useEffect(() => {
        const timer = setTimeout(() => {
            fetchResumes()
        }, 300)
        return () => clearTimeout(timer)
    }, [nameFilter, selectedTags, dateFilter])

    // Handle Preview URL creation/cleanup
    useEffect(() => {
        if (viewingResume) {
            let active = true
            resumesApi.download(viewingResume.id).then(blob => {
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
    }, [viewingResume])

    const fetchInitialData = async () => {
        try {
            setLoading(true)
            const [tagsData] = await Promise.all([
                resumeTagsApi.getAll()
            ])
            setTags(tagsData)
            await fetchResumes()
        } catch (err) {
            setError("Failed to load data.")
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const fetchResumes = async () => {
        try {
            const filter: ResumeFilter = {}
            if (nameFilter) filter.name_contains = nameFilter
            if (selectedTags.length > 0) filter.tags = selectedTags
            if (dateFilter) {
                // Set start/end of day for broader match if needed, or just specific day
                // Backend expects string. Let's send start of day for created_after
                // and end of day for created_before to filter by single day if that's the UX.
                // Or just "created_after" if user wants "since". 
                // Let's assume user picks a date and wants resumes FROM that date onwards? 
                // Or SPECIFIC date? usually specific date in table filters.
                // Let's implement specific date match by setting range [startOfDay, endOfDay]
                const start = new Date(dateFilter)
                start.setHours(0, 0, 0, 0)
                const end = new Date(dateFilter)
                end.setHours(23, 59, 59, 999)

                filter.created_after = start.toISOString()
                filter.created_before = end.toISOString()
            }

            const data = await resumesApi.search(filter)
            setResumes(data)
            setError(null)
        } catch (err) {
            console.error("Search failed", err)
            // Don't set global error to avoid blocking UI on simple filter change fail
        }
    }

    const toggleTag = (tagId: string) => {
        setSelectedTags(prev =>
            prev.includes(tagId)
                ? prev.filter(id => id !== tagId)
                : [...prev, tagId]
        )
    }

    const clearFilters = () => {
        setNameFilter("")
        setSelectedTags([])
        setDateFilter(undefined)
    }

    const handleDownload = async (resume: Resume) => {
        try {
            const blob = await resumesApi.download(resume.id)
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url

            // Construct new filename: <user_name>_<resume_name>.<ext>
            const userName = user?.name || "user"
            const safeUserName = userName.replace(/[^a-z0-9]/gi, '_').replace(/_+/g, '_')
            const safeResumeName = resume.name.replace(/[^a-z0-9]/gi, '_').replace(/_+/g, '_')

            // Try to preserve extension or default to pdf
            // Try to preserve extension or default to pdf
            const parts = (resume.filename || "").split('.')
            const ext = parts.length > 1 ? parts.pop() : 'pdf'

            a.download = `${safeUserName}_${safeResumeName}.${ext}`

            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            URL.revokeObjectURL(url)
        } catch (e) {
            console.error("Download failed", e)
        }
    }

    const tagMap = tags.reduce((acc, tag) => {
        acc[tag.id] = tag.label
        return acc
    }, {} as Record<string, string>)

    const hasFilters = nameFilter || selectedTags.length > 0 || dateFilter

    if (loading && resumes.length === 0) {
        return (
            <div className="flex h-64 items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        )
    }

    return (
        <div className="space-y-4">
            {/* Filters */}
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div className="flex flex-1 items-center gap-2">
                    <div className="relative w-full max-w-sm">
                        <FileText className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search resumes..."
                            value={nameFilter}
                            onChange={(e) => setNameFilter(e.target.value)}
                            className="pl-8"
                        />
                    </div>

                    {/* Date Picker */}
                    <Popover>
                        <PopoverTrigger asChild>
                            <Button
                                variant={"outline"}
                                className={cn(
                                    "w-[200px] justify-start text-left font-normal",
                                    !dateFilter && "text-muted-foreground"
                                )}
                            >
                                <CalendarIcon className="mr-2 h-4 w-4" />
                                {dateFilter ? format(dateFilter, "PPP") : <span>Pick a date</span>}
                            </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="start">
                            <Calendar
                                mode="single"
                                selected={dateFilter}
                                onSelect={setDateFilter}
                                initialFocus
                            />
                        </PopoverContent>
                    </Popover>

                    {/* Tag Filter */}
                    <Popover>
                        <PopoverTrigger asChild>
                            <Button variant="outline" className="h-10 border-dashed">
                                <Filter className="mr-2 h-4 w-4" />
                                Tags
                                {selectedTags.length > 0 && (
                                    <Badge variant="secondary" className="ml-2 rounded-sm px-1 font-normal">
                                        {selectedTags.length}
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
                                            const isSelected = selectedTags.includes(tag.id)
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
                                                        <span className="h-3 w-3" /> {/* Checkmark proxy */}
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

                    {hasFilters && (
                        <Button variant="ghost" onClick={clearFilters} className="h-8 px-2 lg:px-3">
                            Reset
                            <X className="ml-2 h-4 w-4" />
                        </Button>
                    )}
                </div>
                <Button onClick={() => setUploadOpen(true)}>
                    <FileText className="mr-2 h-4 w-4" />
                    New Resume
                </Button>
            </div>

            {/* Table */}
            <div className=" ">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>Uploaded</TableHead>
                            <TableHead>Tags</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {resumes.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={4} className="h-24 text-center">
                                    No resumes found.
                                </TableCell>
                            </TableRow>
                        ) : (
                            resumes.map((resume) => (
                                <TableRow key={resume.id}>
                                    <TableCell className="font-medium">
                                        <div className="flex flex-col">
                                            <span>{resume.name}</span>
                                            <span className="text-xs text-muted-foreground">{resume.filename}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        {format(new Date(resume.created), "MMM d, yyyy")}
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex flex-wrap gap-1">
                                            {resume.tags?.map((tagId) => (
                                                <Badge key={tagId} variant="secondary" className="rounded-sm px-1 font-normal">
                                                    {tagMap[tagId] || "Unknown"}
                                                </Badge>
                                            ))}
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex justify-end gap-2">
                                            <Button size="sm" variant="outline" onClick={() => setViewingResume(resume)}>
                                                <Eye className="mr-2 h-4 w-4" />
                                                View
                                            </Button>
                                            <Button size="sm" variant="ghost" onClick={() => handleDownload(resume)}>
                                                <Download className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>

            {/* View Modal */}
            <Dialog open={!!viewingResume} onOpenChange={(open) => !open && setViewingResume(null)}>
                <DialogContent className="max-w-4xl h-[80vh] flex flex-col p-6 gap-2">
                    <DialogHeader className="p-0 space-y-0">
                        <DialogTitle>{viewingResume?.name}</DialogTitle>
                    </DialogHeader>
                    <div className="flex-1 overflow-hidden rounded-md border bg-muted mt-2">
                        {viewingResume && previewUrl && (
                            <iframe
                                src={previewUrl}
                                className="w-full h-full"
                                title="Resume Preview"
                            />
                        )}
                    </div>
                </DialogContent>
            </Dialog>

            <UploadResumeDialog
                open={uploadOpen}
                onOpenChange={setUploadOpen}
                onUploadSuccess={() => {
                    fetchResumes()
                    // Refresh tags too in case new ones were added
                    resumeTagsApi.getAll().then(setTags)
                }}
            />
        </div >
    )
}
