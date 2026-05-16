export const ChatStatus = {
    ACTIVE: "active",
    COMPLETED: "completed",
} as const;

export type ChatStatus = (typeof ChatStatus)[keyof typeof ChatStatus];

export const MessageRole = {
    USER: "user",
    AI: "ai",
    SYSTEM: "system",
} as const;

export type MessageRole = (typeof MessageRole)[keyof typeof MessageRole];

export interface Message {
    id: number;
    chat_id: number;
    role: MessageRole;
    content: string;
    created_at: string;
}

export interface Chat {
    id: number;
    user_id: number;
    position: string;
    level: string;
    topic?: string;
    status: ChatStatus;
    feedback?: string;
    created_at: string;
    messages?: Message[];
}

export interface CreateChatRequest {
    position: string;
    level: string;
    topic?: string;
}

export interface SendMessageRequest {
    content: string;
}
