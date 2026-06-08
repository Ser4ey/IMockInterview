import React, { useEffect, useState } from 'react';
import { Alert, Box, Button, Chip, Container, FormControl, Grid, InputLabel, MenuItem, Paper, Select, Stack, TextField, Typography } from '@mui/material';
import { Block, CheckCircle, Save } from '@mui/icons-material';
import { createAdminQuestion, disableAdminQuestion, enableAdminQuestion, getAdminInterviewTypes, getAdminQuestions } from '../../api/admin';
import type { InterviewType, Question } from '../../types/interview';
import { getApiErrorMessage } from '../../api/errors';

const AdminQuestions: React.FC = () => {
  const [types, setTypes] = useState<InterviewType[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filterTypeId, setFilterTypeId] = useState<number>(0);
  const [filterLevel, setFilterLevel] = useState('junior');
  const [form, setForm] = useState({
    question_text: '',
    expected_answer: '',
    evaluation_criteria: '',
    tags: '',
  });

  const load = async () => {
    try {
      const nextTypes = await getAdminInterviewTypes();
      setTypes(nextTypes);
      setQuestions(
        nextTypes.length
          ? await getAdminQuestions({
              ...(filterTypeId ? { interview_type_id: filterTypeId } : {}),
              level: filterLevel,
              include_disabled: true,
            })
          : [],
      );
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, 'Не удалось загрузить банк вопросов'));
    }
  };

  useEffect(() => {
    load();
  }, [filterTypeId, filterLevel]);

  const createQuestion = async () => {
    try {
      await createAdminQuestion({
        interview_type_id: filterTypeId,
        level: filterLevel,
        question_text: form.question_text,
        expected_answer: form.expected_answer,
        evaluation_criteria: form.evaluation_criteria.split('\n').map((item) => item.trim()).filter(Boolean),
        tags: form.tags.split(',').map((item) => item.trim()).filter(Boolean),
        is_active: true,
      });
      setForm({ question_text: '', expected_answer: '', evaluation_criteria: '', tags: '' });
      await load();
    } catch (createError) {
      setError(getApiErrorMessage(createError, 'Не удалось создать вопрос'));
    }
  };

  const toggleQuestion = async (question: Question) => {
    try {
      if (question.is_active) {
        await disableAdminQuestion(question.id);
      } else {
        await enableAdminQuestion(question.id);
      }
      await load();
    } catch (toggleError) {
      setError(getApiErrorMessage(toggleError, 'Не удалось изменить статус вопроса'));
    }
  };

  return (
    <Container maxWidth="xl" sx={{ px: { xs: 0, md: 1 }, mb: 4 }}>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Paper sx={{ p: 3, borderRadius: '20px', bgcolor: 'rgba(255,255,255,0.66)' }}>
            <Typography variant="h4">Ручной вопрос</Typography>
            {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
            <Stack spacing={2} sx={{ mt: 2 }}>
              <FormControl fullWidth>
                <InputLabel>Тип</InputLabel>
                <Select value={filterTypeId} label="Тип" onChange={(event) => setFilterTypeId(Number(event.target.value))}>
                  <MenuItem value={0}>Все типы</MenuItem>
                  {types.map((item) => (
                    <MenuItem key={item.id} value={item.id}>{item.title}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Уровень</InputLabel>
                <Select value={filterLevel} label="Уровень" onChange={(event) => setFilterLevel(event.target.value)}>
                  <MenuItem value="junior">Junior</MenuItem>
                  <MenuItem value="middle">Middle</MenuItem>
                  <MenuItem value="senior">Senior</MenuItem>
                </Select>
              </FormControl>
              <TextField multiline minRows={2} label="Вопрос" value={form.question_text} onChange={(event) => setForm({ ...form, question_text: event.target.value })} />
              <TextField multiline minRows={4} label="Эталонный ответ" value={form.expected_answer} onChange={(event) => setForm({ ...form, expected_answer: event.target.value })} />
              <TextField multiline minRows={3} label="Критерии, каждый с новой строки" value={form.evaluation_criteria} onChange={(event) => setForm({ ...form, evaluation_criteria: event.target.value })} />
              <TextField label="Теги через запятую" value={form.tags} onChange={(event) => setForm({ ...form, tags: event.target.value })} />
              <Button variant="contained" startIcon={<Save />} disabled={!filterTypeId || !form.question_text.trim()} onClick={createQuestion}>
                Сохранить вопрос
              </Button>
            </Stack>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 8 }}>
          <Paper sx={{ p: 3, borderRadius: '20px', bgcolor: 'rgba(255,255,255,0.66)' }}>
            <Typography variant="h4">Банк вопросов</Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>Просмотр эталонных ответов, критериев и активности вопросов.</Typography>
            <Stack spacing={2}>
              {questions.map((question) => (
                <Paper key={question.id} variant="outlined" sx={{ p: 2.5, borderRadius: '14px', bgcolor: question.is_active ? 'rgba(251,248,241,0.72)' : 'rgba(238,238,238,0.72)' }}>
                  <Stack spacing={1.75}>
                    <Box>
                      <Typography variant="h6" sx={{ overflowWrap: 'anywhere' }}>{question.question_text}</Typography>
                      <Typography color="text.secondary" sx={{ mt: 1, overflowWrap: 'anywhere' }}>{question.expected_answer}</Typography>
                    </Box>
                    <Stack direction="row" gap={1} flexWrap="wrap">
                      {question.source?.title && <Chip label={`Источник: ${question.source.title}`} size="small" variant="outlined" />}
                      {question.question_hash && <Chip label={`hash: ${question.question_hash.slice(0, 8)}`} size="small" variant="outlined" />}
                    </Stack>
                    <Stack direction="row" gap={1} flexWrap="wrap">
                      {question.evaluation_criteria.map((item) => <Chip key={item} label={item} />)}
                      {question.tags.map((item) => <Chip key={item} label={item} variant="outlined" />)}
                    </Stack>
                    <Box display="flex" justifyContent="flex-end">
                      <Button
                        variant="outlined"
                        startIcon={question.is_active ? <Block /> : <CheckCircle />}
                        onClick={() => toggleQuestion(question)}
                        sx={{ minWidth: 132, whiteSpace: 'nowrap' }}
                      >
                      {question.is_active ? 'Отключить' : 'Включить'}
                      </Button>
                    </Box>
                  </Stack>
                </Paper>
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default AdminQuestions;
