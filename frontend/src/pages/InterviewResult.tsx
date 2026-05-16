import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Alert, Box, Button, Chip, CircularProgress, Container, Grid, LinearProgress, Paper, Stack, Typography } from '@mui/material';
import { ArrowBack, CheckCircle, Psychology, TipsAndUpdates, Warning } from '@mui/icons-material';
import { getInterview, getInterviewResult } from '../api/interviews';
import { getApiErrorMessage } from '../api/errors';
import { InterviewStatus } from '../types/interview';
import type { InterviewResult as InterviewResultType, InterviewSession } from '../types/interview';

const criteriaLabels: Array<[keyof InterviewResultType, string]> = [
  ['correctness', 'Корректность'],
  ['completeness', 'Полнота'],
  ['depth', 'Глубина'],
  ['communication', 'Коммуникация'],
];

const InterviewResult: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [interview, setInterview] = useState<InterviewSession | null>(null);
  const [result, setResult] = useState<InterviewResultType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const interviewId = Number(id);
    Promise.all([getInterview(interviewId), getInterviewResult(interviewId)])
      .then(([interviewData, resultData]) => {
        setInterview(interviewData);
        setResult(resultData);
      })
      .catch((loadError) => {
        console.error(loadError);
        setError(getApiErrorMessage(loadError, 'Не удалось загрузить результат интервью'));
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
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
          {error}
        </Alert>
      </Container>
    );
  }

  if (!interview || !result) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="info">Результат пока недоступен.</Alert>
      </Container>
    );
  }

  const score10 = (result.score / 10).toFixed(1);

  return (
    <Container maxWidth="xl" sx={{ px: { xs: 0, md: 1 }, mb: 4 }}>
      <Button startIcon={<ArrowBack />} onClick={() => navigate('/dashboard')} sx={{ mb: 2 }}>
        К панели
      </Button>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Paper
            sx={{
              p: { xs: 3, md: 4 },
              borderRadius: 7,
              height: '100%',
              color: '#EFF6EF',
              bgcolor: 'primary.main',
              background:
                'radial-gradient(circle at 18% 0%, rgba(177,213,190,.32), transparent 34%), linear-gradient(145deg, #132018, #183827)',
            }}
          >
            <Box display="flex" alignItems="center" gap={1.5}>
              {interview.status === InterviewStatus.FINISHED ? <CheckCircle /> : <Warning />}
              <Typography variant="overline" sx={{ opacity: 0.76, fontWeight: 900 }}>
                Итог собеседования
              </Typography>
            </Box>
            <Typography variant="h1" sx={{ mt: 3, fontSize: { xs: 72, md: 88 } }}>
              {score10}
            </Typography>
            <Typography variant="h5" sx={{ opacity: 0.82 }}>
              из 10
            </Typography>
            <LinearProgress
              variant="determinate"
              value={result.score}
              sx={{ mt: 3, bgcolor: 'rgba(255,255,255,0.16)', '& .MuiLinearProgress-bar': { bgcolor: '#F3E7D2' } }}
            />
            <Typography sx={{ mt: 3, color: 'rgba(239,246,239,0.76)', lineHeight: 1.7 }}>
              {interview.specialization} · {interview.level}. Результат сохранен в истории подготовки.
            </Typography>
            <Stack direction="row" flexWrap="wrap" gap={1} sx={{ mt: 3 }}>
              <Chip label="Технические знания" sx={{ bgcolor: 'rgba(255,255,255,0.12)', color: 'inherit' }} />
              <Chip label="Коммуникация" sx={{ bgcolor: 'rgba(255,255,255,0.12)', color: 'inherit' }} />
            </Stack>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 8 }}>
          <Paper sx={{ p: { xs: 3, md: 4 }, borderRadius: 7, bgcolor: 'rgba(255,255,255,0.66)' }}>
            <Typography variant="h4">Разбор по критериям</Typography>
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              Оценка показывает, насколько ответ был точным, полным и понятным для интервьюера.
            </Typography>

            <Grid container spacing={2} sx={{ mt: 2 }}>
          {criteriaLabels.map(([key, label]) => (
            <Grid size={{ xs: 12, sm: 6 }} key={key}>
              <Paper variant="outlined" sx={{ p: 2.5, borderRadius: 5, bgcolor: 'rgba(251,248,241,0.76)' }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" gap={2}>
                  <Typography variant="subtitle2">{label}</Typography>
                  <Typography variant="h5">{(Number(result[key]) / 10).toFixed(1)}</Typography>
                </Box>
                <LinearProgress variant="determinate" value={Number(result[key])} />
              </Paper>
            </Grid>
          ))}
            </Grid>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, borderRadius: 6, bgcolor: 'rgba(255,255,255,0.66)', height: '100%' }}>
            <Box display="flex" alignItems="center" gap={1.5} mb={2}>
              <Psychology color="primary" />
              <Typography variant="h5">Сильные стороны</Typography>
            </Box>
            <Stack spacing={1.2}>
              <Paper variant="outlined" sx={{ p: 2, borderRadius: 4, bgcolor: 'rgba(238,243,232,0.7)' }}>
                Хорошая структура ответа и понимание базовых принципов проектирования API.
              </Paper>
              <Paper variant="outlined" sx={{ p: 2, borderRadius: 4, bgcolor: 'rgba(238,243,232,0.7)' }}>
                Уверенная коммуникация: ответы звучат последовательно и без лишней воды.
              </Paper>
            </Stack>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, borderRadius: 6, bgcolor: 'rgba(255,255,255,0.66)', height: '100%' }}>
            <Box display="flex" alignItems="center" gap={1.5} mb={2}>
              <TipsAndUpdates color="primary" />
              <Typography variant="h5">Рекомендации</Typography>
            </Box>
            <Typography sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.75, color: 'text.secondary' }}>
              {result.recommendations}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Box display="flex" justifyContent="center" mt={3}>
        <Button variant="contained" onClick={() => navigate('/dashboard')}>
          Вернуться к списку интервью
        </Button>
      </Box>
    </Container>
  );
};

export default InterviewResult;
