
import { ResumeList } from "@/components/dashboard/resume-list"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import Link from "next/link"

export default function ResumesPage() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Resumes</h1>
                    <p className="text-muted-foreground">
                        Manage your uploaded resumes and view their details.
                    </p>
                </div>

            </div>

            <ResumeList />
        </div>
    )
}
