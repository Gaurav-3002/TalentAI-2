import React, { useState, useEffect } from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Box,
  Alert,
  CircularProgress,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Tooltip
} from '@mui/material';
import {
  Search as SearchIcon,
  Visibility as ViewIcon,
  Assessment as EvaluationIcon,
  ContactMail as ContactIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const AccessLogs = () => {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [reasonFilter, setReasonFilter] = useState('');

  const { isRecruiter } = useAuth();

  useEffect(() => {
    if (isRecruiter()) {
      fetchAccessLogs();
    }
  }, [isRecruiter]);

  useEffect(() => {
    // Apply filters
    let filtered = logs;

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(log =>
        log.candidate_name.toLowerCase().includes(term) ||
        log.candidate_email.toLowerCase().includes(term) ||
        log.user_email.toLowerCase().includes(term) ||
        (log.access_details && log.access_details.toLowerCase().includes(term))
      );
    }

    if (roleFilter) {
      filtered = filtered.filter(log => log.user_role === roleFilter);
    }

    if (reasonFilter) {
      filtered = filtered.filter(log => log.access_reason === reasonFilter);
    }

    setFilteredLogs(filtered);
  }, [logs, searchTerm, roleFilter, reasonFilter]);

  const fetchAccessLogs = async () => {
    try {
      const logsData = await api.getAccessLogs(500); // Get more logs for admin view
      setLogs(logsData);
    } catch (error) {
      console.error('Error fetching access logs:', error);
      setError('Failed to fetch access logs');
    } finally {
      setLoading(false);
    }
  };

  const getReasonIcon = (reason) => {
    switch (reason) {
      case 'search': return <SearchIcon />;
      case 'view_profile': return <ViewIcon />;
      case 'evaluation': return <EvaluationIcon />;
      case 'contact': return <ContactIcon />;
      default: return <PersonIcon />;
    }
  };

  const getReasonColor = (reason) => {
    switch (reason) {
      case 'search': return 'primary';
      case 'view_profile': return 'info';
      case 'evaluation': return 'warning';
      case 'contact': return 'success';
      default: return 'default';
    }
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin': return 'error';
      case 'recruiter': return 'warning';
      case 'candidate': return 'success';
      default: return 'default';
    }
  };

  if (!isRecruiter()) {
    return (
      <Container maxWidth="lg" sx={{ py: 8, textAlign: 'center' }}>
        <Typography variant="h4" color="error" gutterBottom>
          Access Denied
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Only recruiters and administrators can view access logs.
        </Typography>
      </Container>
    );
  }

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading access logs...
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom sx={{ textAlign: 'center', mb: 4 }}>
        Access Logs
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Card elevation={3} sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Filters
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Search candidates, users, or details"
                variant="outlined"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>User Role</InputLabel>
                <Select
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                  label="User Role"
                >
                  <MenuItem value="">All Roles</MenuItem>
                  <MenuItem value="admin">Admin</MenuItem>
                  <MenuItem value="recruiter">Recruiter</MenuItem>
                  <MenuItem value="candidate">Candidate</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Access Reason</InputLabel>
                <Select
                  value={reasonFilter}
                  onChange={(e) => setReasonFilter(e.target.value)}
                  label="Access Reason"
                >
                  <MenuItem value="">All Reasons</MenuItem>
                  <MenuItem value="search">Search</MenuItem>
                  <MenuItem value="view_profile">View Profile</MenuItem>
                  <MenuItem value="evaluation">Evaluation</MenuItem>
                  <MenuItem value="contact">Contact</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card elevation={3}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5">
              Access History ({filteredLogs.length} records)
            </Typography>
          </Box>

          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Candidate</TableCell>
                  <TableCell>Access Reason</TableCell>
                  <TableCell>Details</TableCell>
                  <TableCell>IP Address</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredLogs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 8 }}>
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        <Box
                          component="img"
                          src="/empty-states/no-logs.png"
                          alt="No logs"
                          sx={{
                            width: '100%',
                            maxWidth: 200,
                            height: 'auto',
                            mb: 2,
                            borderRadius: 1,
                          }}
                        />
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                          No Access Logs Found
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {logs.length === 0 ? 'No access activities have been recorded yet.' : 'No logs match your current filters.'}
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredLogs.map((log) => (
                    <TableRow key={log.id} hover>
                      <TableCell>
                        <Box>
                          <Typography variant="body2">
                            {new Date(log.timestamp).toLocaleDateString()}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2">{log.user_email}</Typography>
                          <Chip
                            label={log.user_role}
                            size="small"
                            color={getRoleColor(log.user_role)}
                          />
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2">{log.candidate_name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {log.candidate_email}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={log.access_reason.replace('_', ' ')}
                          size="small"
                          color={getReasonColor(log.access_reason)}
                          icon={getReasonIcon(log.access_reason)}
                        />
                      </TableCell>
                      <TableCell>
                        <Tooltip title={log.access_details || 'No details'}>
                          <Typography
                            variant="body2"
                            sx={{
                              maxWidth: 200,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {log.access_details || 'No details'}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="text.secondary">
                          {log.ip_address || 'N/A'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Container>
  );
};

export default AccessLogs;