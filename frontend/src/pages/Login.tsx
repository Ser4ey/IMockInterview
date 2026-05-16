import React, { useState } from 'react';
import { Alert, Box, Button, Container, Paper, Stack, TextField, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import { getApiErrorMessage } from '../api/errors';
import { useAuth } from '../context/AuthContext';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);

    try {
      const response = await client.post('/auth/login/access-token', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      await login(response.data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Не удалось войти. Проверьте email и пароль.'));
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 4, md: 8 } }}>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: '0.92fr 1.08fr' },
          gap: 3,
          alignItems: 'stretch',
        }}
      >
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
            Добро пожаловать обратно
          </Typography>
          <Typography variant="h3" component="h1" sx={{ mt: 2 }}>
            Продолжим подготовку с того места, где остановились
          </Typography>
          <Typography sx={{ mt: 2, color: 'rgba(239,246,239,0.76)', lineHeight: 1.75 }}>
            Войдите в IMock, чтобы открыть историю интервью, результаты и рекомендации
            по дальнейшей подготовке.
          </Typography>
        </Paper>

        <Paper sx={{ p: { xs: 3, md: 5 }, borderRadius: 7, bgcolor: 'rgba(255,255,255,0.72)' }}>
          <Typography variant="h4" component="h2">
            Вход в аккаунт
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 1, mb: 3 }}>
            Используйте email и пароль, указанные при регистрации.
          </Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <form onSubmit={handleSubmit}>
            <Stack spacing={2}>
              <TextField
                label="Email"
                fullWidth
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
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
                Войти
              </Button>
              <Button variant="text" onClick={() => navigate('/register')}>
                Нет аккаунта? Зарегистрироваться
              </Button>
            </Stack>
          </form>
        </Paper>
      </Box>
    </Container>
  );
};

export default Login;
