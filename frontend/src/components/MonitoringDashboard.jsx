import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  CircularProgress,
  Tabs,
  Tab
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  Error,
  Info,
  TrendingUp,
  Speed,
  Assessment
} from '@mui/icons-material';

const MonitoringDashboard = () => {
  const [tabValue, setTabValue] = useState(0);
  const [healthData, setHealthData] = useState(null);
  const [sloData, setSloData] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchMonitoringData();
    const interval = setInterval(fetchMonitoringData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchMonitoringData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Fetch health data (public)
      const healthResponse = await fetch(`${API_BASE_URL}/api/monitoring/health`);
      const health = await healthResponse.json();
      setHealthData(health);

      // Fetch dashboard data (authenticated)
      const dashboardResponse = await fetch(`${API_BASE_URL}/api/monitoring/dashboard`, {
        headers
      });
      if (dashboardResponse.ok) {
        const dashboard = await dashboardResponse.json();
        setDashboardData(dashboard);
      }

      // Fetch SLO data (admin only)
      const sloResponse = await fetch(`${API_BASE_URL}/api/monitoring/slo`, {
        headers
      });
      if (sloResponse.ok) {
        const slo = await sloResponse.json();
        setSloData(slo);
      }

      setError(null);
    } catch (err) {
      setError(`Failed to fetch monitoring data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'up':
      case 'operational':
        return 'success';
      case 'degraded':
      case 'warning':
      case 'at_risk':
        return 'warning';
      case 'unhealthy':
      case 'down':
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'up':
      case 'operational':
        return <CheckCircle color="success" />;
      case 'degraded':
      case 'warning':
      case 'at_risk':
        return <Warning color="warning" />;
      case 'unhealthy':
      case 'down':
      case 'critical':
        return <Error color="error" />;
      default:
        return <Info color="default" />;
    }
  };

  const HealthOverview = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              System Health Status
            </Typography>
            {healthData?.components && Object.entries(healthData.components).map(([component, data]) => (
              <Box key={component} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                {getStatusIcon(data.status)}
                <Typography variant="body1" sx={{ ml: 1, textTransform: 'capitalize' }}>
                  {component.replace('_', ' ')}: 
                </Typography>
                <Chip 
                  label={data.status} 
                  color={getStatusColor(data.status)}
                  size="small"
                  sx={{ ml: 1 }}
                />
              </Box>
            ))}
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              System Metrics
            </Typography>
            {healthData?.metrics && (
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>Total Users</TableCell>
                      <TableCell align="right">{healthData.metrics.total_users}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Total Candidates</TableCell>
                      <TableCell align="right">{healthData.metrics.total_candidates}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Total Jobs</TableCell>
                      <TableCell align="right">{healthData.metrics.total_jobs}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Total Interactions</TableCell>
                      <TableCell align="right">{healthData.metrics.total_interactions}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            {dashboardData?.summary?.recent_activity && (
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>Searches (Last Hour)</TableCell>
                      <TableCell align="right">
                        {dashboardData.summary.recent_activity.searches_last_hour}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Resumes (Today)</TableCell>
                      <TableCell align="right">
                        {dashboardData.summary.recent_activity.resumes_processed_today}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Interactions (Today)</TableCell>
                      <TableCell align="right">
                        {dashboardData.summary.recent_activity.interactions_today}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const SLOOverview = () => (
    <Grid container spacing={3}>
      {sloData?.slos && Object.entries(sloData.slos).map(([sloName, sloInfo]) => (
        <Grid item xs={12} md={4} key={sloName}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ textTransform: 'capitalize' }}>
                {sloName.replace(/_/g, ' ')}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                {getStatusIcon(sloInfo.status)}
                <Chip 
                  label={sloInfo.status} 
                  color={getStatusColor(sloInfo.status)}
                  size="small"
                  sx={{ ml: 1 }}
                />
              </Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Target: {sloInfo.target}
              </Typography>
              <Typography variant="body1" sx={{ mb: 1 }}>
                Current: {sloInfo.current_performance}
              </Typography>
              {sloInfo.status === 'healthy' && (
                <LinearProgress variant="determinate" value={95} color="success" />
              )}
              {sloInfo.status === 'at_risk' && (
                <LinearProgress variant="determinate" value={70} color="warning" />
              )}
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

  const QuickActions = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              External Monitoring Links
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <a href="http://localhost:9090" target="_blank" rel="noopener noreferrer">
                <Chip 
                  icon={<Assessment />}
                  label="Prometheus" 
                  clickable 
                  color="primary"
                />
              </a>
              <a href="http://localhost:3001" target="_blank" rel="noopener noreferrer">
                <Chip 
                  icon={<TrendingUp />}
                  label="Grafana Dashboard" 
                  clickable 
                  color="secondary"
                />
              </a>
              <a href="/metrics" target="_blank" rel="noopener noreferrer">
                <Chip 
                  icon={<Speed />}
                  label="Raw Metrics" 
                  clickable 
                  color="default"
                />
              </a>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              System Information
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Version: {healthData?.version || 'N/A'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Last Updated: {new Date().toLocaleTimeString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Overall Status: {sloData?.overall_status || dashboardData?.summary?.system_status || 'Unknown'}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  if (loading && !healthData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Loading monitoring data...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        TalentAI Monitoring Dashboard
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="Health Overview" />
          <Tab label="SLO Status" disabled={!sloData} />
          <Tab label="Quick Actions" />
        </Tabs>
      </Box>

      {tabValue === 0 && <HealthOverview />}
      {tabValue === 1 && <SLOOverview />}
      {tabValue === 2 && <QuickActions />}
    </Box>
  );
};

export default MonitoringDashboard;