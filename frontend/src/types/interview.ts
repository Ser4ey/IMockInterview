export const InterviewStatus = {
  ACTIVE: 'active',
  FINISHED: 'finished',
} as const;

export type InterviewStatus = (typeof InterviewStatus)[keyof typeof InterviewStatus];

export const InterviewStage = {
  CREATED: 'created',
  INTRO: 'intro',
  QUESTION: 'question',
  FOLLOW_UP: 'follow_up',
  FEEDBACK: 'feedback',
  FINISHED: 'finished',
} as const;

export type InterviewStage = (typeof InterviewStage)[keyof typeof InterviewStage];

export const MessageSender = {
  USER: 'user',
  AI: 'ai',
  SYSTEM: 'system',
} as const;

export type MessageSender = (typeof MessageSender)[keyof typeof MessageSender];

export interface InterviewType {
  id: number;
  title: string;
  role: string;
  technology_stack: string;
  description: string;
  levels: string[];
  default_question_count: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
  question_counts: Record<string, number>;
}

export interface InterviewSession {
  id: number;
  user_id: number;
  interview_type_id: number;
  interview_type_title: string;
  role: string;
  technology_stack: string;
  level: string;
  status: InterviewStatus;
  stage: InterviewStage;
  current_question_id?: number | null;
  question_index: number;
  question_limit?: number | null;
  started_at: string;
  finished_at?: string | null;
}

export interface InterviewMessage {
  id: number;
  session_id: number;
  question_id?: number | null;
  sender: MessageSender;
  content: string;
  created_at: string;
}

export interface InterviewResult {
  id: number;
  session_id: number;
  score: number;
  correctness: number;
  completeness: number;
  depth: number;
  communication: number;
  strengths: string[];
  weaknesses: string[];
  recommendations: string;
  summary: string;
  created_at: string;
}

export interface InterviewTurn {
  session: InterviewSession;
  messages: InterviewMessage[];
  result?: InterviewResult | null;
}

export interface CreateInterviewRequest {
  interview_type_id: number;
  level: string;
  question_count?: number | null;
}

export interface SendInterviewMessageRequest {
  content: string;
}

export interface Question {
  id: number;
  interview_type_id: number;
  interview_type_title?: string | null;
  level: string;
  question_text: string;
  expected_answer: string;
  evaluation_criteria: string[];
  tags: string[];
  question_hash?: string | null;
  source_id?: number | null;
  source?: {
    id: number;
    title: string;
    url?: string | null;
    source_type: string;
  } | null;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface GenerationJob {
  id: number;
  interview_type_id: number;
  interview_type_title?: string | null;
  level: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  requested_count: number;
  generated_count: number;
  skipped_count: number;
  provider: string;
  context_used: boolean;
  raw_response_preview?: string | null;
  input_tokens: number;
  output_tokens: number;
  error_message?: string | null;
  created_at: string;
  finished_at?: string | null;
}

export interface LlmStatus {
  llm_mode: string;
  provider: string;
  question_agent_configured: boolean;
}
