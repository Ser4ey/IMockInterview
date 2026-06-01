import client from './client';
import type { InterviewType } from '../types/interview';

export const getInterviewTypes = async (): Promise<InterviewType[]> => {
  const response = await client.get<InterviewType[]>('/interview-types');
  return response.data;
};
