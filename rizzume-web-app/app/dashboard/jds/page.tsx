"use client"

import { useEffect, useState } from "react"
import { JobDescription, jdsApi, JDFilter, jdTagsApi, JDTag } from "@/lib/api-client"
import { JDTable } from "@/components/dashboard/jd-table"
import { JDUploadDialog } from "@/components/dashboard/jd-upload-dialog"
import { Loader2, Search, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { format } from "date-fns"

export default function JDsPage() {
    const [jds, setJds] = useState<JobDescription[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Filter State
    const [roleSearch, setRoleSearch] = useState("")
    const [filters, setFilters] = useState<JDFilter>({})
    const [availableTags, setAvailableTags] = useState<any[]>([]) // Using any[] temporarily if import issue, or JDTag[]
    const [availableCompanies, setAvailableCompanies] = useState<string[]>([])

    // Debounce search
    useEffect(() => {
        const timer = setTimeout(() => {
            fetchJds()
        }, 300)
        return () => clearTimeout(timer)
    }, [roleSearch, filters])

    const fetchJds = async () => {
        try {
            setLoading(true)
            const searchCriteria: JDFilter = {
                ...filters,
                role_contains: roleSearch || undefined
            }
            // Use search endpoint if any filter is active (including empty filters object if backend handles it, 
            // but effectively we always want latest list. search({ }) behaves like getAll usually)
            // But let's check if getAll is faster or preferred for init? 
            // We'll just use search for everything to be consistent.
            const data = await jdsApi.search(searchCriteria)
            setJds(data)
            setError(null)
        } catch (err) {
            setError("Failed to load job descriptions.")
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    // Initial fetch handled by the debounce effect since initial state triggers it?
    // Actually empty dep array effect runs once. 
    // The debounce effect also runs on mount because state is initialized.
    // So we don't need the [] effect, OR we keep it and remove fetchJds from debounce dependency?
    // Best practice: useEffect on [dependencies] handles mount too.
    // But we want to avoid double fetch.
    // I'll remove the explicitly empty useEffect.

    const fetchTags = async () => {
        try {
            const [tags, companies] = await Promise.all([
                jdTagsApi.getAll(),
                jdsApi.getCompanies()
            ])

            // Deduplicate tags by ID
            const uniqueTagsMap = new Map()
            tags.forEach(tag => {
                if (!uniqueTagsMap.has(tag.id)) {
                    uniqueTagsMap.set(tag.id, tag)
                }
            })
            setAvailableTags(Array.from(uniqueTagsMap.values()))
            setAvailableCompanies(companies)
        } catch (e) {
            console.error("Failed to fetch tags/companies", e)
        }
    }

    useEffect(() => {
        fetchTags()
    }, [])

    const clearAllFilters = () => {
        setRoleSearch("")
        setFilters({})
    }

    const removeTagFilter = (tagId: string) => {
        const nextTags = filters.tags?.filter(t => t !== tagId)
        setFilters({ ...filters, tags: nextTags?.length ? nextTags : undefined })
    }

    const getTagName = (id: string) => {
        return availableTags.find((t: JDTag) => t.id === id)?.label || id
    }

    const hasActiveFilters = roleSearch || filters.company_contains || filters.created_after || (filters.tags && filters.tags.length > 0)

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Job Descriptions</h1>
                    <p className="text-muted-foreground">
                        Manage your job descriptions and usage.
                    </p>
                </div>
                <JDUploadDialog onSuccess={fetchJds} />
            </div>

            {loading ? (
                <div className="flex h-64 items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
            ) : error ? (
                <div className="flex h-64 flex-col items-center justify-center space-y-4 text-center">
                    <p className="text-destructive">{error}</p>
                    <Button variant="outline" onClick={fetchJds}>
                        Try Again
                    </Button>
                </div>
            ) : (
                <div className="flex flex-col gap-4">
                    {/* Active Filters Bar */}
                    {hasActiveFilters && (
                        <div className="flex flex-wrap items-center gap-2">
                            <span className="text-sm text-muted-foreground mr-2">Active Filters:</span>

                            {roleSearch && (
                                <Badge variant="secondary" className="gap-1 pr-1">
                                    Role: {roleSearch}
                                    <Button variant="ghost" size="icon" className="h-4 w-4 p-0 hover:bg-transparent" onClick={() => setRoleSearch("")}>
                                        <X className="h-3 w-3" />
                                    </Button>
                                </Badge>
                            )}

                            {filters.company_contains && (
                                <Badge variant="secondary" className="gap-1 pr-1">
                                    Company: {filters.company_contains}
                                    <Button variant="ghost" size="icon" className="h-4 w-4 p-0 hover:bg-transparent" onClick={() => setFilters({ ...filters, company_contains: undefined })}>
                                        <X className="h-3 w-3" />
                                    </Button>
                                </Badge>
                            )}

                            {filters.created_after && (
                                <Badge variant="secondary" className="gap-1 pr-1">
                                    Date: {format(new Date(filters.created_after), 'MMM d, yyyy')}
                                    <Button variant="ghost" size="icon" className="h-4 w-4 p-0 hover:bg-transparent" onClick={() => setFilters({ ...filters, created_after: undefined, created_before: undefined })}>
                                        <X className="h-3 w-3" />
                                    </Button>
                                </Badge>
                            )}

                            {filters.tags?.map(tagId => (
                                <Badge key={tagId} variant="secondary" className="gap-1 pr-1">
                                    Tag: {getTagName(tagId)}
                                    <Button variant="ghost" size="icon" className="h-4 w-4 p-0 hover:bg-transparent" onClick={() => removeTagFilter(tagId)}>
                                        <X className="h-3 w-3" />
                                    </Button>
                                </Badge>
                            ))}

                            <Button variant="ghost" size="sm" onClick={clearAllFilters} className="h-6 px-2 text-xs">
                                Reset All
                            </Button>
                        </div>
                    )}

                    <div className="relative max-w-sm">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search by role..."
                            value={roleSearch}
                            onChange={(e) => setRoleSearch(e.target.value)}
                            className="pl-8"
                        />
                    </div>

                    <JDTable
                        data={jds}
                        onRefresh={fetchJds}
                        filters={filters}
                        onFilterChange={setFilters}
                        availableTags={availableTags}
                        availableCompanies={availableCompanies}
                    />
                </div>
            )}
        </div>
    )
}
