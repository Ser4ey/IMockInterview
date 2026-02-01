import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Paper, Typography, Box, Button, CircularProgress } from '@mui/material';
import { ArrowBack, CheckCircle, Warning } from '@mui/icons-material';
import { getChat } from '../api/chats';
import { Chat, ChatStatus } from '../types/chat';

const InterviewResult: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [chat, setChat] = useState<Chat | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getChat(Number(id))
      .then(data => {
        setChat(data);
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Box display="flex" justifyContent="center" p={4}><CircularProgress /></Box>;
  if (!chat) return <Typography>Chat not found</Typography>;

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Button startIcon={<ArrowBack />} onClick={() => navigate('/dashboard')} sx={{ mb: 2 }}>
        Dashboard
      </Button>

      <Paper sx={{ p: 4 }}>
        <Box display="flex" alignItems="center" gap={2} mb={3}>
            {chat.status === ChatStatus.COMPLETED ? (
                <CheckCircle color="success" sx={{ fontSize: 40 }} />
            ) : (
                <Warning color="warning" sx={{ fontSize: 40 }} />
            )}
            <Box>
                <Typography variant="h4">Interview Result</Typography>
                <Typography variant="subtitle1" color="text.secondary">
                    {chat.position} ({chat.level})
                </Typography>
            </Box>
        </Box>

        <Box mb={4}>
            <Typography variant="h6" gutterBottom>AI Feedback Analysis</Typography>
            {chat.feedback ? (
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                     <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                        {chat.feedback}
                     </Typography>
                </Paper>
            ) : (
                <Box display="flex" alignItems="center" gap={1} color="text.secondary">
                    <Typography>
                        {chat.status === ChatStatus.COMPLETED 
                            ? "Analysis completed but no feedback content found." 
                            : "Interview is not yet finished. Complete the interview to see feedback."}
                    </Typography>
                </Box>
            )}
        </Box>
        
        <Box display="flex" justifyContent="center">
            <Button variant="contained" onClick={() => navigate('/dashboard')}>
                Return to Dashboard
            </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default InterviewResult;
