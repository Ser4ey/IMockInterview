import React from 'react';
import { alpha } from '@mui/material/styles';
import { AppBar, Avatar, Box, Button, IconButton, Menu, MenuItem, Toolbar, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import AccountCircle from '@mui/icons-material/AccountCircle';
import { useAuth } from '../context/AuthContext';

const Header: React.FC = () => {
  const { isAuthenticated, logout, user } = useAuth();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleClose();
    logout();
    navigate('/login');
  };

  const handleProfile = () => {
    handleClose();
    navigate('/profile');
  };

  const handleAdmin = () => {
    handleClose();
    navigate('/admin/interview-types');
  };

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        top: 16,
        width: 'calc(100% - 32px)',
        maxWidth: 1500,
        mx: 'auto',
        mt: 2,
        border: '1px solid rgba(255,255,255,0.72)',
        borderRadius: 999,
        color: 'text.primary',
        bgcolor: alpha('#FFFFFF', 0.72),
        backdropFilter: 'blur(18px)',
        boxShadow: '0 18px 55px rgba(15, 23, 42, 0.08)',
      }}
    >
      <Toolbar sx={{ minHeight: { xs: 60, md: 66 }, gap: 2 }}>
        <Box
          onClick={() => navigate(isAuthenticated ? '/dashboard' : '/')}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1.2,
            flexGrow: 1,
            cursor: 'pointer',
            minWidth: 0,
          }}
        >
          <Avatar
            variant="rounded"
            sx={{
              width: 38,
              height: 38,
              borderRadius: 3,
              bgcolor: 'primary.main',
              fontWeight: 900,
            }}
          >
            I
          </Avatar>
          <Box>
            <Typography variant="h6" component="div" sx={{ lineHeight: 1, fontWeight: 900, letterSpacing: '-0.04em' }}>
              IMock
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' } }}>
              AI-тренажер собеседований
            </Typography>
          </Box>
        </Box>

        {isAuthenticated ? (
          <Box display="flex" alignItems="center" gap={1}>
            <Button variant="outlined" onClick={() => navigate('/dashboard')} sx={{ display: { xs: 'none', sm: 'inline-flex' } }}>
              Панель
            </Button>
            <IconButton
              size="large"
              aria-label="Аккаунт пользователя"
              aria-controls="menu-appbar"
              aria-haspopup="true"
              onClick={handleMenu}
              sx={{ color: 'primary.main' }}
            >
              <AccountCircle />
            </IconButton>
            <Menu
              id="menu-appbar"
              anchorEl={anchorEl}
              anchorOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              keepMounted
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              open={Boolean(anchorEl)}
              onClose={handleClose}
            >
              <MenuItem disabled>{user?.email}</MenuItem>
              <MenuItem onClick={handleProfile}>Профиль</MenuItem>
              {(user?.is_superuser || user?.role === 'admin') && <MenuItem onClick={handleAdmin}>Администрирование</MenuItem>}
              <MenuItem onClick={handleLogout}>Выйти</MenuItem>
            </Menu>
          </Box>
        ) : (
          <Box display="flex" gap={1}>
            <Button variant="outlined" onClick={() => navigate('/login')}>Войти</Button>
            <Button variant="contained" onClick={() => navigate('/register')}>Регистрация</Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Header;
