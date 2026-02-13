import axios from 'axios';

// Constants
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const TOKEN_KEY = 'rizzume_token';

// -- Public API Client --
// Used for Login, Signup, Health checks that don't need a token
export const publicApi = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// -- Private API Client --
// Automatically attaches tokens and handles 401s
export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach Token
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle 401 (Unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Check if error is 401
    if (error.response && error.response.status === 401) {
      if (typeof window !== 'undefined') {
        // Clear token
        localStorage.removeItem(TOKEN_KEY);
        // Redirect to auth page if not already there
        if (!window.location.pathname.startsWith('/auth')) {
            window.location.href = '/auth?view=login&session_expired=true';
        }
      }
    }
    return Promise.reject(error);
  }
);

export interface Resume {
  id: string;
  name: string;
  filename: string;
  created: string;
  tags?: string[];
  original_text?: string;
}

export interface ResumeFilter {
  tags?: string[];
  created_after?: string;
  created_before?: string;
  name_contains?: string;
}

export const resumesApi = {
  getAll: async () => {
    const response = await api.get<Resume[]>('/api/resumes');
    return response.data;
  },

  search: async (filter: ResumeFilter) => {
    const response = await api.post<Resume[]>('/api/resumes/search', filter);
    return response.data;
  },
  
  // Helper to construct the download URL for a resume file
  // DEPRECATED: Use download() instead for authenticated access
  getDownloadUrl: (recordId: string, filename: string) => {
    return `${API_URL}/api/resumes/${recordId}/download`;
  },

  download: async (recordId: string) => {
    const response = await api.get(`/api/resumes/${recordId}/download`, {
        responseType: 'blob'
    });
    return response.data as Blob;
  },

  create: async (formData: FormData) => {
    const response = await api.post<Resume>('/api/resumes', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
};

export interface JobDescription {
  id: string;
  role_name: string;
  company_name: string;
  original_text: string;
  filename?: string;
  created: string;
  tags?: string[];
  scoring_config?: string; // config ID — nullable relation
}

export interface JDFilter {
  tags?: string[];
  created_after?: string;
  created_before?: string;
  role_contains?: string;
  company_contains?: string;
}

export const jdsApi = {
  getAll: async () => {
    const response = await api.get<JobDescription[]>('/api/jds');
    return response.data;
  },

  search: async (filter: JDFilter) => {
    const response = await api.post<JobDescription[]>('/api/jds/search', filter);
    return response.data;
  },

  getCompanies: async () => {
    const response = await api.get<string[]>('/api/jds/companies');
    return response.data;
  },
  
  create: async (formData: FormData) => {
    const response = await api.post<JobDescription>('/api/jds', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  delete: async (id: string) => {
      await api.delete(`/api/jds/${id}`);
  },

  getDownloadUrl: (recordId: string, filename: string) => {
      return `${API_URL}/api/jds/${recordId}/download`;
  },

  download: async (recordId: string) => {
      const response = await api.get(`/api/jds/${recordId}/download`, {
          responseType: 'blob'
      });
      return response.data as Blob;
  },

  // Helper to download text JDs as .txt
  downloadText: (jd: JobDescription) => {
      const element = document.createElement("a");
      const file = new Blob([jd.original_text], {type: 'text/plain'});
      element.href = URL.createObjectURL(file);
      element.download = `${jd.role_name}-${jd.company_name}.txt`;
      document.body.appendChild(element); // Required for this to work in FireFox
      element.click();
      document.body.removeChild(element);
  }
};

export interface ScoringRecord {
  id: string;
  resume_id: string;
  jd_id: string;
  score: number;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'recalculating';
  created: string;
  expand?: {
    resume?: Resume;
    jd?: JobDescription;
  };
  result?: any;
  analysis?: any;
}

export const scoringApi = {
  getResults: async (filters?: { resume_id?: string; jd_id?: string }) => {
    const params = new URLSearchParams();
    if (filters?.resume_id && filters.resume_id !== "all") params.append("resume_id", filters.resume_id);
    if (filters?.jd_id && filters.jd_id !== "all") params.append("jd_id", filters.jd_id);
    
    // Using axios with params for cleaner URL construction if preferred, but manual string is fine too.
    const response = await api.get<ScoringRecord[]>(`/api/results?${params.toString()}`);
    return response.data;
  },
  
  getDetail: async (id: string) => {
    const response = await api.get<ScoringRecord>(`/api/results/${id}`);
    return response.data;
  },

  batchScore: async (resumeIds: string[], jdIds: string[]) => {
    const response = await api.post('/api/batch-score', {
      resume_ids: resumeIds,
      jd_ids: jdIds
    });
    return response.data;
  },

  estimateBatch: async (resumeIds: string[], jdIds: string[]) => {
      const response = await api.post<BatchTokenEstimateResponse>('/api/score/estimate-batch', {
          resume_ids: resumeIds,
          jd_ids: jdIds
      });
      return response.data;
  }
};

export interface TokenStrategyDetail {
    name: string;
    total_tokens: number;
    tokens_per_question: number;
    context_tokens: number;
    context_type: string;
}

export interface BatchTokenEstimateResponse {
    resume_count: number;
    jd_count: number;
    total_combinations: number;
    total_questions: number;
    rag_strategy: TokenStrategyDetail;
    full_resume_strategy: TokenStrategyDetail;
    savings_tokens: number;
    savings_percentage: number;
    warnings: string[];
}


export interface ResumeTag {
  id: string;
  label: string;
}

export const resumeTagsApi = {
  getAll: async (search?: string) => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    
    const response = await api.get<ResumeTag[]>(`/api/resume/tags?${params.toString()}`);
    return response.data;
  },

  create: async (label: string) => {
      const response = await api.post<ResumeTag>('/api/resume/tags', { label });
      return response.data;
  }
};

export interface JDTag {
    id: string;
    label: string;
    category: string;
}

export const jdTagsApi = {
    getAll: async () => {
        const response = await api.get<JDTag[]>('/api/jd/tags');
        return response.data;
    }
};

// ─────────────────────────────────────────────────────────────
// Scoring Configs
// ─────────────────────────────────────────────────────────────

export interface ScoringConfig {
  id: string;
  name: string;
  education_weight: number;
  experience_weight: number;
  technical_weight: number;
  soft_skills_weight: number;
  mandatory_question_weight: number;
  optional_question_weight: number;
  mandatory_cap_weight: number;
  is_default: boolean;
  created: string;
  updated: string;
  usage_count?: number;
  used_by_jds?: { id: string; role_name: string; company_name: string }[];
}

export interface ScoringConfigInput {
  name: string;
  education_weight: number;
  experience_weight: number;
  technical_weight: number;
  soft_skills_weight: number;
  mandatory_question_weight?: number;
  optional_question_weight?: number;
  mandatory_cap_weight?: number;
  is_default?: boolean;
}

export const scoringConfigApi = {
  getAll: async () => {
    const response = await api.get<ScoringConfig[]>('/api/scoring-configs');
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get<ScoringConfig>(`/api/scoring-configs/${id}`);
    return response.data;
  },

  create: async (data: ScoringConfigInput) => {
    const response = await api.post<ScoringConfig>('/api/scoring-configs', data);
    return response.data;
  },

  update: async (id: string, data: Partial<ScoringConfigInput>) => {
    const response = await api.patch<ScoringConfig>(`/api/scoring-configs/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    const response = await api.delete(`/api/scoring-configs/${id}`);
    return response.data;
  },

  assignToJd: async (configId: string, jdId: string) => {
    const response = await api.post(`/api/scoring-configs/${configId}/assign/${jdId}`);
    return response.data as { status: string; affected_count: number };
  },

  recalculateJd: async (jdId: string) => {
    const response = await api.post(`/api/scoring-configs/recalculate/${jdId}`);
    return response.data as { status: string; affected_count: number };
  },
};
