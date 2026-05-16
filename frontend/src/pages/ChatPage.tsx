import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  Avatar,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Grid,
  IconButton,
  LinearProgress,
  Paper,
  Snackbar,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon, Person, Send as SendIcon, SmartToy } from '@mui/icons-material';
import {
  finishInterview,
  getInterview,
  getInterviewMessages,
  sendInterviewMessage,
} from '../api/interviews';
import { getApiErrorMessage } from '../api/errors';
import { InterviewStatus, MessageSender } from '../types/interview';
import type { InterviewMessage, InterviewSession } from '../types/interview';

const stageLabels: Record<string, string> = {
  intro: 'Вступление',
  self_presentation: 'Самопрезентация',
  technical: 'Технический блок',
  practice: 'Практика',
  soft_skills: 'Soft skills',
  feedback: 'Финальная реплика',
  finished: 'Завершено',
};

const typeLabels: Record<string, string> = {
  full: 'Полное интервью',
  theory: 'Теория',
  self_presentation: 'Самопрезентация',
  technical: 'Технический блок',
};

const ChatPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [interview, setInterview] = useState<InterviewSession | null>(null);
  const [messages, setMessages] = useState<InterviewMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const interviewId = Number(id);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!interviewId) return;

    const fetchInitial = async () => {
      try {
        const [interviewData, messageData] = await Promise.all([
          getInterview(interviewId),
          getInterviewMessages(interviewId),
        ]);
        setInterview(interviewData);
        setMessages(messageData);
      } catch (loadError) {
        console.error('Не удалось загрузить интервью', loadError);
        setLoadError(getApiErrorMessage(loadError, 'Не удалось загрузить интервью'));
      } finally {
        setLoading(false);
      }
    };

    fetchInitial();
  }, [interviewId, navigate]);

  const handleSend = async () => {
    if (!input.trim() || sending || !interview) return;
    const content = input.trim();
    setInput('');
    setSending(true);

    try {
      const turn = await sendInterviewMessage(interview.id, { content });
      setInterview(turn.session);
      setMessages((previous) => [...previous, ...turn.messages]);
      if (turn.session.status === InterviewStatus.FINISHED) {
        navigate(`/interviews/${interview.id}/result`);
      }
    } catch (sendError: any) {
      console.error('Не удалось отправить сообщение', sendError);
      setError(getApiErrorMessage(sendError, 'Не удалось отправить ответ'));
      setInput(content);
    } finally {
      setSending(false);
    }
  };

  const handleFinish = async () => {
    if (!interview) return;
    setSending(true);
    try {
      const turn = await finishInterview(interview.id);
      setInterview(turn.session);
      navigate(`/interviews/${interview.id}/result`);
    } catch (finishError: any) {
      console.error('Не удалось завершить интервью', finishError);
      setError(getApiErrorMessage(finishError, 'Не удалось завершить интервью'));
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
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

  if (loadError) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={() => navigate('/dashboard')}>
              К панели
            </Button>
          }
        >
          {loadError}
        </Alert>
      </Container>
    );
  }

  if (!interview) return null;

  const isFinished = interview.status === InterviewStatus.FINISHED;
  const progressByStage: Record<string, number> = {
    created: 8,
    intro: 18,
    self_presentation: 34,
    technical: 56,
    practice: 72,
    soft_skills: 84,
    feedback: 94,
    finished: 100,
  };

  return (
    <Container maxWidth="xl" sx={{ px: { xs: 0, md: 1 }, mb: 4 }}>
      <Paper
        sx={{
          p: { xs: 2.5, md: 3 },
          mb: 2.5,
          borderRadius: 6,
          bgcolor: 'rgba(255,255,255,0.66)',
        }}
      >
        <Box display="flex" alignItems="center" justifyContent="space-between" gap={2} flexWrap="wrap">
          <Box display="flex" alignItems="center">
          <IconButton aria-label="Вернуться к панели" onClick={() => navigate('/dashboard')} sx={{ mr: 1 }}>
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h4">{interview.specialization}</Typography>
            <Box display="flex" gap={1} alignItems="center" flexWrap="wrap">
              <Chip label={interview.level} size="small" variant="outlined" />
              <Chip label={typeLabels[interview.interview_type]} size="small" variant="outlined" />
              <Chip label={`Этап: ${stageLabels[interview.stage] || interview.stage}`} size="small" />
            </Box>
          </Box>
        </Box>
          <Box display="flex" alignItems="center" gap={1.5}>
          {!isFinished && (
            <Button variant="outlined" color="primary" onClick={handleFinish} disabled={sending}>
              Завершить
            </Button>
          )}
          <Chip label={isFinished ? 'Завершено' : 'Активно'} color={isFinished ? 'default' : 'success'} />
        </Box>
        </Box>
        <Box sx={{ mt: 2 }}>
          <LinearProgress variant="determinate" value={progressByStage[interview.stage] ?? 20} />
        </Box>
      </Paper>

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, md: 8.5 }}>
          <Paper
            sx={{
              height: { xs: '64vh', md: '68vh' },
              p: { xs: 2, md: 2.5 },
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              borderRadius: 6,
              bgcolor: 'rgba(255,255,255,0.66)',
            }}
          >
            {messages.map((message) => {
              const isUser = message.sender === MessageSender.USER;
              const isSystem = message.sender === MessageSender.SYSTEM;

              if (isSystem) {
                return (
                  <Box key={message.id} sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
                    <Alert severity="error">{message.content}</Alert>
                  </Box>
                );
              }

              return (
                <Box
                  key={message.id}
                  sx={{
                    display: 'flex',
                    justifyContent: isUser ? 'flex-end' : 'flex-start',
                    gap: 1.2,
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
                      maxWidth: { xs: '84%', md: '72%' },
                      bgcolor: isUser ? 'primary.main' : '#FFFFFF',
                      color: isUser ? 'primary.contrastText' : 'text.primary',
                      borderRadius: isUser ? '22px 22px 8px 22px' : '22px 22px 22px 8px',
                      boxShadow: '0 12px 34px rgba(15,23,42,0.07)',
                    }}
                  >
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.65 }}>
                      {message.content}
                    </Typography>
                    <Typography variant="caption" display="block" textAlign="right" sx={{ mt: 1, opacity: 0.65 }}>
                      {new Date(message.created_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                    </Typography>
                  </Paper>
                  {isUser && (
                    <Avatar sx={{ bgcolor: 'secondary.light', color: 'text.primary' }}>
                      <Person />
                    </Avatar>
                  )}
                </Box>
              );
            })}
            <div ref={messagesEndRef} />
          </Paper>

          <Paper sx={{ mt: 2, p: 2, borderRadius: 5, bgcolor: 'rgba(255,255,255,0.72)' }}>
            <Box display="flex" gap={1.2}>
              <TextField
                fullWidth
                multiline
                maxRows={4}
                placeholder={isFinished ? 'Интервью завершено' : 'Введите ответ кандидата...'}
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isFinished || sending}
              />
              <IconButton
                aria-label="Отправить ответ"
                color="primary"
                onClick={handleSend}
                disabled={!input.trim() || isFinished || sending}
                sx={{
                  alignSelf: 'flex-end',
                  width: 52,
                  height: 52,
                  bgcolor: 'primary.main',
                  color: 'primary.contrastText',
                  '&:hover': { bgcolor: 'primary.dark' },
                }}
              >
                {sending ? <CircularProgress size={24} color="inherit" /> : <SendIcon />}
              </IconButton>
            </Box>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 3.5 }}>
          <Stack spacing={2}>
            <Paper sx={{ p: 3, borderRadius: 6, bgcolor: 'rgba(255,255,255,0.66)' }}>
              <Typography variant="h6">Параметры</Typography>
              <Stack spacing={1.2} sx={{ mt: 2 }}>
                <Chip label={`Роль: ${interview.specialization}`} />
                <Chip label={`Уровень: ${interview.level}`} />
                <Chip label={`Формат: ${typeLabels[interview.interview_type]}`} />
              </Stack>
            </Paper>
            <Paper sx={{ p: 3, borderRadius: 6, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
              <Typography variant="h6">Подсказка</Typography>
              <Typography sx={{ mt: 1.5, color: 'rgba(255,255,255,0.76)', lineHeight: 1.7 }}>
                Отвечайте по структуре: тезис, объяснение, пример из опыта, компромисс или ограничение.
              </Typography>
            </Paper>
          </Stack>
        </Grid>
      </Grid>

      <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError(null)}>
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default ChatPage;
