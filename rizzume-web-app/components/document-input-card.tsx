"use client"

import type React from "react"

import { useState } from "react"
import { Upload, X, FileText } from "lucide-react"
import { Card } from "@/components/ui/card"

interface DocumentInputCardProps {
  title: string
  description: string
  placeholder: string
  type: "resume" | "jd"
  mode: "file" | "text"
  onModeChange: (mode: "file" | "text") => void
  file?: File | null
  onFileChange: (file: File | null) => void
  text: string
  onTextChange: (text: string) => void
}

export function DocumentInputCard({
  title,
  description,
  placeholder,
  type,
  mode,
  onModeChange,
  file,
  onFileChange,
  text,
  onTextChange,
}: DocumentInputCardProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) onFileChange(droppedFile)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) onFileChange(selectedFile)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i]
  }

  return (
    <Card className="p-6 flex flex-col h-full border border-border/50">
      <div className="space-y-4 flex-1">
        {/* Header */}
        <div>
          <h3 className="text-lg font-semibold text-foreground">{title}</h3>
          <p className="text-sm text-muted-foreground mt-1">{description}</p>
        </div>

        {/* Mode toggle */}
        <div className="flex gap-2 border border-border/50 rounded-lg p-1 bg-muted/30 w-fit">
          {(["file", "text"] as const).map((m) => (
            <button
              key={m}
              onClick={() => onModeChange(m)}
              className={`px-4 py-2 rounded transition-all text-sm font-medium ${
                mode === m ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {m === "file" ? "File" : "Text"}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1">
          {mode === "file" ? (
            <>
              {!file ? (
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
                    isDragging ? "border-primary/50 bg-primary/5" : "border-border/50 hover:border-primary/30"
                  }`}
                >
                  <label className="cursor-pointer flex flex-col items-center gap-3">
                    <Upload className="w-8 h-8 text-muted-foreground" />
                    <div>
                      <p className="font-medium text-foreground">Drop your file here, or click to browse</p>
                      <p className="text-sm text-muted-foreground mt-1">Accepted: PDF, DOCX, TXT</p>
                    </div>
                    <input type="file" onChange={handleFileSelect} accept=".pdf,.docx,.txt" className="hidden" />
                  </label>
                </div>
              ) : (
                <div className="border border-border/50 rounded-lg p-4 flex items-center justify-between bg-card">
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-primary" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{file.name}</p>
                      <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                    </div>
                  </div>
                  <button onClick={() => onFileChange(null)} className="p-1.5 hover:bg-muted rounded transition-colors">
                    <X className="w-4 h-4 text-muted-foreground" />
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="flex flex-col gap-2">
              <textarea
                value={text}
                onChange={(e) => onTextChange(e.target.value)}
                placeholder={placeholder}
                className="w-full h-48 p-4 border border-border/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent resize-none bg-card text-foreground placeholder:text-muted-foreground"
              />
              <div className="text-xs text-muted-foreground text-right">{text.length.toLocaleString()} characters</div>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}
