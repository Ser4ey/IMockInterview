import React from 'react';
import { Alert, Box, CircularProgress } from '@mui/material';
import { Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const AdminRoute: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!user?.is_superuser && user?.role !== 'admin') {
    return <Alert severity="error">Раздел доступен только администратору.</Alert>;
  }

  return <Outlet />;
};

export default AdminRoute;
