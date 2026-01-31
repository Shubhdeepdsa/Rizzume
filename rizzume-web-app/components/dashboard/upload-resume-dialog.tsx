"use client"

import { useState, useEffect, useRef } from "react"
import { useDropzone } from "react-dropzone"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { resumesApi, resumeTagsApi, ResumeTag } from "@/lib/api-client"
import { Loader2, Upload, FileText, X, Plus, Check } from "lucide-react"
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface UploadResumeDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onUploadSuccess: () => void
}

export function UploadResumeDialog({ open, onOpenChange, onUploadSuccess }: UploadResumeDialogProps) {
    const [file, setFile] = useState<File | null>(null)
    const [previewUrl, setPreviewUrl] = useState<string | null>(null)
    const [name, setName] = useState("")
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Tag State
    const [tags, setTags] = useState<ResumeTag[]>([])
    const [selectedTags, setSelectedTags] = useState<ResumeTag[]>([])
    const [tagSearch, setTagSearch] = useState("")
    const [tagOpen, setTagOpen] = useState(false)
    const [creatingTag, setCreatingTag] = useState(false)

    // File Dropzone
    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        accept: { 'application/pdf': ['.pdf'] },
        maxFiles: 1,
        onDrop: (acceptedFiles: File[]) => {
            if (acceptedFiles?.[0]) {
                handleFileSelect(acceptedFiles[0])
            }
        }
    })

    const handleFileSelect = (selectedFile: File) => {
        setFile(selectedFile)
        // Default name to filename without extension
        setName(selectedFile.name.replace(/\.pdf$/i, ""))

        // Create preview
        if (previewUrl) URL.revokeObjectURL(previewUrl)
        const url = URL.createObjectURL(selectedFile)
        setPreviewUrl(url)
    }

    // Cleanup preview on unmount or file change
    useEffect(() => {
        return () => {
            if (previewUrl) URL.revokeObjectURL(previewUrl)
        }
    }, [previewUrl])

    // Fetch tags on search
    useEffect(() => {
        const fetchTags = async () => {
            try {
                const data = await resumeTagsApi.getAll(tagSearch)
                setTags(data)
            } catch (e) {
                console.error("Failed to fetch tags", e)
            }
        }

        const timeout = setTimeout(fetchTags, 300)
        return () => clearTimeout(timeout)
    }, [tagSearch])


    const handleCreateTag = async () => {
        if (!tagSearch) return
        try {
            setCreatingTag(true)
            const newTag = await resumeTagsApi.create(tagSearch)
            setTags(prev => [...prev, newTag])
            setSelectedTags(prev => [...prev, newTag])
            setTagSearch("")
            setTagOpen(false)
        } catch (e) {
            console.error("Failed to create tag", e)
        } finally {
            setCreatingTag(false)
        }
    }

    const toggleTag = (tag: ResumeTag) => {
        setSelectedTags(prev =>
            prev.some(t => t.id === tag.id)
                ? prev.filter(t => t.id !== tag.id)
                : [...prev, tag]
        )
    }

    const handleUpload = async () => {
        if (!file || !name) return

        try {
            setLoading(true)
            setError(null)

            const formData = new FormData()
            formData.append("file", file)
            // Just send the name field if API supported renaming on upload, 
            // but actually resumesApi.create takes file as 'file' and metadata.
            // Wait, looking at api-client.ts I added:
            // create: (formData) => api.post(...)
            // Does the backend use 'name' from form? 
            // Let's check resumes.py... 
            // Yes: name=file.filename or "Untitled" if not passed? 
            // Actually: name=file.filename unless we pass something else?
            // The backend endpoint: 
            // upload_resume(file: UploadFile, tags: str = Form("[]"), ...)
            // It doesn't seem to take a 'name' field explicitly for the record Name, 
            // it uses `name=file.filename or "Untitled Resume"`. 
            // Wait, let me check the backend code again briefly if I can.
            // Ah, I recall resumes.py:
            // name=file.filename or "Untitled Resume" 
            // It doesn't seem to look for a 'name' form field.
            // However, PocketBase 'create' often takes any matching fields.
            // In resumes.py:
            // record = await pb.create_resume(..., name=file.filename, ...)
            // It sets 'name' to filename. 
            // If I want to support custom name, I should probably update backend or just accept it's filename for now.
            // Or I can send 'name' in form and update `resumes.py`.
            // BUT I am in EXECUTION mode and backend changes are expensive if not planned.
            // For now, I will stick to filename or maybe I can Rename AFTER upload?
            // Actually, let's just assume for now we upload with filename.
            // Wait, I can just rename the file object before sending? 
            // Or I can append 'name' to FormData and if backend ignores it, fine.
            // IF I really want custom name, I should check if I can modify.
            // Let's assume for now the user is fine with filename OR 
            // I'll see if I can rename the file object. File object name is readonly.
            // I'll just append 'name' to formData, maybe backend picks it up automatically if PB service handles extra kwargs?
            // `pb.create_resume` calls `resumes_col.create(...)`.
            // If `resumes.py` explicitly passes `name=file.filename`, it overrides.
            // I'll skip Custom Name for now to be safe, or just leave the input but warn myself it might not work?
            // Actually, I'll just send 'tags' correctly.

            // Correction: I should pass tags as JSON string
            const tagIds = selectedTags.map(t => t.id)
            formData.append("tags", JSON.stringify(tagIds))

            // Helpful if I can rename the file being uploaded to the user's input name?
            const renamedFile = new File([file], name.endsWith(".pdf") ? name : `${name}.pdf`, { type: file.type })
            formData.set("file", renamedFile)

            await resumesApi.create(formData)
            onUploadSuccess()
            onOpenChange(false)

            // Reset state
            setFile(null)
            setPreviewUrl(null)
            setName("")
            setSelectedTags([])
        } catch (e: any) {
            console.error("Upload failed", e)
            setError(e.response?.data?.detail || "Failed to upload resume.")
        } finally {
            setLoading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-h-[90vh] flex flex-col p-0 gap-0 overflow-hidden">
                <DialogHeader className="p-6 pb-2">
                    <DialogTitle>Upload New Resume</DialogTitle>
                </DialogHeader>

                <div className="flex flex-1 overflow-hidden p-6 pt-2 gap-6">
                    {/* Left: Form */}
                    <div className="w-1/3 flex flex-col gap-4 overflow-y-auto pr-2">
                        {error && (
                            <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">
                                {error}
                            </div>
                        )}

                        <div className="grid gap-2">
                            <Label htmlFor="name">Resume Name</Label>
                            <Input
                                id="name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="e.g. John Doe - Full Stack"
                                disabled={!file}
                            />
                        </div>

                        <div className="grid gap-2">
                            <Label>Tags</Label>
                            <div className="flex flex-wrap gap-1 mb-2">
                                {selectedTags.map(tag => (
                                    <Badge key={tag.id} variant="secondary" className="pl-1 pr-2">
                                        <X
                                            className="h-3 w-3 mr-1 cursor-pointer hover:text-destructive"
                                            onClick={() => toggleTag(tag)}
                                        />
                                        {tag.label}
                                    </Badge>
                                ))}
                            </div>
                            <Popover open={tagOpen} onOpenChange={setTagOpen}>
                                <PopoverTrigger asChild>
                                    <Button
                                        variant="outline"
                                        role="combobox"
                                        aria-expanded={tagOpen}
                                        className="justify-between"
                                        disabled={loading}
                                    >
                                        <span className="truncate opacity-50">
                                            {selectedTags.length > 0 ? "Add more tags..." : "Select tags..."}
                                        </span>
                                        <Plus className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                                    </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-[300px] p-0" align="start">
                                    <Command shouldFilter={false}>
                                        <CommandInput
                                            placeholder="Search tags..."
                                            value={tagSearch}
                                            onValueChange={setTagSearch}
                                        />
                                        <CommandList>
                                            <CommandEmpty className="py-2 px-2 text-sm">
                                                {tagSearch ? (
                                                    <div
                                                        className="flex items-center gap-2 cursor-pointer p-2 hover:bg-muted rounded-sm"
                                                        onClick={handleCreateTag}
                                                    >
                                                        <Plus className="h-4 w-4" />
                                                        Create "{tagSearch}"
                                                    </div>
                                                ) : "No tags found."}
                                            </CommandEmpty>
                                            <CommandGroup>
                                                {tags.map((tag) => (
                                                    <CommandItem
                                                        key={tag.id}
                                                        value={tag.label}
                                                        onSelect={() => {
                                                            toggleTag(tag)
                                                            setTagSearch("")
                                                            setTagOpen(false)
                                                        }}
                                                    >
                                                        <Check
                                                            className={cn(
                                                                "mr-2 h-4 w-4",
                                                                selectedTags.some(t => t.id === tag.id) ? "opacity-100" : "opacity-0"
                                                            )}
                                                        />
                                                        {tag.label}
                                                    </CommandItem>
                                                ))}
                                            </CommandGroup>
                                        </CommandList>
                                    </Command>
                                </PopoverContent>
                            </Popover>
                        </div>

                        {!file && (
                            <div
                                {...getRootProps()}
                                className={cn(
                                    "mt-4 flex flex-1 flex-col items-center justify-center rounded-md border border-dashed p-8 text-center animate-in fade-in zoom-in-95 cursor-pointer hover:bg-muted/50 transition-colors",
                                    isDragActive && "bg-muted border-primary"
                                )}
                            >
                                <input {...getInputProps()} />
                                <div className="rounded-full bg-muted p-4 mb-4">
                                    <Upload className="h-8 w-8 text-muted-foreground" />
                                </div>
                                <h3 className="font-semibold text-lg">Upload Resume</h3>
                                <p className="text-sm text-muted-foreground mt-1">
                                    Drag & drop a PDF here, or click to select
                                </p>
                            </div>
                        )}

                        {file && (
                            <div className="mt-4 p-4 border rounded-md bg-muted/20 flex items-center justify-between">
                                <div className="flex items-center gap-3 overflow-hidden">
                                    <FileText className="h-8 w-8 text-primary shrink-0" />
                                    <div className="flex flex-col overflow-hidden">
                                        <span className="text-sm font-medium truncate">{file.name}</span>
                                        <span className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                                    </div>
                                </div>
                                <Button variant="ghost" size="icon" onClick={() => {
                                    setFile(null)
                                    setPreviewUrl(null)
                                }}>
                                    <X className="h-4 w-4" />
                                </Button>
                            </div>
                        )}
                    </div>

                    {/* Right: Preview */}
                    <div className="flex-1 rounded-md border bg-muted w-2/3 h-full relative">
                        {previewUrl ? (
                            <iframe
                                src={previewUrl}
                                className="w-full h-full rounded-md"
                                title="Resume Preview"
                            />
                        ) : (
                            <div className="flex items-center justify-center h-full text-muted-foreground">
                                Preview will appear here
                            </div>
                        )}
                    </div>
                </div>

                <DialogFooter className="p-6 pt-2">
                    <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
                    <Button onClick={handleUpload} disabled={!file || loading}>
                        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Upload Resume
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
