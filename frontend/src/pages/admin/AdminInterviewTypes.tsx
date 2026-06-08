import React, { useEffect, useState } from 'react';
import { Alert, Box, Button, Checkbox, Chip, Container, FormControl, FormControlLabel, Grid, InputLabel, MenuItem, Paper, Select, Snackbar, Stack, TextField, Typography } from '@mui/material';
import { Add, AutoAwesome } from '@mui/icons-material';
import { createAdminInterviewType, generateAdminQuestions, getAdminInterviewTypes, getAdminLlmStatus } from '../../api/admin';
import type { GenerationJob, InterviewType, LlmStatus } from '../../types/interview';
import { getApiErrorMessage } from '../../api/errors';

const levels = ['junior', 'middle', 'senior'];
const maxInterviewQuestionCount = 10;

const AdminInterviewTypes: React.FC = () => {
  const [items, setItems] = useState<InterviewType[]>([]);
  const [llmStatus, setLlmStatus] = useState<LlmStatus | null>(null);
  const [latestJob, setLatestJob] = useState<GenerationJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generationNotice, setGenerationNotice] = useState<string | null>(null);
  const [form, setForm] = useState({
    title: 'Backend Java-разработчик',
    role: 'Backend Java-разработчик',
    technology_stack: 'Java, Spring Boot, SQL, REST API',
    description: 'Mock-собеседование для backend-разработчика Java.',
    levels,
    default_question_count: 3,
    is_active: true,
    auto_generate_questions: false,
    questions_per_level: 3,
  });
  const [generationForm, setGenerationForm] = useState({
    interview_type_id: 0,
    level: 'junior',
    requested_count: 3,
  });

  const load = async () => {
    try {
      const nextItems = await getAdminInterviewTypes();
      setItems(nextItems);
      setGenerationForm((current) => {
        if (current.interview_type_id || !nextItems.length) return current;
        const firstType = nextItems[0];
        const firstLevel = firstType.levels[0] || 'junior';
        return {
          interview_type_id: firstType.id,
          level: firstLevel,
          requested_count: firstType.default_question_count || 3,
        };
      });
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, 'Не удалось загрузить типы собеседований'));
    }
  };

  useEffect(() => {
    load();
    getAdminLlmStatus()
      .then(setLlmStatus)
      .catch((statusError) => setError(getApiErrorMessage(statusError, 'Не удалось загрузить статус LLM')));
  }, []);

  const createType = async () => {
    try {
      setError(null);
      if (form.auto_generate_questions) {
        setGenerationNotice(`Генерация успешно запущена: ${form.questions_per_level} вопросов для каждого выбранного уровня.`);
      }
      await createAdminInterviewType(form);
      await load();
    } catch (createError) {
      setError(getApiErrorMessage(createError, 'Не удалось создать тип собеседования'));
    }
  };

  const selectedGenerationType = items.find((item) => item.id === generationForm.interview_type_id);

  const selectGenerationType = (interviewTypeId: number) => {
    const nextType = items.find((item) => item.id === interviewTypeId);
    const nextLevel = nextType?.levels[0] || 'junior';
    setGenerationForm({
      interview_type_id: interviewTypeId,
      level: nextLevel,
      requested_count: nextType?.default_question_count || 3,
    });
  };

  const generate = async () => {
    if (!generationForm.interview_type_id) return;
    setGenerating(true);
    setError(null);
    setLatestJob(null);
    setGenerationNotice(`Генерация успешно запущена: ${generationForm.requested_count} вопросов для уровня ${generationForm.level}.`);
    try {
      const job = await generateAdminQuestions(
        generationForm.interview_type_id,
        generationForm.level,
        generationForm.requested_count,
      );
      setLatestJob(job);
      await load();
    } catch (generateError) {
      setError(getApiErrorMessage(generateError, 'Не удалось сгенерировать вопросы'));
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ px: { xs: 0, md: 1 }, mb: 4 }}>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Paper sx={{ p: 3, borderRadius: '20px', bgcolor: 'rgba(255,255,255,0.66)' }}>
            <Typography variant="h4">Новый тип</Typography>
            <Stack spacing={2} sx={{ mt: 2 }}>
              <TextField label="Название" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
              <TextField label="Роль" value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })} />
              <TextField label="Стек" value={form.technology_stack} onChange={(event) => setForm({ ...form, technology_stack: event.target.value })} />
              <TextField multiline minRows={3} label="Описание" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
              <TextField
                type="number"
                label="Вопросов по умолчанию"
                value={form.default_question_count}
                inputProps={{ min: 1, max: maxInterviewQuestionCount }}
                onChange={(event) =>
                  setForm({
                    ...form,
                    default_question_count: Math.min(Math.max(1, Number(event.target.value) || 1), maxInterviewQuestionCount),
                  })
                }
                helperText="Этот лимит будет подставлен пользователю при запуске интервью. Максимум: 10."
              />
              <Stack direction="row" gap={1} flexWrap="wrap">
                {levels.map((level) => (
                  <FormControlLabel
                    key={level}
                    control={
                      <Checkbox
                        checked={form.levels.includes(level)}
                        onChange={(event) =>
                          setForm({
                            ...form,
                            levels: event.target.checked ? [...form.levels, level] : form.levels.filter((item) => item !== level),
                          })
                        }
                      />
                    }
                    label={level}
                  />
                ))}
              </Stack>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={form.auto_generate_questions}
                    onChange={(event) => setForm({ ...form, auto_generate_questions: event.target.checked })}
                  />
                }
                label="Сразу сгенерировать вопросы"
              />
              {form.auto_generate_questions && (
                <TextField
                  type="number"
                  label="Вопросов на уровень"
                  value={form.questions_per_level}
                  inputProps={{ min: 1, max: 20 }}
                  onChange={(event) => setForm({ ...form, questions_per_level: Math.max(1, Number(event.target.value) || 1) })}
                />
              )}
              <Button variant="contained" startIcon={<Add />} onClick={createType}>
                Создать
              </Button>
            </Stack>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 8 }}>
          <Paper sx={{ p: 3, borderRadius: '20px', bgcolor: 'rgba(255,255,255,0.66)' }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" gap={2} mb={2}>
              <Box>
                <Typography variant="h4">Типы собеседований</Typography>
                <Typography color="text.secondary">Управление направлениями и запуском генерации банка вопросов.</Typography>
              </Box>
            </Box>
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            {llmStatus && llmStatus.provider === 'mock' && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                Генерация сейчас работает в mock-режиме. Для реальных агентов включите LLM_MODE=yandex_agents и заполните Yandex AI Studio настройки.
              </Alert>
            )}
            {llmStatus && llmStatus.provider === 'yandex_agent' && !llmStatus.question_agent_configured && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                Включен режим yandex_agents, но агент генерации вопросов настроен не полностью.
              </Alert>
            )}
            <Paper variant="outlined" sx={{ p: 2.5, mb: 2, borderRadius: '14px', bgcolor: 'rgba(238,243,232,0.62)' }}>
              <Typography variant="h6">Генерация вопросов</Typography>
              <Grid container spacing={2} sx={{ mt: 0.5 }} alignItems="flex-start">
                <Grid size={{ xs: 12, md: 5 }}>
                  <FormControl fullWidth>
                    <InputLabel>Тип интервью</InputLabel>
                    <Select
                      value={generationForm.interview_type_id || ''}
                      label="Тип интервью"
                      onChange={(event) => selectGenerationType(Number(event.target.value))}
                    >
                      {items.map((item) => (
                        <MenuItem key={item.id} value={item.id}>{item.title}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <FormControl fullWidth>
                    <InputLabel>Уровень</InputLabel>
                    <Select
                      value={generationForm.level}
                      label="Уровень"
                      onChange={(event) => setGenerationForm({ ...generationForm, level: event.target.value })}
                    >
                      {(selectedGenerationType?.levels || levels).map((level) => (
                        <MenuItem key={level} value={level}>{level}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid size={{ xs: 12, md: 2 }}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Количество"
                    value={generationForm.requested_count}
                    inputProps={{ min: 1, max: 30 }}
                    onChange={(event) =>
                      setGenerationForm({
                        ...generationForm,
                        requested_count: Math.min(Math.max(Number(event.target.value) || 1, 1), 30),
                      })
                    }
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 2 }}>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<AutoAwesome />}
                    disabled={!generationForm.interview_type_id || generating}
                    onClick={generate}
                    sx={{ minHeight: 56 }}
                  >
                    {generating ? 'Генерирую...' : 'Запустить'}
                  </Button>
                </Grid>
              </Grid>
              <Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 2 }}>
                <Chip label={`provider: ${llmStatus?.provider || 'unknown'}`} variant="outlined" />
                {selectedGenerationType && (
                  <Chip
                    label={`Активно сейчас: ${selectedGenerationType.question_counts[generationForm.level] || 0}`}
                    variant="outlined"
                  />
                )}
              </Stack>
              {latestJob && (
                <Alert severity={latestJob.status === 'completed' ? 'success' : latestJob.status === 'failed' ? 'error' : 'info'} sx={{ mt: 2 }}>
                  Задание {latestJob.status}: сохранено {latestJob.generated_count} из {latestJob.requested_count}, пропущено {latestJob.skipped_count}, provider: {latestJob.provider}.
                  {latestJob.error_message ? ` Ошибка: ${latestJob.error_message}` : ''}
                </Alert>
              )}
            </Paper>
            <Stack spacing={2}>
              {items.map((item) => (
                <Paper key={item.id} variant="outlined" sx={{ p: 2.5, borderRadius: '14px', bgcolor: 'rgba(251,248,241,0.72)' }}>
                  <Box display="flex" justifyContent="space-between" gap={2} flexWrap="wrap">
                    <Box>
                      <Typography variant="h6">{item.title}</Typography>
                      <Typography color="text.secondary">{item.technology_stack}</Typography>
                      <Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 1 }}>
                        <Chip label={`по умолчанию: ${item.default_question_count}`} variant="outlined" />
                        {item.levels.map((level) => (
                          <Chip key={level} label={`${level}: ${item.question_counts[level] || 0}`} />
                        ))}
                      </Stack>
                    </Box>
                  </Box>
                </Paper>
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
      <Snackbar
        open={!!generationNotice}
        autoHideDuration={6000}
        onClose={() => setGenerationNotice(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="info" onClose={() => setGenerationNotice(null)} sx={{ width: '100%' }}>
          {generationNotice}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default AdminInterviewTypes;
