import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Container, Paper, Typography, Box, TextField, IconButton, 
  CircularProgress, Avatar, Chip 
} from '@mui/material';
import { Send as SendIcon, ArrowBack as ArrowBackIcon, Person, SmartToy } from '@mui/icons-material';
import { getChat, getMessages, sendMessage } from '../api/chats';
import { Chat, Message, MessageRole, ChatStatus } from '../types/chat';

const ChatPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [chat, setChat] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const chatId = Number(id);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!chatId) return;

    const fetchInitial = async () => {
      try {
        const chatData = await getChat(chatId);
        setChat(chatData);
        if (chatData.messages) {
          setMessages(chatData.messages);
        }
      } catch (error) {
        console.error('Failed to load chat', error);
        navigate('/dashboard');
      } finally {
        setLoading(false);
      }
    };

    fetchInitial();

    // Polling for new messages
    const interval = setInterval(async () => {
      try {
        const msgs = await getMessages(chatId);
        setMessages(msgs);
      } catch (error) {
        console.error('Polling error', error);
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(interval);
  }, [chatId, navigate]);

  const handleSend = async () => {
    if (!input.trim() || sending) return;

    const content = input;
    setInput('');
    setSending(true);

    try {
      // Optimistic update
      const tempMsg: Message = {
        id: Date.now(), // temporary id
        chat_id: chatId,
        role: MessageRole.USER,
        content: content,
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, tempMsg]);

      await sendMessage(chatId, { content });
      // The polling will catch the real message and the AI response eventually
    } catch (error) {
      console.error('Failed to send message', error);
      // Revert optimistic update if needed, but for now simple error log
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!chat) return null;

  return (
    <Container maxWidth="md" sx={{ mt: 2, mb: 4, height: '85vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box display="flex" alignItems="center">
          <IconButton onClick={() => navigate('/dashboard')} sx={{ mr: 1 }}>
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h6">
              {chat.position}
            </Typography>
            <Box display="flex" gap={1} alignItems="center">
              <Chip label={chat.level} size="small" variant="outlined" />
              <Typography variant="caption" color="text.secondary">
                {chat.topic ? `Topic: ${chat.topic}` : 'General Interview'}
              </Typography>
            </Box>
          </Box>
        </Box>
        <Chip 
          label={chat.status} 
          color={chat.status === ChatStatus.ACTIVE ? 'success' : 'default'} 
        />
      </Paper>

      {/* Messages Area */}
      <Paper sx={{ flexGrow: 1, p: 2, mb: 2, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {messages.map((msg, index) => {
          const isUser = msg.role === MessageRole.USER;
          return (
            <Box 
              key={msg.id || index} 
              sx={{ 
                display: 'flex', 
                justifyContent: isUser ? 'flex-end' : 'flex-start',
                gap: 1
              }}
            >
              {!isUser && (
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <SmartToy />
                </Avatar>
              )}
              <Paper 
                sx={{ 
                  p: 2, 
                  maxWidth: '70%', 
                  bgcolor: isUser ? 'primary.light' : 'grey.100',
                  color: isUser ? 'primary.contrastText' : 'text.primary',
                  borderRadius: 2
                }}
              >
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {msg.content}
                </Typography>
                <Typography variant="caption" display="block" textAlign="right" sx={{ mt: 1, opacity: 0.7 }}>
                  {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </Typography>
              </Paper>
              {isUser && (
                <Avatar sx={{ bgcolor: 'secondary.main' }}>
                  <Person />
                </Avatar>
              )}
            </Box>
          );
        })}
        <div ref={messagesEndRef} />
      </Paper>

      {/* Input Area */}
      <Paper sx={{ p: 2 }}>
        <Box display="flex" gap={1}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder={chat.status === ChatStatus.ACTIVE ? "Type your answer..." : "Interview completed"}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={chat.status !== ChatStatus.ACTIVE || sending}
          />
          <IconButton 
            color="primary" 
            onClick={handleSend}
            disabled={!input.trim() || chat.status !== ChatStatus.ACTIVE || sending}
            sx={{ alignSelf: 'flex-end' }}
          >
            {sending ? <CircularProgress size={24} /> : <SendIcon />}
          </IconButton>
        </Box>
      </Paper>
    </Container>
  );
};

export default ChatPage;
