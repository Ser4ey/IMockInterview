import React from 'react';
import { Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Toolbar, Box, Divider, Typography, LinearProgress } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import ChatIcon from '@mui/icons-material/Chat';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const drawerWidth = 240;

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
    // { text: 'Interviews', icon: <ChatIcon />, path: '/chats' }, // 'Interviews' is redundant if Dashboard lists them, but okay.
  ];

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
      }}
    >
      <Toolbar />
      <Box sx={{ overflow: 'auto', flexGrow: 1 }}>
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton 
                selected={location.pathname === item.path}
                onClick={() => navigate(item.path)}
              >
                <ListItemIcon>
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>
      <Divider />
      {user && (
          <Box p={2}>
            <Typography variant="subtitle2" gutterBottom>
                Plan: {user.tariff.toUpperCase()}
            </Typography>
            <Typography variant="caption" display="block" gutterBottom>
                Requests: {user.requests_count} / 20
            </Typography>
            <LinearProgress 
                variant="determinate" 
                value={Math.min((user.requests_count || 0) * (100/20), 100)} 
                color={user.requests_count >= 20 ? "error" : "primary"}
            />
        </Box>
      )}
    </Drawer>
  );
};

export default Sidebar;
