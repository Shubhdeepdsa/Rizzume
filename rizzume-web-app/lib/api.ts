// API integration layer for Rizzume

export interface RetrievedChunk {
  chunk_id: number | undefined
  start_char: number
  end_char: number
  similarity: number
  text: string
}

export interface QuestionItem {
  category: string
  question: string
  is_mandatory: boolean
  answer: string
  score: number
  reasoning: string
  evidence_chars: number
  retrieved_chunks: RetrievedChunk[]
}

export interface ActionPlan {
  critical_actions: string[]
  improvement_suggestions: string[]
}

export interface ScoreResult {
  questions: QuestionItem[]
  average_score: number
  action_plan?: ActionPlan
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
  resume_text: string
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
  jdText?: string
  resumeFile?: File
  resumeText?: string
}): Promise<TokenEstimate> {
  const form = new FormData()
  if (payload.jdFile) form.append("jd_file", payload.jdFile)
  else if (payload.jdText) form.append("jd_text", payload.jdText)
  if (payload.resumeFile) form.append("resume_file", payload.resumeFile)
  else if (payload.resumeText) form.append("resume_text", payload.resumeText)

  const res = await fetch("http://localhost:8000/score/estimate", {
    method: "POST",
    body: form,
  })
  if (!res.ok) throw new Error("Failed to estimate tokens")
  return res.json()
}

export async function scoreResumeApi(payload: {
  jdFile?: File
  jdText?: string
  resumeFile?: File
  resumeText?: string
}): Promise<ScoreResponse> {
  const form = new FormData()
  if (payload.jdFile) form.append("jd_file", payload.jdFile)
  else if (payload.jdText) form.append("jd_text", payload.jdText)
  if (payload.resumeFile) form.append("resume_file", payload.resumeFile)
  else if (payload.resumeText) form.append("resume_text", payload.resumeText)

  const res = await fetch("http://localhost:8000/score", {
    method: "POST",
    body: form,
  })
  if (!res.ok) throw new Error("Failed to score resume")
  return res.json()
}
