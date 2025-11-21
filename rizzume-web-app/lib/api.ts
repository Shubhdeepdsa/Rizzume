// API integration layer for Rizzume

export interface RetrievedChunk {
  chunk_id: number
  start: number
  end: number
  similarity: number
  text: string
}

export interface QuestionItem {
  category: string
  question: string
  answer: string
  score: number
  reasoning: string
  evidence_chars: number
  retrieved_chunks: RetrievedChunk[]
}

export interface ScoreResult {
  questions: QuestionItem[]
  average_score: number
}

export interface TokenEstimate {
  jd_text_length: number
  resume_text_length: number
  jd_token_estimate: number
  resume_token_estimate: number
}

export interface ScoreResponse {
  success: boolean
  result: ScoreResult
  jd_text_length: number
  resume_text_length: number
  groupedQuestions?: {
    education: { question: string }[]
    experience: { question: string }[]
    technical_skills: { question: string }[]
    soft_skills: { question: string }[]
  }
  message: string
}

export async function estimateTokensApi(payload: {
  jdFile?: File
  resumeFile?: File
}): Promise<TokenEstimate> {
  const form = new FormData()
  if (payload.jdFile) form.append("jd_file", payload.jdFile)
  if (payload.resumeFile) form.append("resume_file", payload.resumeFile)

  const res = await fetch("http://localhost:8000/score/estimate", {
    method: "POST",
    body: form,
  })
  if (!res.ok) throw new Error("Failed to estimate tokens")
  return res.json()
}

export async function scoreResumeApi(payload: {
  jdFile?: File
  resumeFile?: File
}): Promise<ScoreResponse> {
  const form = new FormData()
  if (payload.jdFile) form.append("jd_file", payload.jdFile)
  if (payload.resumeFile) form.append("resume_file", payload.resumeFile)

  const res = await fetch("http://localhost:8000/score", {
    method: "POST",
    body: form,
  })
  if (!res.ok) throw new Error("Failed to score resume")
  return res.json()
}
