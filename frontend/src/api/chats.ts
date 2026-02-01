import client from './client';
import { Chat, CreateChatRequest, Message, SendMessageRequest } from '../types/chat';

export const getChats = async (): Promise<Chat[]> => {
    const response = await client.get<Chat[]>('/chats');
    return response.data;
};

export const getChat = async (id: number): Promise<Chat> => {
    const response = await client.get<Chat>(`/chats/${id}`);
    return response.data;
};

export const createChat = async (data: CreateChatRequest): Promise<Chat> => {
    const response = await client.post<Chat>('/chats', data);
    return response.data;
};

export const sendMessage = async (chatId: number, data: SendMessageRequest): Promise<Message> => {
    const response = await client.post<Message>(`/chats/${chatId}/messages`, data);
    return response.data;
};

export const getMessages = async (chatId: number): Promise<Message[]> => {
    const response = await client.get<Message[]>(`/chats/${chatId}/messages`);
    return response.data;
};

export const finishChat = async (chatId: number): Promise<Chat> => {
    const response = await client.post<Chat>(`/chats/${chatId}/finish`);
    return response.data;
};
