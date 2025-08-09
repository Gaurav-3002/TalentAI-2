import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Menu,
  MenuItem,
  IconButton,
  Avatar,
  Divider,
  Chip
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Upload as UploadIcon,
  Work as WorkIcon,
  Search as SearchIcon,
  Person as PersonIcon,
  AdminPanelSettings as AdminIcon,
  Assessment as LogsIcon,
  ExitToApp as LogoutIcon,
  AccountCircle as AccountIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const Navigation = () => {
  const { isAuthenticated, user, logout, isAdmin, isRecruiter, isCandidate } = useAuth();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);

  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    handleProfileMenuClose();
    navigate('/login');
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin': return 'error';
      case 'recruiter': return 'warning';
      case 'candidate': return 'success';
      default: return 'default';
    }
  };

  return (
    <AppBar position="static" elevation={2}>
      <Toolbar>
        <Typography
          variant="h6"
          component={Link}
          to={isAuthenticated ? "/dashboard" : "/"}
          sx={{
            flexGrow: 1,
            textDecoration: 'none',
            color: 'inherit',
            fontWeight: 'bold'
          }}
        >
          🎯 Job Matcher
        </Typography>

        {isAuthenticated ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {/* Navigation Menu Items Based on Role */}
            <Button
              color="inherit"
              component={Link}
              to="/dashboard"
              startIcon={<DashboardIcon />}
              sx={{ textTransform: 'none' }}
            >
              Dashboard
            </Button>

            {/* Candidate can upload resume */}
            {isCandidate() && (
              <Button
                color="inherit"
                component={Link}
                to="/upload-resume"
                startIcon={<UploadIcon />}
                sx={{ textTransform: 'none' }}
              >
                Upload Resume
              </Button>
            )}

            {/* Recruiters and Admins can post jobs and search candidates */}
            {isRecruiter() && (
              <>
                <Button
                  color="inherit"
                  component={Link}
                  to="/post-job"
                  startIcon={<WorkIcon />}
                  sx={{ textTransform: 'none' }}
                >
                  Post Job
                </Button>
                <Button
                  color="inherit"
                  component={Link}
                  to="/search"
                  startIcon={<SearchIcon />}
                  sx={{ textTransform: 'none' }}
                >
                  Search
                </Button>
              </>
            )}

            {/* Admin-only features */}
            {isAdmin() && (
              <>
                <Button
                  color="inherit"
                  component={Link}
                  to="/admin/users"
                  startIcon={<AdminIcon />}
                  sx={{ textTransform: 'none' }}
                >
                  Users
                </Button>
                <Button
                  color="inherit"
                  component={Link}
                  to="/admin/logs"
                  startIcon={<LogsIcon />}
                  sx={{ textTransform: 'none' }}
                >
                  Access Logs
                </Button>
              </>
            )}

            {/* User Profile Menu */}
            <Box sx={{ display: 'flex', alignItems: 'center', ml: 2 }}>
              <Chip 
                label={user?.role || 'User'} 
                size="small" 
                color={getRoleColor(user?.role)}
                sx={{ mr: 1 }}
              />
              <IconButton
                size="large"
                edge="end"
                aria-label="account menu"
                aria-controls="profile-menu"
                aria-haspopup="true"
                onClick={handleProfileMenuOpen}
                color="inherit"
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
                  {user?.full_name?.charAt(0) || <PersonIcon />}
                </Avatar>
              </IconButton>
            </Box>

            <Menu
              id="profile-menu"
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleProfileMenuClose}
              onClick={handleProfileMenuClose}
              PaperProps={{
                elevation: 3,
                sx: {
                  mt: 1.5,
                  minWidth: 200,
                  '& .MuiMenuItem-root': {
                    gap: 2,
                  },
                },
              }}
              transformOrigin={{ horizontal: 'right', vertical: 'top' }}
              anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            >
              <Box sx={{ px: 2, py: 1 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                  {user?.full_name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {user?.email}
                </Typography>
              </Box>
              <Divider />
              <MenuItem onClick={() => navigate('/profile')}>
                <AccountIcon />
                Profile
              </MenuItem>
              <MenuItem onClick={handleLogout}>
                <LogoutIcon />
                Logout
              </MenuItem>
            </Menu>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button color="inherit" component={Link} to="/login">
              Login
            </Button>
            <Button color="inherit" component={Link} to="/register">
              Register
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Navigation;