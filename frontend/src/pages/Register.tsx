import React, { useState } from 'react';
import { Alert, Box, Button, Container, Paper, Stack, TextField, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import { getApiErrorMessage } from '../api/errors';
import { useAuth } from '../context/AuthContext';

const Register: React.FC = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await client.post('/auth/register', {
        email,
        password,
        full_name: fullName,
      });

      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);

      const loginResponse = await client.post('/auth/login/access-token', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      await login(loginResponse.data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Не удалось зарегистрироваться.'));
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 4, md: 8 } }}>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: '1.08fr 0.92fr' },
          gap: 3,
          alignItems: 'stretch',
        }}
      >
        <Paper sx={{ p: { xs: 3, md: 5 }, borderRadius: 7, bgcolor: 'rgba(255,255,255,0.72)' }}>
          <Typography variant="overline" color="text.secondary" fontWeight={900}>
            Новый аккаунт
          </Typography>
          <Typography variant="h4" component="h1" sx={{ mt: 1 }}>
            Создайте пространство для подготовки
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 1, mb: 3 }}>
            После регистрации вы сможете запускать mock-интервью, сохранять историю и
            отслеживать прогресс.
          </Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <form onSubmit={handleSubmit}>
            <Stack spacing={2}>
              <TextField
                label="Имя"
                fullWidth
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Александр Петров"
              />
              <TextField
                label="Email"
                fullWidth
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="alexander.demo@example.com"
              />
              <TextField
                label="Пароль"
                type="password"
                fullWidth
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <Button type="submit" variant="contained" fullWidth size="large">
                Создать аккаунт
              </Button>
              <Button variant="text" onClick={() => navigate('/login')}>
                Уже есть аккаунт? Войти
              </Button>
            </Stack>
          </form>
        </Paper>

        <Paper
          sx={{
            p: { xs: 3, md: 5 },
            borderRadius: 7,
            color: '#EFF6EF',
            bgcolor: 'primary.main',
            background:
              'radial-gradient(circle at 18% 0%, rgba(177,213,190,.32), transparent 34%), linear-gradient(145deg, #132018, #183827)',
          }}
        >
          <Typography variant="overline" sx={{ opacity: 0.72, fontWeight: 900 }}>
            Что внутри
          </Typography>
          <Typography variant="h3" sx={{ mt: 2 }}>
            Собеседование, результат и план роста в одном месте
          </Typography>
          <Stack spacing={1.5} sx={{ mt: 4 }}>
            {['Настройка роли и уровня', 'Диалог с AI-интервьюером', 'Оценка по критериям', 'История и рекомендации'].map((item) => (
              <Paper
                key={item}
                sx={{
                  p: 2,
                  borderRadius: 4,
                  bgcolor: 'rgba(255,255,255,0.1)',
                  color: 'inherit',
                  borderColor: 'rgba(255,255,255,0.14)',
                }}
              >
                {item}
              </Paper>
            ))}
          </Stack>
        </Paper>
      </Box>
    </Container>
  );
};

export default Register;
