import React, { useEffect, useMemo, useState } from 'react';
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
import { Add as AddIcon, Assessment, AutoAwesome, Chat, Insights, QueryStats, TrendingUp } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { createInterview, getInterviews } from '../api/interviews';
import { getInterviewTypes } from '../api/interviewTypes';
import { getApiErrorMessage } from '../api/errors';
import { useAuth } from '../context/AuthContext';
import { InterviewStatus } from '../types/interview';
import type { CreateInterviewRequest, InterviewSession, InterviewType } from '../types/interview';

const levelLabels: Record<string, string> = {
  junior: 'Junior',
  middle: 'Middle',
  senior: 'Senior',
};

const stageLabels: Record<string, string> = {
  created: 'Подготовка',
  intro: 'Вступление',
  question: 'Вопрос',
  follow_up: 'Уточнение',
  feedback: 'Финал',
  finished: 'Завершено',
};

const maxInterviewQuestionCount = 10;

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [interviews, setInterviews] = useState<InterviewSession[]>([]);
  const [interviewTypes, setInterviewTypes] = useState<InterviewType[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newInterviewData, setNewInterviewData] = useState<CreateInterviewRequest>({
    interview_type_id: 0,
    level: 'junior',
    question_count: null,
  });

  const resolveDefaultQuestionCount = (type: InterviewType | undefined, level: string): number | null => {
    const available = type?.question_counts?.[level] ?? 0;
    if (!type || !available) return null;
    return Math.min(Math.max(type.default_question_count || 1, 1), available, maxInterviewQuestionCount);
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (interviewTypes.length && !newInterviewData.interview_type_id) {
      const firstType = interviewTypes[0];
      const firstLevel = firstType.levels[0] || 'junior';
      setNewInterviewData({
        interview_type_id: firstType.id,
        level: firstLevel,
        question_count: resolveDefaultQuestionCount(firstType, firstLevel),
      });
    }
  }, [interviewTypes, newInterviewData.interview_type_id]);

  const selectedType = useMemo(
    () => interviewTypes.find((item) => item.id === newInterviewData.interview_type_id),
    [interviewTypes, newInterviewData.interview_type_id],
  );
  const selectedQuestionCount = selectedType?.question_counts?.[newInterviewData.level] ?? 0;
  const selectedMaxQuestionCount = Math.min(selectedQuestionCount, maxInterviewQuestionCount);
  const selectedDefaultQuestionCount = resolveDefaultQuestionCount(selectedType, newInterviewData.level);

  const updateSelectedType = (interviewTypeId: number) => {
    const nextType = interviewTypes.find((item) => item.id === interviewTypeId);
    const nextLevel = nextType?.levels[0] || 'junior';
    setNewInterviewData({
      interview_type_id: interviewTypeId,
      level: nextLevel,
      question_count: resolveDefaultQuestionCount(nextType, nextLevel),
    });
  };

  const updateSelectedLevel = (level: string) => {
    setNewInterviewData({
      ...newInterviewData,
      level,
      question_count: resolveDefaultQuestionCount(selectedType, level),
    });
  };

  const updateQuestionCount = (value: string) => {
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || !selectedMaxQuestionCount) {
      setNewInterviewData({ ...newInterviewData, question_count: null });
      return;
    }
    const nextCount = Math.min(Math.max(Math.trunc(parsed), 1), selectedMaxQuestionCount);
    setNewInterviewData({ ...newInterviewData, question_count: nextCount });
  };

  const loadDashboard = async () => {
    setLoadError(null);
    try {
      const [interviewData, typeData] = await Promise.all([getInterviews(), getInterviewTypes()]);
      setInterviews(interviewData);
      setInterviewTypes(typeData);
    } catch (error) {
      console.error('Не удалось загрузить панель', error);
      setLoadError(getApiErrorMessage(error, 'Не удалось загрузить данные панели'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateInterview = async () => {
    if (!newInterviewData.interview_type_id || !selectedMaxQuestionCount) return;
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
    { label: 'Банк вопросов', value: interviewTypes.length, icon: <Insights />, helper: 'активных типов интервью' },
  ];

  return (
    <Container maxWidth="xl" sx={{ px: { xs: 0, md: 1 }, mb: 4 }}>
      <Paper
        sx={{
          p: { xs: 3, md: 4.5 },
          mb: 3,
          borderRadius: { xs: '24px', md: '28px' },
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
              {user?.full_name || 'Кандидат'}, выберите собеседование из банка IMock
            </Typography>
            <Typography sx={{ mt: 2, maxWidth: 760, color: 'rgba(239,246,239,0.76)', lineHeight: 1.7 }}>
              Вопросы заранее подготовлены и сохранены в базе. AI-интервьюер использует эталонный ответ,
              критерии оценки и историю диалога, чтобы задавать уточнения и формировать итог.
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Stack spacing={1.5}>
              <Button
                variant="contained"
                size="large"
                startIcon={<AddIcon />}
                onClick={() => setOpenDialog(true)}
                sx={{
                  bgcolor: '#FBF8F1',
                  color: 'primary.main',
                  '&:hover': { bgcolor: '#F3E7D2' },
                }}
              >
                Новое mock-собеседование
              </Button>
              <Button variant="outlined" sx={{ color: '#EFF6EF', borderColor: 'rgba(255,255,255,0.35)' }} onClick={() => navigate('/profile')}>
                Открыть прогресс
              </Button>
            </Stack>
          </Grid>
        </Grid>
      </Paper>

      {loadError && (
        <Alert severity="error" sx={{ mb: 3 }} action={<Button color="inherit" size="small" onClick={loadDashboard}>Повторить</Button>}>
          {loadError}
        </Alert>
      )}

      <Grid container spacing={3}>
        {metrics.map((item) => (
          <Grid size={{ xs: 12, md: 4 }} key={item.label}>
            <Paper sx={{ p: 3, height: '100%', borderRadius: '16px', bgcolor: 'rgba(255,255,255,0.64)' }}>
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
                <Box sx={{ display: 'grid', placeItems: 'center', width: 48, height: 48, borderRadius: '12px', bgcolor: 'rgba(238,243,232,0.9)', color: 'primary.main' }}>
                  {item.icon}
                </Box>
              </Box>
            </Paper>
          </Grid>
        ))}

        <Grid size={{ xs: 12, md: 4 }}>
          <Paper sx={{ p: 3, height: '100%', borderRadius: '20px', bgcolor: 'rgba(255,255,255,0.64)' }}>
            <Typography variant="h5" gutterBottom>
              Доступные направления
            </Typography>
            <Stack spacing={1} sx={{ mt: 2 }}>
              {interviewTypes.map((item) => (
                <Paper key={item.id} variant="outlined" sx={{ px: 1.6, py: 1.1, borderRadius: '12px', bgcolor: 'rgba(251,248,241,0.74)' }}>
                  <Typography variant="subtitle2">{item.title}</Typography>
                </Paper>
              ))}
            </Stack>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 8 }}>
          <Paper sx={{ p: { xs: 2.5, md: 3 }, height: '100%', borderRadius: '20px', bgcolor: 'rgba(255,255,255,0.64)' }}>
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
                    onClick={() => navigate(interview.status === InterviewStatus.FINISHED ? `/interviews/${interview.id}/result` : `/interviews/${interview.id}`)}
                    sx={{ mb: 1.2, border: '1px solid rgba(21, 57, 38, 0.1)', borderRadius: '12px', bgcolor: 'rgba(255,255,255,0.56)', alignItems: 'flex-start', gap: 1.5 }}
                  >
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1} flexWrap="wrap">
                          <Typography variant="subtitle1" component="span" fontWeight={900}>
                            {interview.interview_type_title}
                          </Typography>
                          <Chip label={levelLabels[interview.level] || interview.level} size="small" variant="outlined" />
                          <Chip label={interview.role} size="small" variant="outlined" />
                          {interview.question_limit && <Chip label={`${interview.question_limit} вопросов`} size="small" variant="outlined" />}
                        </Box>
                      }
                      secondary={`Этап: ${stageLabels[interview.stage] || interview.stage}. Создано: ${new Date(interview.started_at).toLocaleDateString('ru-RU')}`}
                    />
                    <Stack spacing={1} alignItems="flex-end" sx={{ flexShrink: 0, mt: 0.5 }}>
                      <Chip label={interview.status === InterviewStatus.ACTIVE ? 'Активно' : 'Завершено'} color={interview.status === InterviewStatus.ACTIVE ? 'success' : 'default'} size="small" />
                      {interview.status === InterviewStatus.FINISHED && (
                        <Stack direction="row" gap={1} flexWrap="wrap" justifyContent="flex-end">
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<Assessment />}
                            onClick={(event) => {
                              event.stopPropagation();
                              navigate(`/interviews/${interview.id}/result`);
                            }}
                          >
                            Результат
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<Chat />}
                            onClick={(event) => {
                              event.stopPropagation();
                              navigate(`/interviews/${interview.id}`);
                            }}
                          >
                            Диалог
                          </Button>
                        </Stack>
                      )}
                    </Stack>
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
            Выберите направление и уровень. Вопросы будут взяты из банка IMock.
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 1 }}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Тип собеседования</InputLabel>
              <Select
                value={newInterviewData.interview_type_id || ''}
                label="Тип собеседования"
                onChange={(event) => {
                  updateSelectedType(Number(event.target.value));
                }}
              >
                {interviewTypes.map((item) => (
                  <MenuItem value={item.id} key={item.id}>
                    {item.title}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth margin="normal">
              <InputLabel>Уровень</InputLabel>
              <Select
                value={newInterviewData.level}
                label="Уровень"
                onChange={(event) => updateSelectedLevel(event.target.value)}
              >
                {(selectedType?.levels || []).map((level) => (
                  <MenuItem value={level} key={level}>
                    {levelLabels[level] || level}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              fullWidth
              margin="normal"
              type="number"
              label="Количество вопросов"
              value={newInterviewData.question_count ?? ''}
              disabled={!selectedMaxQuestionCount}
              inputProps={{ min: 1, max: selectedMaxQuestionCount || 1 }}
              onChange={(event) => updateQuestionCount(event.target.value)}
              helperText={
                selectedMaxQuestionCount
                  ? `Можно выбрать от 1 до ${selectedMaxQuestionCount}. В банке доступно: ${selectedQuestionCount}. Дефолт: ${selectedDefaultQuestionCount}.`
                  : 'Для выбранного уровня пока нет активных вопросов.'
              }
            />
            {selectedType && (
              <Paper variant="outlined" sx={{ mt: 2, p: 2, borderRadius: '16px', bgcolor: 'rgba(238,243,232,0.7)' }}>
                <Typography variant="subtitle2">{selectedType.role}</Typography>
                <Typography color="text.secondary">{selectedType.technology_stack}</Typography>
                <Typography color="text.secondary" sx={{ mt: 1 }}>
                  Активных вопросов для уровня: {selectedQuestionCount}
                </Typography>
                {!selectedQuestionCount && (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    Для выбранного уровня пока нет активных вопросов. Администратор должен заполнить банк вопросов.
                  </Alert>
                )}
              </Paper>
            )}
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button onClick={() => setOpenDialog(false)}>Отмена</Button>
          <Button onClick={handleCreateInterview} variant="contained" disabled={!newInterviewData.interview_type_id || !selectedMaxQuestionCount || !newInterviewData.question_count || creating}>
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
