import React from 'react';
import { Alert, Box, Button, Container, Typography } from '@mui/material';

type ErrorBoundaryState = {
  hasError: boolean;
};

class ErrorBoundary extends React.Component<React.PropsWithChildren, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    console.error('Ошибка интерфейса', error);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <Container maxWidth="sm" sx={{ mt: 8 }}>
        <Box display="flex" flexDirection="column" gap={2}>
          <Typography variant="h4">Что-то пошло не так</Typography>
          <Alert severity="error">
            Интерфейс столкнулся с ошибкой, но приложение не было закрыто. Обновите страницу и попробуйте еще раз.
          </Alert>
          <Button variant="contained" onClick={this.handleReload}>
            Обновить страницу
          </Button>
        </Box>
      </Container>
    );
  }
}

export default ErrorBoundary;
