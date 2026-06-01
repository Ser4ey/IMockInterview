import React from 'react';
import { Box, Chip, Container, Grid, Paper, Stack, Typography } from '@mui/material';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import { useAuth } from '../context/AuthContext';

const ProfilePage: React.FC = () => {
  const { user } = useAuth();

  if (!user) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Typography>Загрузка профиля...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ px: { xs: 0, md: 1 }, mb: 4 }}>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Paper
            sx={{
              p: { xs: 3, md: 4 },
              borderRadius: { xs: '24px', md: '28px' },
              height: '100%',
              color: '#EFF6EF',
              bgcolor: 'primary.main',
              background:
                'radial-gradient(circle at 18% 0%, rgba(177,213,190,.32), transparent 34%), linear-gradient(145deg, #132018, #183827)',
            }}
          >
            <AccountCircleIcon sx={{ fontSize: 58, mb: 2 }} />
            <Typography variant="overline" sx={{ opacity: 0.72, fontWeight: 900 }}>
              Профиль кандидата
            </Typography>
            <Typography variant="h3" sx={{ mt: 1 }}>
              {user.full_name || 'Имя не указано'}
            </Typography>
            <Typography sx={{ mt: 1.5, color: 'rgba(239,246,239,0.76)' }}>{user.email}</Typography>
            <Stack direction="row" flexWrap="wrap" gap={1} sx={{ mt: 3 }}>
              <Chip label={user.is_active ? 'Активен' : 'Неактивен'} sx={{ bgcolor: 'rgba(255,255,255,0.12)', color: 'inherit' }} />
              {user.is_superuser && <Chip label="Администратор" color="warning" />}
            </Stack>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 8 }}>
          <Paper sx={{ p: { xs: 3, md: 4 }, borderRadius: '20px', bgcolor: 'rgba(255,255,255,0.66)', height: '100%' }}>
            <Box display="flex" alignItems="center" gap={1.5} mb={3}>
              <AccountCircleIcon color="primary" />
              <Box>
                <Typography variant="h4">Профиль подготовки</Typography>
                <Typography color="text.secondary">Основная информация о пользователе и рекомендации по тренировкам.</Typography>
              </Box>
            </Box>

            <Grid container spacing={2.5}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Paper variant="outlined" sx={{ p: 2.5, borderRadius: '14px', bgcolor: 'rgba(238,243,232,0.7)' }}>
                  <Typography variant="overline" color="text.secondary" fontWeight={900}>
                    Роль
                  </Typography>
                  <Typography variant="h3" sx={{ mt: 1 }}>
                    {user.is_superuser ? 'Admin' : 'User'}
                  </Typography>
                </Paper>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Paper variant="outlined" sx={{ p: 2.5, borderRadius: '14px', bgcolor: 'rgba(251,248,241,0.8)' }}>
                  <Typography variant="overline" color="text.secondary" fontWeight={900}>
                    Статус
                  </Typography>
                  <Typography variant="h3" sx={{ mt: 1 }}>
                    {user.is_active ? 'Активен' : 'Неактивен'}
                  </Typography>
                </Paper>
              </Grid>
            </Grid>

            <Paper variant="outlined" sx={{ mt: 3, p: 2.5, borderRadius: '14px', bgcolor: 'rgba(255,255,255,0.5)' }}>
              <Typography variant="h6">Рекомендация</Typography>
              <Typography color="text.secondary" sx={{ mt: 1, lineHeight: 1.7 }}>
                Для подготовки к ВКР-сценарию пройдите полное интервью по Python Backend и сравните
                результат с предыдущими тренировками в панели подготовки.
              </Typography>
            </Paper>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ProfilePage;
