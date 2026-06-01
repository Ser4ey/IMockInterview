import React, { useEffect, useState } from 'react';
import { Alert, Box, Button, Checkbox, Chip, Container, FormControlLabel, Grid, Paper, Stack, TextField, Typography } from '@mui/material';
import { Add, AutoAwesome } from '@mui/icons-material';
import { createAdminInterviewType, generateAdminQuestions, getAdminInterviewTypes } from '../../api/admin';
import type { InterviewType } from '../../types/interview';
import { getApiErrorMessage } from '../../api/errors';

const levels = ['junior', 'middle', 'senior'];

const AdminInterviewTypes: React.FC = () => {
  const [items, setItems] = useState<InterviewType[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    title: 'Backend Java-разработчик',
    role: 'Backend Java-разработчик',
    technology_stack: 'Java, Spring Boot, SQL, REST API',
    description: 'Mock-собеседование для backend-разработчика Java.',
    levels,
    is_active: true,
  });

  const load = async () => {
    try {
      setItems(await getAdminInterviewTypes());
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, 'Не удалось загрузить типы собеседований'));
    }
  };

  useEffect(() => {
    load();
  }, []);

  const createType = async () => {
    try {
      await createAdminInterviewType(form);
      await load();
    } catch (createError) {
      setError(getApiErrorMessage(createError, 'Не удалось создать тип собеседования'));
    }
  };

  const generate = async (item: InterviewType, level: string) => {
    try {
      await generateAdminQuestions(item.id, level, 3);
      await load();
    } catch (generateError) {
      setError(getApiErrorMessage(generateError, 'Не удалось сгенерировать вопросы'));
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
            <Stack spacing={2}>
              {items.map((item) => (
                <Paper key={item.id} variant="outlined" sx={{ p: 2.5, borderRadius: '14px', bgcolor: 'rgba(251,248,241,0.72)' }}>
                  <Box display="flex" justifyContent="space-between" gap={2} flexWrap="wrap">
                    <Box>
                      <Typography variant="h6">{item.title}</Typography>
                      <Typography color="text.secondary">{item.technology_stack}</Typography>
                      <Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 1 }}>
                        {item.levels.map((level) => (
                          <Chip key={level} label={`${level}: ${item.question_counts[level] || 0}`} />
                        ))}
                      </Stack>
                    </Box>
                    <Stack direction="row" gap={1} flexWrap="wrap" alignItems="center">
                      {item.levels.map((level) => (
                        <Button key={level} variant="outlined" startIcon={<AutoAwesome />} onClick={() => generate(item, level)}>
                          {level}
                        </Button>
                      ))}
                    </Stack>
                  </Box>
                </Paper>
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default AdminInterviewTypes;
