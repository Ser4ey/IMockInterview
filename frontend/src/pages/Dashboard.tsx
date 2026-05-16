import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  InputLabel,
  List,
  ListItemButton,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  Snackbar,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  AutoAwesome,
  CheckCircle,
  Insights,
  QueryStats,
  TrendingUp,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { createInterview, getInterviews } from '../api/interviews';
import { getApiErrorMessage } from '../api/errors';
import { useAuth } from '../context/AuthContext';
import { InterviewStatus, InterviewType } from '../types/interview';
import type { CreateInterviewRequest, InterviewSession } from '../types/interview';

const typeLabels: Record<InterviewType, string> = {
  full: 'Полное интервью',
  theory: 'Теория',
  self_presentation: 'Самопрезентация',
  technical: 'Технический блок',
};

const stageLabels: Record<string, string> = {
  created: 'Подготовка',
  intro: 'Вступление',
  self_presentation: 'Самопрезентация',
  technical: 'Технический блок',
  practice: 'Практика',
  soft_skills: 'Soft skills',
  feedback: 'Финал',
  finished: 'Завершено',
};

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [interviews, setInterviews] = useState<InterviewSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [creating, setCreating] = useState(false);
  const [duration, setDuration] = useState('45 минут');
  const [newInterviewData, setNewInterviewData] = useState<CreateInterviewRequest>({
    specialization: 'Python Backend',
    level: 'Middle',
    interview_type: InterviewType.FULL,
  });

  useEffect(() => {
    loadInterviews();
  }, []);

  const loadInterviews = async () => {
    setLoadError(null);
    try {
      const data = await getInterviews();
      setInterviews(data);
    } catch (error) {
      console.error('Не удалось загрузить интервью', error);
      setLoadError(getApiErrorMessage(error, 'Не удалось загрузить интервью'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateInterview = async () => {
    if (!newInterviewData.specialization.trim()) return;
    setCreating(true);
    setActionError(null);
    try {
      const interview = await createInterview(newInterviewData);
      setOpenDialog(false);
      navigate(`/interviews/${interview.id}`);
    } catch (error) {
      console.error('Не удалось создать интервью', error);
      setActionError(getApiErrorMessage(error, 'Не удалось создать интервью'));
    } finally {
      setCreating(false);
    }
  };

  const finishedCount = interviews.filter((interview) => interview.status === InterviewStatus.FINISHED).length;
  const activeCount = interviews.filter((interview) => interview.status === InterviewStatus.ACTIVE).length;
  const readiness = interviews.length ? Math.min(62 + finishedCount * 7 + activeCount * 3, 92) : 64;

  const metrics = [
    { label: 'Готовность', value: `${readiness}%`, icon: <TrendingUp />, helper: 'по текущей активности' },
    { label: 'Интервью', value: interviews.length, icon: <QueryStats />, helper: `${finishedCount} завершено` },
    {
      label: 'Тариф',
      value: (user?.tariff || 'free').toUpperCase(),
      icon: <CheckCircle />,
      helper: `${user?.requests_count ?? 0} запросов использовано`,
    },
  ];

  return (
    <Container maxWidth="xl" sx={{ px: { xs: 0, md: 1 }, mb: 4 }}>
      <Paper
        sx={{
          p: { xs: 3, md: 4 },
          mb: 3,
          borderRadius: 7,
          color: '#EFF6EF',
          bgcolor: 'primary.main',
          background:
            'radial-gradient(circle at 14% 0%, rgba(177,213,190,.32), transparent 32%), linear-gradient(145deg, #132018, #183827 64%, #2F5D46)',
        }}
      >
        <Grid container spacing={3} alignItems="center">
          <Grid size={{ xs: 12, md: 8 }}>
            <Chip
              icon={<AutoAwesome />}
              label="Персональная панель подготовки"
              sx={{ mb: 2, bgcolor: 'rgba(255,255,255,0.12)', color: 'inherit' }}
            />
            <Typography variant="h3" component="h1">
              {user?.full_name || 'Кандидат'}, продолжим тренировать собеседования
            </Typography>
            <Typography sx={{ mt: 2, maxWidth: 760, color: 'rgba(239,246,239,0.76)', lineHeight: 1.7 }}>
              Выберите сценарий, пройдите диалог с AI-интервьюером и получите разбор по критериям:
              технические знания, полнота ответа, структура и коммуникация.
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Stack spacing={1.5}>
              <Button
                variant="contained"
                color="secondary"
                size="large"
                startIcon={<AddIcon />}
                onClick={() => setOpenDialog(true)}
              >
                Новое mock-собеседование
              </Button>
              <Button
                variant="outlined"
                sx={{ color: '#EFF6EF', borderColor: 'rgba(255,255,255,0.35)' }}
                onClick={() => navigate('/profile')}
              >
                Открыть профиль
              </Button>
            </Stack>
          </Grid>
        </Grid>
      </Paper>

      {loadError && (
        <Alert severity="error" sx={{ mb: 3 }} action={<Button color="inherit" size="small" onClick={loadInterviews}>Повторить</Button>}>
          {loadError}
        </Alert>
      )}

      <Grid container spacing={3}>
        {metrics.map((item) => (
          <Grid size={{ xs: 12, md: 4 }} key={item.label}>
            <Paper sx={{ p: 3, height: '100%', borderRadius: 5, bgcolor: 'rgba(255,255,255,0.64)' }}>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start" gap={2}>
                <Box>
                  <Typography variant="overline" color="text.secondary" fontWeight={900}>
                    {item.label}
                  </Typography>
                  <Typography variant="h3" sx={{ mt: 0.5 }}>
                    {item.value}
                  </Typography>
                  <Typography color="text.secondary">{item.helper}</Typography>
                </Box>
                <Box
                  sx={{
                    display: 'grid',
                    placeItems: 'center',
                    width: 48,
                    height: 48,
                    borderRadius: 3,
                    bgcolor: 'rgba(238,243,232,0.9)',
                    color: 'primary.main',
                  }}
                >
                  {item.icon}
                </Box>
              </Box>
            </Paper>
          </Grid>
        ))}

        <Grid size={{ xs: 12, md: 4 }}>
          <Paper sx={{ p: 3, height: '100%', borderRadius: 5, bgcolor: 'rgba(255,255,255,0.64)' }}>
            <Typography variant="h5" gutterBottom>
              Следующий фокус
            </Typography>
            <Typography color="text.secondary" sx={{ lineHeight: 1.7 }}>
              Тренируйте ответы с четкой структурой: короткий контекст, решение, ограничения и компромиссы.
            </Typography>
            <Stack direction="row" flexWrap="wrap" gap={1} sx={{ mt: 2 }}>
              <Chip label="REST API" />
              <Chip label="Пагинация" />
              <Chip label="Архитектура" />
            </Stack>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 8 }}>
          <Paper sx={{ p: { xs: 2.5, md: 3 }, height: '100%', borderRadius: 5, bgcolor: 'rgba(255,255,255,0.64)' }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" gap={2} mb={2}>
              <Box>
                <Typography variant="h5">История интервью</Typography>
                <Typography color="text.secondary">Последние тренировки и текущие сессии</Typography>
              </Box>
              <Button variant="outlined" startIcon={<Insights />} onClick={() => setOpenDialog(true)}>
                Настроить
              </Button>
            </Box>
            {loading ? (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            ) : interviews.length === 0 ? (
              <Box sx={{ py: 4, textAlign: 'center' }}>
                <Typography variant="h6">Интервью пока нет</Typography>
                <Typography color="text.secondary" sx={{ mt: 1 }}>
                  Создайте первое mock-собеседование, чтобы увидеть историю и прогресс.
                </Typography>
                <Button variant="contained" sx={{ mt: 2 }} onClick={() => setOpenDialog(true)}>
                  Создать интервью
                </Button>
              </Box>
            ) : (
              <List disablePadding>
                {interviews.map((interview) => (
                  <ListItemButton
                    key={interview.id}
                    onClick={() => navigate(`/interviews/${interview.id}`)}
                    sx={{
                      mb: 1.2,
                      border: '1px solid rgba(21, 57, 38, 0.1)',
                      borderRadius: 4,
                      bgcolor: 'rgba(255,255,255,0.56)',
                    }}
                  >
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1} flexWrap="wrap">
                          <Typography variant="subtitle1" component="span" fontWeight={900}>
                            {interview.specialization}
                          </Typography>
                          <Chip label={interview.level} size="small" variant="outlined" />
                          <Chip label={typeLabels[interview.interview_type]} size="small" variant="outlined" />
                        </Box>
                      }
                      secondary={`Этап: ${stageLabels[interview.stage] || interview.stage}. Создано: ${new Date(
                        interview.started_at,
                      ).toLocaleDateString('ru-RU')}`}
                    />
                    <Chip
                      label={interview.status === InterviewStatus.ACTIVE ? 'Активно' : 'Завершено'}
                      color={interview.status === InterviewStatus.ACTIVE ? 'success' : 'default'}
                      size="small"
                    />
                  </ListItemButton>
                ))}
              </List>
            )}
          </Paper>
        </Grid>
      </Grid>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle component="div" sx={{ pb: 0 }}>
          <Typography variant="h4">Настройка интервью</Typography>
          <Typography color="text.secondary" sx={{ mt: 1 }}>
            Соберите сценарий тренировки перед запуском.
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              label="Специализация"
              helperText="Например: Python Backend, Frontend React, ML Engineer"
              value={newInterviewData.specialization}
              onChange={(event) =>
                setNewInterviewData({ ...newInterviewData, specialization: event.target.value })
              }
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Уровень</InputLabel>
              <Select
                value={newInterviewData.level}
                label="Уровень"
                onChange={(event) => setNewInterviewData({ ...newInterviewData, level: event.target.value })}
              >
                <MenuItem value="Junior">Junior</MenuItem>
                <MenuItem value="Middle">Middle</MenuItem>
                <MenuItem value="Senior">Senior</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth margin="normal">
              <InputLabel>Сценарий</InputLabel>
              <Select
                value={newInterviewData.interview_type}
                label="Сценарий"
                onChange={(event) =>
                  setNewInterviewData({
                    ...newInterviewData,
                    interview_type: event.target.value as InterviewType,
                  })
                }
              >
                <MenuItem value={InterviewType.FULL}>Полное интервью</MenuItem>
                <MenuItem value={InterviewType.THEORY}>Теория</MenuItem>
                <MenuItem value={InterviewType.SELF_PRESENTATION}>Самопрезентация</MenuItem>
                <MenuItem value={InterviewType.TECHNICAL}>Технический блок</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth margin="normal">
              <InputLabel>Длительность</InputLabel>
              <Select value={duration} label="Длительность" onChange={(event) => setDuration(event.target.value)}>
                <MenuItem value="30 минут">30 минут</MenuItem>
                <MenuItem value="45 минут">45 минут</MenuItem>
                <MenuItem value="60 минут">60 минут</MenuItem>
              </Select>
            </FormControl>
            <Paper variant="outlined" sx={{ mt: 2, p: 2, borderRadius: 4, bgcolor: 'rgba(238,243,232,0.7)' }}>
              <Typography variant="subtitle2">Резюме параметров</Typography>
              <Typography color="text.secondary">
                {newInterviewData.specialization || 'Backend-разработка / Python'} · {newInterviewData.level} ·{' '}
                {typeLabels[newInterviewData.interview_type]} · {duration}
              </Typography>
            </Paper>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button onClick={() => setOpenDialog(false)}>Отмена</Button>
          <Button
            onClick={handleCreateInterview}
            variant="contained"
            disabled={!newInterviewData.specialization.trim() || creating}
          >
            {creating ? 'Создаю...' : 'Начать интервью'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!actionError} autoHideDuration={6000} onClose={() => setActionError(null)}>
        <Alert severity="error" onClose={() => setActionError(null)}>
          {actionError}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Dashboard;
