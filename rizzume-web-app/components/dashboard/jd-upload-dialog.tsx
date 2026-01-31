"use client"

import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useState } from "react"
import { jdsApi } from "@/lib/api-client"
import { useToast } from "@/components/ui/use-toast"
import { Loader2, Plus } from "lucide-react"

interface JDUploadDialogProps {
    onSuccess: () => void
    open?: boolean
    onOpenChange?: (open: boolean) => void
}

export function JDUploadDialog({ onSuccess, open: constrainedOpen, onOpenChange }: JDUploadDialogProps) {
    const [internalOpen, setInternalOpen] = useState(false)

    // Derived state to handle both controlled and uncontrolled modes
    // If constrainedOpen is provided, use it. Otherwise use internalOpen.
    const isOpen = constrainedOpen !== undefined ? constrainedOpen : internalOpen

    // Helper to change state
    const setOpen = (newOpen: boolean) => {
        if (onOpenChange) {
            onOpenChange(newOpen)
        } else {
            setInternalOpen(newOpen)
        }
    }

    const [isLoading, setIsLoading] = useState(false)
    const [text, setText] = useState("")
    const [file, setFile] = useState<File | null>(null)
    const { toast } = useToast()

    const handleTextSubmit = async () => {
        if (!text.trim()) return

        try {
            setIsLoading(true)
            const formData = new FormData()
            formData.append("text", text)

            await jdsApi.create(formData)

            toast({
                title: "Success",
                description: "Job Description created successfully",
            })
            setText("")
            setOpen(false)
            onSuccess()
        } catch (error) {
            console.error(error)
            toast({
                title: "Error",
                description: "Failed to create Job Description",
                variant: "destructive",
            })
        } finally {
            setIsLoading(false)
        }
    }

    const handleFileSubmit = async () => {
        if (!file) return

        try {
            setIsLoading(true)
            const formData = new FormData()
            formData.append("file", file)

            await jdsApi.create(formData)

            toast({
                title: "Success",
                description: "Job Description uploaded successfully",
            })
            setFile(null)
            setOpen(false)
            onSuccess()
        } catch (error) {
            console.error(error)
            toast({
                title: "Error",
                description: "Failed to upload Job Description",
                variant: "destructive",
            })
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Dialog open={isOpen} onOpenChange={setOpen}>
            {!onOpenChange && (
                <DialogTrigger asChild>
                    <Button>
                        <Plus className="mr-2 h-4 w-4" />
                        Add Job Description
                    </Button>
                </DialogTrigger>
            )}
            <DialogContent className="sm:max-w-[525px] max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Add Job Description</DialogTitle>
                    <DialogDescription>
                        Paste the job description text or upload a file (PDF/DOCX).
                    </DialogDescription>
                </DialogHeader>
                <Tabs defaultValue="text" className="w-full">
                    <TabsList className="grid w-full grid-cols-2">
                        <TabsTrigger value="text">Paste Text</TabsTrigger>
                        <TabsTrigger value="file">Upload File</TabsTrigger>
                    </TabsList>
                    <TabsContent value="text" className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="jd-text">Job Description Text</Label>
                            <Textarea
                                id="jd-text"
                                placeholder="Paste the full job description here..."
                                className="min-h-[200px]"
                                value={text}
                                onChange={(e) => setText(e.target.value)}
                            />
                        </div>
                        <Button
                            onClick={handleTextSubmit}
                            className="w-full"
                            disabled={isLoading || !text.trim()}
                        >
                            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Save JD
                        </Button>
                    </TabsContent>
                    <TabsContent value="file" className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="jd-file">Upload File</Label>
                            <Input
                                id="jd-file"
                                type="file"
                                accept=".pdf,.doc,.docx,.txt"
                                onChange={(e) => setFile(e.target.files?.[0] || null)}
                            />
                            <p className="text-sm text-muted-foreground">
                                Supported formats: PDF, DOC, DOCX, TXT
                            </p>
                        </div>
                        <Button
                            onClick={handleFileSubmit}
                            className="w-full"
                            disabled={isLoading || !file}
                        >
                            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Upload JD
                        </Button>
                    </TabsContent>
                </Tabs>
            </DialogContent>
        </Dialog>
    )
}
