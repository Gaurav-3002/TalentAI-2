import React, { useEffect, useState } from 'react';
import { Container, Card, CardContent, Typography, Chip, Box, CircularProgress, Alert, Button, Grid, Divider } from '@mui/material';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const Section = ({ title, children }) => (
  <Card variant="outlined" sx={{ mb: 3 }}>
    <CardContent>
      <Typography variant="h6" gutterBottom>{title}</Typography>
      {children}
    </CardContent>
  </Card>
);

const Profile = () => {
  const { user, isGuestUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await api.getProfile();
        setData(res);
      } catch (e) {
        setError(e.response?.data?.detail || 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    };
    if (!isGuestUser()) fetchProfile();
    else setLoading(false);
  }, [isGuestUser]);

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 6, textAlign: 'center' }}>
        <CircularProgress size={50} />
        <Typography sx={{ mt: 2 }}>Loading profile...</Typography>
      </Container>
    );
  }

  if (isGuestUser()) {
    return (
      <Container maxWidth="md" sx={{ py: 6, textAlign: 'center' }}>
        <Alert severity="warning">Guest users do not have profiles. Please login or register.</Alert>
        <Box sx={{ mt: 2 }}>
          <Button variant="contained" onClick={() => window.location.href = '/login'}>Login</Button>
          <Button variant="outlined" sx={{ ml: 2 }} onClick={() => window.location.href = '/register'}>Register</Button>
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ py: 6 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  const role = data?.role;
  const base = data?.user;

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" sx={{ mb: 1 }}>My Profile</Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>{base?.full_name} • {base?.email}</Typography>
      <Box sx={{ mb: 3 }}>
        <Chip label={role} color={role === 'admin' ? 'error' : role === 'recruiter' ? 'warning' : 'success'} />
      </Box>

      {role === 'candidate' && (
        <>
          <Section title="Resume & Skills">
            {data?.candidate_info ? (
              <>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Skills</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                  {data.candidate_info.skills?.map((s) => (
                    <Chip key={s} label={s} size="small" color="primary" variant="outlined" />
                  ))}
                </Box>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Resume Text</Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {data.candidate_info.resume_text?.slice(0, 1200) || 'No resume text available'}
                </Typography>
              </>
            ) : (
              <Alert severity="info">No resume uploaded yet. <Button size="small" onClick={() => window.location.href = '/upload-resume'}>Upload Resume</Button></Alert>
            )}
          </Section>

          <Section title="Applications">
            {data?.applications?.length ? (
              <Box>
                {data.applications.map((a) => (
                  <Card key={a.id} variant="outlined" sx={{ mb: 1 }}>
                    <CardContent sx={{ py: 1.5 }}>
                      <Typography variant="subtitle1">{a.job_title} • {a.company}</Typography>
                      <Typography variant="caption" color="text.secondary">Status: {a.status} • {new Date(a.applied_at).toLocaleString()}</Typography>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            ) : (
              <Alert severity="info">You haven't applied to any jobs yet.</Alert>
            )}
          </Section>
        </>
      )}

      {role === 'recruiter' && (
        <Section title="My Job Postings">
          {data?.recruiter_info?.jobs?.length ? (
            <Grid container spacing={2}>
              {data.recruiter_info.jobs.map((j) => (
                <Grid item xs={12} md={6} key={j.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1">{j.title}</Typography>
                      <Typography variant="body2" color="text.secondary">{j.company}</Typography>
                      <Typography variant="caption" color="text.secondary">{new Date(j.created_at).toLocaleDateString()}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Alert severity="info">No job postings yet. <Button size="small" onClick={() => window.location.href = '/post-job'}>Create Job</Button></Alert>
          )}
        </Section>
      )}

      {role === 'admin' && (
        <Section title="Platform Overview">
          <Typography variant="body2">Total Users: {data?.admin_info?.users_count}</Typography>
          <Typography variant="body2">Admins: {data?.admin_info?.counts_by_role?.admin}</Typography>
          <Typography variant="body2">Recruiters: {data?.admin_info?.counts_by_role?.recruiter}</Typography>
          <Typography variant="body2">Candidates: {data?.admin_info?.counts_by_role?.candidate}</Typography>
          <Divider sx={{ my: 2 }} />
          <Typography variant="body2">Jobs: {data?.admin_info?.jobs_count}</Typography>
          <Typography variant="body2">Candidates Profiles: {data?.admin_info?.candidates_count}</Typography>
        </Section>
      )}
    </Container>
  );
};

export default Profile;