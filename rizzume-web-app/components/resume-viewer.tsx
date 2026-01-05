"use client"

import type { RetrievedChunk } from "@/lib/api"

interface ResumeViewerProps {
  resumeText: string
  chunks: RetrievedChunk[]
}

export function ResumeViewer({ resumeText, chunks }: ResumeViewerProps) {
  // Build segments with chunk info
  const segments = buildSegments(resumeText, chunks)

  const getChunkColor = (chunkId: number) => {
    // Distribute colors across chunks
    const colors = [
      "bg-yellow-200 dark:bg-yellow-900/40",
      "bg-blue-200 dark:bg-blue-900/40",
      "bg-purple-200 dark:bg-purple-900/40",
      "bg-pink-200 dark:bg-pink-900/40",
      "bg-green-200 dark:bg-green-900/40",
      "bg-orange-200 dark:bg-orange-900/40",
      "bg-cyan-200 dark:bg-cyan-900/40",
      "bg-indigo-200 dark:bg-indigo-900/40",
    ]
    return colors[chunkId % colors.length]
  }

  return (
    <div className="space-y-4">
      <div className="text-xs text-muted-foreground mb-4 flex items-center gap-2 flex-wrap">
        <span className="font-medium">Highlighted sections:</span>
        {chunks.map((chunk) => (
          <span key={chunk.chunk_id} className={`px-2 py-1 rounded text-xs ${getChunkColor(chunk.chunk_id)}`}>
            Chunk #{chunk.chunk_id}
          </span>
        ))}
      </div>

      <div className="bg-card border border-border/50 rounded-lg p-6 font-mono text-sm leading-relaxed whitespace-pre-wrap break-words max-h-96 overflow-y-auto">
        {segments.map((segment, idx) => {
          if (segment.type === "text") {
            return (
              <span key={idx} className="text-foreground">
                {segment.text}
              </span>
            )
          }
          return (
            <span
              key={idx}
              className={`${getChunkColor(segment.chunkId)} px-1 rounded cursor-help transition-opacity hover:opacity-80`}
              title={`Chunk #${segment.chunkId} - Similarity: ${((segment.similarity || 0) * 100).toFixed(1)}%`}
            >
              {segment.text}
            </span>
          )
        })}
      </div>

      <div className="text-xs text-muted-foreground">
        Total highlighted: {chunks.reduce((sum, c) => sum + (c.end_char - c.start_char), 0).toLocaleString()} characters
      </div>
    </div>
  )
}

interface Segment {
  type: "text" | "highlight"
  text: string
  chunkId?: number
  similarity?: number
}

function buildSegments(resumeText: string, chunks: RetrievedChunk[]): Segment[] {
  if (chunks.length === 0) {
    return [{ type: "text", text: resumeText }]
  }

  // Sort chunks by start position
  const sortedChunks = [...chunks].sort((a, b) => a.start_char - b.start_char)

  const segments: Segment[] = []
  let currentPos = 0

  for (const chunk of sortedChunks) {
    // Add text before chunk
    if (currentPos < chunk.start_char) {
      segments.push({
        type: "text",
        text: resumeText.slice(currentPos, chunk.start_char),
      })
    }

    // Add highlighted chunk
    segments.push({
      type: "highlight",
      text: resumeText.slice(chunk.start_char, chunk.end_char),
      chunkId: chunk.chunk_id,
      similarity: chunk.similarity,
    })

    currentPos = chunk.end_char
  }

  // Add remaining text
  if (currentPos < resumeText.length) {
    segments.push({
      type: "text",
      text: resumeText.slice(currentPos),
    })
  }

  return segments
}
