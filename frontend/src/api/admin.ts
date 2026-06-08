import client from './client';
import type { GenerationJob, InterviewType, LlmStatus, Question } from '../types/interview';

export interface CreateInterviewTypePayload {
  title: string;
  role: string;
  technology_stack: string;
  description: string;
  levels: string[];
  default_question_count: number;
  is_active: boolean;
  auto_generate_questions?: boolean;
  questions_per_level?: number;
}

export interface CreateQuestionPayload {
  interview_type_id: number;
  level: string;
  question_text: string;
  expected_answer: string;
  evaluation_criteria: string[];
  tags: string[];
  is_active: boolean;
}

export const getAdminInterviewTypes = async (): Promise<InterviewType[]> => {
  const response = await client.get<InterviewType[]>('/admin/interview-types');
  return response.data;
};

export const getAdminLlmStatus = async (): Promise<LlmStatus> => {
  const response = await client.get<LlmStatus>('/admin/llm-status');
  return response.data;
};

export const createAdminInterviewType = async (payload: CreateInterviewTypePayload): Promise<InterviewType> => {
  const response = await client.post<InterviewType>('/admin/interview-types', payload);
  return response.data;
};

export const updateAdminInterviewType = async (
  id: number,
  payload: Partial<CreateInterviewTypePayload>,
): Promise<InterviewType> => {
  const response = await client.patch<InterviewType>(`/admin/interview-types/${id}`, payload);
  return response.data;
};

export const generateAdminQuestions = async (
  interviewTypeId: number,
  level: string,
  requestedCount: number,
): Promise<GenerationJob> => {
  const response = await client.post<GenerationJob>(`/admin/interview-types/${interviewTypeId}/generate-questions`, {
    level,
    requested_count: requestedCount,
  });
  return response.data;
};

export const getAdminQuestions = async (params?: {
  interview_type_id?: number;
  level?: string;
  tag?: string;
  include_disabled?: boolean;
}): Promise<Question[]> => {
  const response = await client.get<Question[]>('/admin/questions', { params });
  return response.data;
};

export const createAdminQuestion = async (payload: CreateQuestionPayload): Promise<Question> => {
  const response = await client.post<Question>('/admin/questions', payload);
  return response.data;
};

export const updateAdminQuestion = async (id: number, payload: Partial<CreateQuestionPayload>): Promise<Question> => {
  const response = await client.patch<Question>(`/admin/questions/${id}`, payload);
  return response.data;
};

export const disableAdminQuestion = async (id: number): Promise<Question> => {
  const response = await client.patch<Question>(`/admin/questions/${id}/disable`);
  return response.data;
};

export const enableAdminQuestion = async (id: number): Promise<Question> => {
  const response = await client.patch<Question>(`/admin/questions/${id}/enable`);
  return response.data;
};

export const getAdminGenerationJobs = async (): Promise<GenerationJob[]> => {
  const response = await client.get<GenerationJob[]>('/admin/question-generation-jobs');
  return response.data;
};
