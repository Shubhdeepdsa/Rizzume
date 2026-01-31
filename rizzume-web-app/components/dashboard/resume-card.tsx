import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { FileText, Download, Calendar } from "lucide-react"
import { Resume, resumesApi } from "@/lib/api-client"
import { format } from "date-fns"

interface ResumeCardProps {
    resume: Resume
    tagMap: Record<string, string>
}

export function ResumeCard({ resume, tagMap }: ResumeCardProps) {
    const handleDownload = () => {
        const url = resumesApi.getDownloadUrl(resume.id, resume.filename)
        window.open(url, '_blank')
    }

    return (
        <Card className="flex flex-col h-full hover:shadow-md transition-shadow">
            <CardHeader className="pb-4">
                <div className="flex items-start justify-between space-x-2">
                    <div className="p-2 bg-primary/10 rounded-lg">
                        <FileText className="h-6 w-6 text-primary" />
                    </div>
                    {resume.tags && resume.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 justify-end max-w-[50%]">
                            {resume.tags.map((tagId) => (
                                <Badge key={tagId} variant="secondary" className="text-xs">
                                    {tagMap[tagId] || tagId}
                                </Badge>
                            ))}
                        </div>
                    )}
                </div>
                <CardTitle className="mt-4 text-lg font-medium line-clamp-2" title={resume.name}>
                    {resume.name}
                </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 pb-4">
                <div className="flex items-center text-sm text-muted-foreground">
                    <Calendar className="mr-2 h-4 w-4" />
                    {resume.created ? format(new Date(resume.created), 'PP') : 'Unknown Date'}
                </div>
            </CardContent>
            <CardFooter>
                <Button variant="outline" className="w-full" onClick={handleDownload} disabled={!resume.filename}>
                    <Download className="mr-2 h-4 w-4" />
                    Download
                </Button>
            </CardFooter>
        </Card>
    )
}
