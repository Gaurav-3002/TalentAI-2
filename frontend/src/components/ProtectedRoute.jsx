import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Box, CircularProgress, Typography, Button } from '@mui/material';

const ProtectedRoute = ({ children, requiredRoles = [], allowGuest = false, redirectTo = '/login' }) => {
  const { isAuthenticated, loading, hasRole, isGuestUser } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '60vh',
          flexDirection: 'column',
          gap: 2
        }}
      >
        <CircularProgress size={60} />
        <Typography variant="h6" color="text.secondary">
          Verifying authentication...
        </Typography>
      </Box>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login page with return url
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  // If it's a guest user and guest access is not allowed for this route
  if (isGuestUser() && !allowGuest) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '60vh',
          flexDirection: 'column',
          gap: 2
        }}
      >
        <Typography variant="h4" color="warning.main" gutterBottom>
          Guest Access Limited
        </Typography>
        <Typography variant="body1" color="text.secondary" textAlign="center">
          This feature requires a full account. Please log in or create an account to access this page.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <Button variant="contained" onClick={() => window.location.href = '/login'}>
            Login
          </Button>
          <Button variant="outlined" onClick={() => window.location.href = '/register'}>
            Create Account
          </Button>
        </Box>
      </Box>
    );
  }

  // Check role permissions if required roles are specified (skip for guest users)
  if (requiredRoles.length > 0 && !isGuestUser() && !hasRole(requiredRoles)) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '60vh',
          flexDirection: 'column',
          gap: 2
        }}
      >
        <Typography variant="h4" color="error" gutterBottom>
          Access Denied
        </Typography>
        <Typography variant="body1" color="text.secondary" textAlign="center">
          You don't have permission to access this page.
          <br />
          Required roles: {requiredRoles.join(', ')}
        </Typography>
      </Box>
    );
  }

  return children;
};

export default ProtectedRoute;