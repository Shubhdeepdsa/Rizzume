"use client"

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Eye } from "lucide-react"
import { format } from "date-fns"
import { useRouter } from "next/navigation"
import { ScoringRecord, Resume, JobDescription } from "@/lib/api-client"

interface HistoryTableProps {
    data: ScoringRecord[]
    resumes: Resume[]
    jds: JobDescription[]
    filters: { resume_id: string; jd_id: string }
    onFilterChange: (key: string, value: string) => void
}

export function HistoryTable({
    data,
    resumes,
    jds,
    filters,
    onFilterChange
}: HistoryTableProps) {
    const router = useRouter()

    const getScoreColor = (score: number) => {
        if (score >= 8) return "bg-green-100 text-green-800 hover:bg-green-100"
        if (score >= 5) return "bg-yellow-100 text-yellow-800 hover:bg-yellow-100"
        return "bg-red-100 text-red-800 hover:bg-red-100"
    }

    return (
        <div className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-4">
                <div className="w-full sm:w-[200px]">
                    <Select value={filters.resume_id} onValueChange={(val) => onFilterChange("resume_id", val)}>
                        <SelectTrigger>
                            <SelectValue placeholder="Filter by Resume" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All Resumes</SelectItem>
                            {resumes.map(r => (
                                <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
                <div className="w-full sm:w-[200px]">
                    <Select value={filters.jd_id} onValueChange={(val) => onFilterChange("jd_id", val)}>
                        <SelectTrigger>
                            <SelectValue placeholder="Filter by JD" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All Job Descriptions</SelectItem>
                            {jds.map(jd => (
                                <SelectItem key={jd.id} value={jd.id}>{jd.role_name} at {jd.company_name}</SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <div className="rounded-md border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Resume</TableHead>
                            <TableHead>Job Description</TableHead>
                            <TableHead>Score</TableHead>
                            <TableHead>Date</TableHead>
                            <TableHead className="w-[70px]"></TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {data.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={5} className="h-24 text-center">
                                    No scoring history found.
                                </TableCell>
                            </TableRow>
                        ) : (
                            data.map((record) => (
                                <TableRow key={record.id}>
                                    <TableCell className="font-medium">
                                        {record.expand?.resume?.name || "Unknown Resume"}
                                    </TableCell>
                                    <TableCell>
                                        {record.expand?.jd ? (
                                            <span>{record.expand.jd.role_name} <span className="text-muted-foreground">at</span> {record.expand.jd.company_name}</span>
                                        ) : (
                                            "Unknown JD"
                                        )}
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant="secondary" className={getScoreColor(record.score)}>
                                            {record.score.toFixed(1)} / 10
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        {record.created ? format(new Date(record.created), 'PP p') : 'N/A'}
                                    </TableCell>
                                    <TableCell>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => router.push(`/dashboard/history/${record.id}`)}
                                        >
                                            <Eye className="h-4 w-4" />
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    )
}
