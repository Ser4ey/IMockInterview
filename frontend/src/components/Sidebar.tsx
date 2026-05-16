import React from 'react';
import {
  Box,
  Divider,
  LinearProgress,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PersonIcon from '@mui/icons-material/Person';
import TipsAndUpdatesIcon from '@mui/icons-material/TipsAndUpdates';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const sidebarWidth = 260;

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const menuItems = [
    { text: 'Панель подготовки', icon: <DashboardIcon />, path: '/dashboard' },
    { text: 'Профиль', icon: <PersonIcon />, path: '/profile' },
  ];

  return (
    <Box
      sx={{
        display: { xs: 'none', md: 'flex' },
        flexDirection: 'column',
        width: sidebarWidth,
        flexShrink: 0,
        alignSelf: 'flex-start',
        position: 'sticky',
        top: 100,
        mt: 3,
        p: 1.2,
        border: '1px solid rgba(21, 57, 38, 0.12)',
        borderRadius: 5,
        bgcolor: 'rgba(255,255,255,0.52)',
        backdropFilter: 'blur(18px)',
        boxShadow: '0 20px 60px rgba(15, 23, 42, 0.06)',
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="overline" color="text.secondary" fontWeight={900}>
          Рабочее место
        </Typography>
        <Typography variant="h6" sx={{ mt: 0.5 }}>
          Подготовка
        </Typography>
      </Box>
      <Box sx={{ overflow: 'auto', flexGrow: 1 }}>
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                selected={location.pathname === item.path}
                onClick={() => navigate(item.path)}
                sx={{
                  mb: 0.5,
                  borderRadius: 3,
                  '&.Mui-selected': {
                    bgcolor: 'rgba(24, 56, 39, 0.1)',
                    color: 'primary.main',
                    '& .MuiListItemIcon-root': { color: 'primary.main' },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 38 }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>
      <Box
        sx={{
          m: 1,
          p: 2,
          borderRadius: 4,
          bgcolor: 'primary.main',
          color: 'primary.contrastText',
        }}
      >
        <TipsAndUpdatesIcon sx={{ mb: 1 }} />
        <Typography variant="subtitle2" fontWeight={900}>
          Фокус недели
        </Typography>
        <Typography variant="caption" sx={{ opacity: 0.8 }}>
          Структурируйте ответы по схеме: контекст, решение, компромиссы.
        </Typography>
      </Box>
      <Divider sx={{ my: 1 }} />
      {user && (
        <Box p={2}>
          <Typography variant="subtitle2" gutterBottom>
            Тариф: {(user.tariff || 'free').toUpperCase()}
          </Typography>
          <Typography variant="caption" display="block" gutterBottom>
            Запросы: {user.requests_count || 0} / 20
          </Typography>
          <LinearProgress
            variant="determinate"
            value={Math.min((user.requests_count || 0) * (100 / 20), 100)}
            color={(user.requests_count || 0) >= 20 ? 'error' : 'primary'}
          />
        </Box>
      )}
    </Box>
  );
};

export default Sidebar;
