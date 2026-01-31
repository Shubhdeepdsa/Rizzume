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
import { MoreHorizontal, Download, Trash2, FileText, Eye } from "lucide-react"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { JobDescription, jdsApi, JDTag, jdTagsApi } from "@/lib/api-client"
import { format } from "date-fns"
import { useState, useEffect } from "react"
import { useToast } from "@/components/ui/use-toast"

interface JDTableProps {
    data: JobDescription[]
    onRefresh: () => void
}

export function JDTable({ data, onRefresh }: JDTableProps) {
    const { toast } = useToast()
    const [deletingId, setDeletingId] = useState<string | null>(null)
    const [viewingJD, setViewingJD] = useState<JobDescription | null>(null)
    const [previewUrl, setPreviewUrl] = useState<string | null>(null)
    const [jdTags, setJdTags] = useState<JDTag[]>([])

    useEffect(() => {
        fetchTags()
    }, [])

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

    const fetchTags = async () => {
        try {
            const tags = await jdTagsApi.getAll()
            setJdTags(tags)
        } catch (e) {
            console.error("Failed to fetch JD tags", e)
        }
    }

    const tagMap = jdTags.reduce((acc, tag) => {
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

    return (
        <>
            <div className="">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Role</TableHead>
                            <TableHead>Company</TableHead>
                            <TableHead>Date Added</TableHead>
                            <TableHead>Tags</TableHead>
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
        </>
    )
}
