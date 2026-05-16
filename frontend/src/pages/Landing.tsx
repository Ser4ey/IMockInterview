import React, { useEffect } from 'react';
import { alpha } from '@mui/material/styles';
import { Box, Button, Chip, Container, Grid, Paper, Stack, Typography } from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import InsightsIcon from '@mui/icons-material/Insights';
import RouteIcon from '@mui/icons-material/Route';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const advantages = [
  {
    title: 'Интервью под вашу роль',
    text: 'Выберите специализацию, уровень и формат: от теории до полного mock-интервью.',
    icon: <RouteIcon />,
  },
  {
    title: 'Живой диалог',
    text: 'AI-интервьюер задает уточняющие вопросы и помогает тренировать структуру ответа.',
    icon: <ChatBubbleOutlineIcon />,
  },
  {
    title: 'Понятный результат',
    text: 'После тренировки вы видите оценку, критерии и рекомендации для подготовки.',
    icon: <InsightsIcon />,
  },
];

const Landing: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 4, md: 7 } }}>
      <Grid container spacing={3} alignItems="stretch">
        <Grid size={{ xs: 12, md: 7 }}>
          <Paper
            sx={{
              minHeight: { xs: 'auto', md: 560 },
              p: { xs: 3, sm: 5, md: 7 },
              borderRadius: 7,
              bgcolor: 'rgba(255,255,255,0.62)',
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            <Box
              sx={{
                position: 'absolute',
                width: 260,
                height: 260,
                borderRadius: '50%',
                right: -70,
                top: -70,
                bgcolor: alpha('#B1D5BE', 0.34),
                filter: 'blur(4px)',
              }}
            />
            <Box sx={{ position: 'relative' }}>
              <Chip
                icon={<AutoAwesomeIcon />}
                label="AI-интервьюер для спокойной подготовки"
                sx={{ mb: 3, bgcolor: 'rgba(238, 243, 232, 0.95)' }}
              />
              <Typography
                variant="h1"
                component="h1"
                sx={{
                  maxWidth: 820,
                  fontSize: { xs: 46, sm: 64, md: 86 },
                }}
              >
                Тренируйте собеседования без стресса и случайности
              </Typography>
              <Typography
                variant="h6"
                color="text.secondary"
                sx={{ maxWidth: 660, mt: 3, lineHeight: 1.75, fontWeight: 500 }}
              >
                IMock проводит mock-собеседование по выбранной специализации, задает вопросы
                как интервьюер и показывает понятный результат: оценку, критерии и зоны роста.
              </Typography>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ mt: 4 }}>
                <Button variant="contained" size="large" onClick={() => navigate('/register')}>
                  Начать подготовку
                </Button>
                <Button variant="outlined" size="large" onClick={() => navigate('/login')}>
                  Войти в аккаунт
                </Button>
              </Stack>
            </Box>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <Paper
            sx={{
              height: '100%',
              minHeight: 560,
              p: { xs: 3, sm: 4 },
              borderRadius: 7,
              color: '#EFF6EF',
              bgcolor: 'primary.main',
              background:
                'radial-gradient(circle at 18% 0%, rgba(177,213,190,.34), transparent 34%), linear-gradient(145deg, #132018, #183827 62%, #2F5D46)',
            }}
          >
            <Typography variant="overline" sx={{ opacity: 0.74, fontWeight: 900 }}>
              Пример тренировки
            </Typography>
            <Typography variant="h4" sx={{ mt: 1, maxWidth: 420 }}>
              Backend-разработка, Middle, полное интервью
            </Typography>
            <Stack spacing={1.5} sx={{ mt: 4 }}>
              <Paper sx={{ p: 2, borderRadius: 4, bgcolor: 'rgba(255,255,255,0.1)', color: 'inherit', borderColor: 'rgba(255,255,255,0.14)' }}>
                Расскажите, как вы проектируете REST API и выбираете структуру эндпоинтов?
              </Paper>
              <Paper sx={{ p: 2, borderRadius: 4, bgcolor: '#FBF8F1', color: 'text.primary' }}>
                Я начинаю с ресурсов, HTTP-методов, кодов статусов, валидации и контроля доступа.
              </Paper>
              <Paper sx={{ p: 2, borderRadius: 4, bgcolor: 'rgba(255,255,255,0.1)', color: 'inherit', borderColor: 'rgba(255,255,255,0.14)' }}>
                Хорошо. А как бы вы спроектировали пагинацию для большого списка данных?
              </Paper>
            </Stack>
            <Grid container spacing={1.5} sx={{ mt: 4 }}>
              <Grid size={4}>
                <Paper sx={{ p: 2, borderRadius: 4, bgcolor: 'rgba(255,255,255,0.1)', color: 'inherit', textAlign: 'center', borderColor: 'rgba(255,255,255,0.14)' }}>
                  <Typography variant="h4">8.5</Typography>
                  <Typography variant="caption" sx={{ opacity: 0.74 }}>оценка</Typography>
                </Paper>
              </Grid>
              <Grid size={4}>
                <Paper sx={{ p: 2, borderRadius: 4, bgcolor: 'rgba(255,255,255,0.1)', color: 'inherit', textAlign: 'center', borderColor: 'rgba(255,255,255,0.14)' }}>
                  <Typography variant="h4">12</Typography>
                  <Typography variant="caption" sx={{ opacity: 0.74 }}>вопросов</Typography>
                </Paper>
              </Grid>
              <Grid size={4}>
                <Paper sx={{ p: 2, borderRadius: 4, bgcolor: 'rgba(255,255,255,0.1)', color: 'inherit', textAlign: 'center', borderColor: 'rgba(255,255,255,0.14)' }}>
                  <Typography variant="h4">30м</Typography>
                  <Typography variant="caption" sx={{ opacity: 0.74 }}>сессия</Typography>
                </Paper>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>

      <Grid container spacing={2.5} sx={{ mt: 3 }}>
        {advantages.map((advantage) => (
          <Grid size={{ xs: 12, md: 4 }} key={advantage.title}>
            <Paper sx={{ p: 3, height: '100%', borderRadius: 5, bgcolor: 'rgba(255,255,255,0.58)' }}>
              <Box
                sx={{
                  width: 46,
                  height: 46,
                  display: 'grid',
                  placeItems: 'center',
                  borderRadius: 3,
                  color: 'primary.main',
                  bgcolor: 'rgba(238,243,232,0.9)',
                  mb: 2,
                }}
              >
                {advantage.icon}
              </Box>
              <Typography variant="h6">{advantage.title}</Typography>
              <Typography color="text.secondary" sx={{ mt: 1, lineHeight: 1.7 }}>
                {advantage.text}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

export default Landing;
