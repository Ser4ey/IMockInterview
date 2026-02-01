import React from 'react';
import { Container, Typography, Button, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const Landing: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 8, textAlign: 'center' }}>
        <Typography variant="h2" component="h1" gutterBottom>
          Welcome to IMock
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom color="text.secondary">
          Master your interview skills with AI-powered mock interviews.
        </Typography>
        <Box sx={{ mt: 4 }}>
          <Button variant="contained" size="large" onClick={() => navigate('/register')} sx={{ mr: 2 }}>
            Get Started
          </Button>
          <Button variant="outlined" size="large" onClick={() => navigate('/login')}>
            Login
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default Landing;
