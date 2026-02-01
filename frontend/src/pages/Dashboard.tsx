import React, { useEffect, useState } from 'react';
import { 
  Container, Typography, Paper, Grid, Button, 
  Dialog, DialogTitle, DialogContent, DialogActions, 
  TextField, FormControl, InputLabel, Select, MenuItem,
  List, ListItem, ListItemText, ListItemButton, Chip, Box,
  CircularProgress
} from '@mui/material';
import { Add as AddIcon, Chat as ChatIcon } from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { getChats, createChat } from '../api/chats';
import { Chat, ChatStatus } from '../types/chat';
import { useNavigate } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [newChatData, setNewChatData] = useState({ position: '', level: 'Junior', topic: '' });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadChats();
  }, []);

  const loadChats = async () => {
    try {
      const data = await getChats();
      setChats(data);
    } catch (error) {
      console.error('Failed to load chats', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateChat = async () => {
    if (!newChatData.position) return;
    setCreating(true);
    try {
      const chat = await createChat(newChatData);
      setOpenDialog(false);
      navigate(`/chats/${chat.id}`);
    } catch (error) {
      console.error('Failed to create chat', error);
    } finally {
      setCreating(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Grid container justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Grid item>
          <Typography variant="h4" component="h1">
            Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Welcome back, {user?.full_name || user?.email}!
          </Typography>
        </Grid>
        <Grid item>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />} 
            onClick={() => setOpenDialog(true)}
          >
            New Interview
          </Button>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Statistics Card */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Your Statistics
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body1">
                <strong>Tariff:</strong> {user?.tariff}
              </Typography>
              <Typography variant="body1">
                <strong>Requests:</strong> {user?.requests_count}
              </Typography>
              <Typography variant="body1">
                <strong>Total Interviews:</strong> {chats.length}
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Recent Interviews List */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Recent Interviews
            </Typography>
            {loading ? (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            ) : chats.length === 0 ? (
              <Typography color="text.secondary" align="center" sx={{ py: 3 }}>
                No interviews yet. Click "New Interview" to start!
              </Typography>
            ) : (
              <List>
                {chats.map((chat) => (
                  <ListItemButton 
                    key={chat.id} 
                    onClick={() => navigate(`/chats/${chat.id}`)}
                    sx={{ mb: 1, border: '1px solid #eee', borderRadius: 1 }}
                  >
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="subtitle1" component="span" fontWeight="bold">
                            {chat.position}
                          </Typography>
                          <Chip 
                            label={chat.level} 
                            size="small" 
                            color={chat.level === 'Senior' ? 'error' : chat.level === 'Middle' ? 'warning' : 'success'} 
                            variant="outlined"
                          />
                        </Box>
                      }
                      secondary={`Created: ${new Date(chat.created_at).toLocaleDateString()}`}
                    />
                    <Chip 
                      label={chat.status} 
                      color={chat.status === ChatStatus.ACTIVE ? 'primary' : 'default'} 
                      size="small" 
                    />
                  </ListItemButton>
                ))}
              </List>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* New Interview Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Start New Mock Interview</DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              label="Position (e.g. Python Developer)"
              value={newChatData.position}
              onChange={(e) => setNewChatData({ ...newChatData, position: e.target.value })}
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Level</InputLabel>
              <Select
                value={newChatData.level}
                label="Level"
                onChange={(e) => setNewChatData({ ...newChatData, level: e.target.value as string })}
              >
                <MenuItem value="Junior">Junior</MenuItem>
                <MenuItem value="Middle">Middle</MenuItem>
                <MenuItem value="Senior">Senior</MenuItem>
                <MenuItem value="Lead">Lead</MenuItem>
              </Select>
            </FormControl>
            <TextField
              margin="normal"
              fullWidth
              label="Specific Topic (Optional)"
              helperText="E.g. AsyncIO, System Design, Algorithms"
              value={newChatData.topic}
              onChange={(e) => setNewChatData({ ...newChatData, topic: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateChat} 
            variant="contained" 
            disabled={!newChatData.position || creating}
          >
            {creating ? 'Creating...' : 'Start'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Dashboard;
