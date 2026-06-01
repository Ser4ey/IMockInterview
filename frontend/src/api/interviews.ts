import client from './client';
import type {
  CreateInterviewRequest,
  InterviewMessage,
  InterviewResult,
  InterviewSession,
  InterviewTurn,
  SendInterviewMessageRequest,
} from '../types/interview';

export const getInterviews = async (): Promise<InterviewSession[]> => {
  const response = await client.get<InterviewSession[]>('/interviews');
  return response.data;
};

export const getInterview = async (id: number): Promise<InterviewSession> => {
  const response = await client.get<InterviewSession>(`/interviews/${id}`);
  return response.data;
};

export const createInterview = async (data: CreateInterviewRequest): Promise<InterviewSession> => {
  const response = await client.post<InterviewSession>('/interviews', data);
  return response.data;
};

export const getInterviewMessages = async (id: number): Promise<InterviewMessage[]> => {
  const response = await client.get<InterviewMessage[]>(`/interviews/${id}/messages`);
  return response.data;
};

export const sendInterviewMessage = async (
  id: number,
  data: SendInterviewMessageRequest,
): Promise<InterviewTurn> => {
  const response = await client.post<InterviewTurn>(`/interviews/${id}/messages`, data);
  return response.data;
};

export const finishInterview = async (id: number): Promise<InterviewTurn> => {
  const response = await client.post<InterviewTurn>(`/interviews/${id}/finish`);
  return response.data;
};

export const getInterviewResult = async (id: number): Promise<InterviewResult> => {
  const response = await client.get<InterviewResult>(`/interviews/${id}/result`);
  return response.data;
};
