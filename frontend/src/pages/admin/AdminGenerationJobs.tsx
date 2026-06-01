import React, { useEffect, useState } from 'react';
import { Alert, Chip, Container, Paper, Stack, Typography } from '@mui/material';
import { getAdminGenerationJobs } from '../../api/admin';
import type { GenerationJob } from '../../types/interview';
import { getApiErrorMessage } from '../../api/errors';

const AdminGenerationJobs: React.FC = () => {
  const [jobs, setJobs] = useState<GenerationJob[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAdminGenerationJobs()
      .then(setJobs)
      .catch((loadError) => setError(getApiErrorMessage(loadError, 'Не удалось загрузить задания генерации')));
  }, []);

  return (
    <Container maxWidth="xl" sx={{ px: { xs: 0, md: 1 }, mb: 4 }}>
      <Paper sx={{ p: 3, borderRadius: '20px', bgcolor: 'rgba(255,255,255,0.66)' }}>
        <Typography variant="h4">Статус генерации вопросов</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>Техническая история формирования банка вопросов.</Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Stack spacing={2}>
          {jobs.map((job) => (
            <Paper key={job.id} variant="outlined" sx={{ p: 2.5, borderRadius: '14px', bgcolor: 'rgba(251,248,241,0.72)' }}>
              <Stack direction="row" gap={1} flexWrap="wrap" alignItems="center">
                <Typography variant="h6">{job.interview_type_title}</Typography>
                <Chip label={job.level} />
                <Chip label={job.status} color={job.status === 'completed' ? 'success' : job.status === 'failed' ? 'error' : 'default'} />
                <Chip label={`${job.generated_count}/${job.requested_count} вопросов`} variant="outlined" />
                <Chip label={`provider: ${job.provider}`} variant="outlined" />
                <Chip label={job.context_used ? 'context: yes' : 'context: no'} variant="outlined" />
                {job.skipped_count > 0 && <Chip label={`skipped: ${job.skipped_count}`} color="warning" variant="outlined" />}
              </Stack>
              {job.raw_response_preview && (
                <Typography color="text.secondary" sx={{ mt: 1, wordBreak: 'break-word' }}>
                  {job.raw_response_preview}
                </Typography>
              )}
              {job.error_message && <Alert severity="error" sx={{ mt: 2 }}>{job.error_message}</Alert>}
              <Typography color="text.secondary" sx={{ mt: 1 }}>
                Создано: {new Date(job.created_at).toLocaleString('ru-RU')}
              </Typography>
            </Paper>
          ))}
        </Stack>
      </Paper>
    </Container>
  );
};

export default AdminGenerationJobs;
