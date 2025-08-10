import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import {
  ThemeProvider,
  CssBaseline,
  Container,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Typography,
  Box,
  TextField,
  Button,
} from '@mui/material';
import {
  Person as PersonIcon,
  Work as WorkIcon,
} from '@mui/icons-material';

// Import components and services
import theme from './utils/theme';
import api from './services/api';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navigation from './components/Navigation';
import Login from './components/Login';
import Register from './components/Register';
import JobForm from './components/JobForm';
import CandidateList from './components/CandidateList';
import ValidationQuiz from './components/ValidationQuiz';
import SearchCandidates from './components/SearchCandidates';
import UserManagement from './components/UserManagement';
import AccessLogs from './components/AccessLogs';
import Profile from './components/Profile';

// Dashboard Component with role-based data
const Dashboard = () => {
  const [stats, setStats] = useState({
    candidatesCount: 0,
    jobsCount: 0
  });
  const [recentCandidates, setRecentCandidates] = useState([]);
  const [recentJobs, setRecentJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { isRecruiter, isCandidate, user, isGuestUser } = useAuth();

  useEffect(() => {
    fetchDashboardData();
  }, [isRecruiter]);

  const fetchDashboardData = async () => {
    try {
      // For guest users, show public demo data or limited access
      if (isGuestUser()) {
        // Set some demo stats for guest users
        setStats({
          candidatesCount: 25,
          jobsCount: 12
        });
        setRecentCandidates([]);
        setRecentJobs([]);
        setError(null);
      } else if (isCandidate()) {
        // For candidates, only show jobs data and their own profile
        try {
          const jobsRes = await api.getJobs();
          setRecentJobs(jobsRes.slice(0, 5));
          setStats({
            candidatesCount: 0, // Don't show candidate count to candidates
            jobsCount: jobsRes.length
          });
          setRecentCandidates([]); // Candidates don't see other candidates
          setError(null);
        } catch (jobsError) {
          console.error('Error fetching jobs for candidate:', jobsError);
          // Even if jobs fail, don't show the error, just show empty state
          setStats({ candidatesCount: 0, jobsCount: 0 });
          setRecentJobs([]);
          setRecentCandidates([]);
          setError(null);
        }
      } else {
        // For recruiters and admins, show full dashboard data
        const data = await api.getDashboardData(false); // Don't use blind mode for dashboard
        setRecentCandidates(data.candidates.slice(0, 5));
        setRecentJobs(data.jobs.slice(0, 5));
        setStats(data.stats);
        setError(null);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading dashboard...
        </Typography>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom sx={{ textAlign: 'center', mb: 1 }}>
        Welcome back, {user?.full_name}!
      </Typography>
      <Typography variant="h6" color="text.secondary" gutterBottom sx={{ textAlign: 'center', mb: 4 }}>
        Job Matching Dashboard
      </Typography>
      
      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {!isCandidate() && (
          <Grid item xs={12} md={isCandidate() ? 12 : 6}>
            <Card elevation={3}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box
                    sx={{
                      backgroundColor: 'primary.main',
                      color: 'primary.contrastText',
                      p: 2,
                      borderRadius: 2,
                      mr: 3,
                    }}
                  >
                    <PersonIcon sx={{ fontSize: 32 }} />
                  </Box>
                  <Box>
                    <Typography variant="h6" color="text.secondary">
                      Total Candidates
                    </Typography>
                    <Typography variant="h3" color="primary.main" fontWeight="bold">
                      {stats.candidatesCount}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
        
        <Grid item xs={12} md={isCandidate() ? 12 : 6}>
          <Card elevation={3}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box
                  sx={{
                    backgroundColor: 'success.main',
                    color: 'success.contrastText',
                    p: 2,
                    borderRadius: 2,
                    mr: 3,
                  }}
                >
                  <WorkIcon sx={{ fontSize: 32 }} />
                </Box>
                <Box>
                  <Typography variant="h6" color="text.secondary">
                    {isCandidate() ? 'Available Jobs' : 'Total Jobs'}
                  </Typography>
                  <Typography variant="h3" color="success.main" fontWeight="bold">
                    {stats.jobsCount}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Data - Show different content based on user type */}
      <Grid container spacing={3}>
        {/* Candidates Section - Only for non-candidates */}
        {!isCandidate() && (
          <Grid item xs={12} md={6}>
            <Card elevation={3}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <PersonIcon sx={{ mr: 2, color: 'primary.main' }} />
                  Recent Candidates
                </Typography>
                
                {recentCandidates && recentCandidates.length > 0 ? (
                  <Box>
                    {recentCandidates.map((candidate) => (
                      <Box key={candidate.id} sx={{ py: 1, borderBottom: '1px solid', borderColor: 'grey.200' }}>
                        <Typography variant="body1" fontWeight="medium">
                          {candidate.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {candidate.skills?.slice(0, 2).join(', ')} 
                          {candidate.skills?.length > 2 && ` +${candidate.skills.length - 2} more`}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {candidate.experience_years} years experience
                        </Typography>
                      </Box>
                    ))}
                    <Box sx={{ textAlign: 'center', mt: 2 }}>
                      <Button variant="outlined" size="small" href="/search">
                        View All Candidates
                      </Button>
                    </Box>
                  </Box>
                ) : (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Box
                      component="img"
                      src="/empty-states/no-candidates.avif"
                      alt="No candidates yet"
                      sx={{
                        width: '100%',
                        maxWidth: 120,
                        height: 'auto',
                        mb: 2,
                        borderRadius: 1,
                        opacity: 0.7
                      }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      No candidates uploaded yet
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
        
        {/* Jobs Section - Available for all users */}
        <Grid item xs={12} md={isCandidate() ? 12 : 6}>
          <Card elevation={3}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <WorkIcon sx={{ mr: 2, color: 'success.main' }} />
                {isCandidate() ? 'Available Jobs' : 'Recent Job Postings'}
              </Typography>
              
              {recentJobs && recentJobs.length > 0 ? (
                <Box>
                  {recentJobs.map((job) => (
                    <Box key={job.id} sx={{ py: 1, borderBottom: '1px solid', borderColor: 'grey.200' }}>
                      <Typography variant="body1" fontWeight="medium">
                        {job.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {job.company} • {job.location}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {job.min_experience_years}+ years • {job.required_skills?.slice(0, 2).join(', ')}
                        {job.required_skills?.length > 2 && ` +${job.required_skills.length - 2} more`}
                      </Typography>
                    </Box>
                  ))}
                  <Box sx={{ textAlign: 'center', mt: 2 }}>
                    <Button variant="outlined" size="small" href="/search">
                      {isCandidate() ? 'Browse All Jobs' : 'View All Jobs'}
                    </Button>
                  </Box>
                </Box>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Box
                    component="img"
                    src="/empty-states/no-jobs.png"
                    alt="No jobs yet"
                    sx={{
                      width: '100%',
                      maxWidth: 120,
                      height: 'auto',
                      mb: 2,
                      borderRadius: 1,
                      opacity: 0.7
                    }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    No job postings available yet
                  </Typography>
                  {!isCandidate() && (
                    <Button 
                      variant="text" 
                      size="small" 
                      href="/post-job"
                      sx={{ mt: 1 }}
                    >
                      Post a Job
                    </Button>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

    </Container>
  );
};

// Resume Upload Component (updated for authentication)
const ResumeUpload = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    resumeText: '',
    skills: '',
    experienceYears: 0,
    education: ''
  });
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [showQuiz, setShowQuiz] = useState(false);
  const [candidateSkills, setCandidateSkills] = useState([]);

  const { user } = useAuth();

  // Pre-fill form with user data if available
  useEffect(() => {
    if (user) {
      setFormData(prev => ({
        ...prev,
        name: user.full_name || '',
        email: user.email || ''
      }));
    }
  }, [user]);

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const submitData = new FormData();
      submitData.append('name', formData.name);
      submitData.append('email', formData.email);
      submitData.append('resume_text', formData.resumeText);
      submitData.append('skills', formData.skills);
      submitData.append('experience_years', formData.experienceYears);
      submitData.append('education', formData.education);
      
      if (file) {
        submitData.append('file', file);
      }

      const response = await api.uploadResume(submitData);
      setSuccess(response);
      setCandidateSkills(response.extracted_skills || []);
    } catch (error) {
      console.error('Error uploading resume:', error);
      setError(error.response?.data?.detail || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleQuizComplete = (results) => {
    console.log('Quiz completed:', results);
    setTimeout(() => {
      window.location.href = '/dashboard';
    }, 3000);
  };

  const handleSkipQuiz = () => {
    window.location.href = '/dashboard';
  };

  // Show validation quiz after successful upload
  if (success && showQuiz) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <ValidationQuiz
          candidateSkills={candidateSkills}
          onComplete={handleQuizComplete}
          onSkip={handleSkipQuiz}
        />
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom sx={{ textAlign: 'center', mb: 4 }}>
        Upload Resume
      </Typography>
      
      <Card elevation={3}>
        <CardContent sx={{ p: 4 }}>
          <Box component="form" onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Full Name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  variant="outlined"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  variant="outlined"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Upload Resume File"
                  type="file"
                  onChange={handleFileChange}
                  InputLabelProps={{ shrink: true }}
                  inputProps={{ accept: '.pdf,.docx,.txt' }}
                  variant="outlined"
                />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Supported formats: PDF, DOCX, TXT
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Resume Text (if not uploading file)"
                  name="resumeText"
                  value={formData.resumeText}
                  onChange={handleInputChange}
                  multiline
                  rows={6}
                  placeholder="Paste your resume text here..."
                  variant="outlined"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Skills (comma-separated)"
                  name="skills"
                  value={formData.skills}
                  onChange={handleInputChange}
                  placeholder="JavaScript, Python, React, etc."
                  variant="outlined"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Years of Experience"
                  name="experienceYears"
                  type="number"
                  value={formData.experienceYears}
                  onChange={handleInputChange}
                  inputProps={{ min: 0, max: 50 }}
                  variant="outlined"
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Education"
                  name="education"
                  value={formData.education}
                  onChange={handleInputChange}
                  placeholder="Bachelor's in Computer Science"
                  variant="outlined"
                />
              </Grid>

              {error && (
                <Grid item xs={12}>
                  <Alert severity="error">
                    {error}
                  </Alert>
                </Grid>
              )}

              {success && (
                <Grid item xs={12}>
                  <Alert severity="success" sx={{ mb: 2 }}>
                    Resume uploaded successfully! Candidate ID: {success.candidate_id}
                    <br />
                    Extracted Skills: {success.extracted_skills?.join(', ')}
                    <br />
                    Experience: {success.experience_years} years
                  </Alert>
                  {!showQuiz && (
                    <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                      <Button
                        variant="contained"
                        onClick={() => setShowQuiz(true)}
                        disabled={!success.extracted_skills || success.extracted_skills.length === 0}
                      >
                        Take Validation Test
                      </Button>
                      <Button
                        variant="outlined"
                        onClick={handleSkipQuiz}
                      >
                        Skip and Continue
                      </Button>
                    </Box>
                  )}
                </Grid>
              )}

              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                  fullWidth
                  disabled={loading || (!file && !formData.resumeText)}
                  sx={{ py: 2, fontSize: '1.1rem' }}
                >
                  {loading ? (
                    <>
                      <CircularProgress size={20} sx={{ mr: 2 }} />
                      Processing...
                    </>
                  ) : (
                    'Upload Resume'
                  )}
                </Button>
              </Grid>
            </Grid>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
};

// Job Posting Component (updated for authentication)
const JobPosting = () => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

  const handleJobSubmit = async (jobData) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.createJob(jobData);
      setSuccess(response);
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 2000);
    } catch (error) {
      console.error('Error creating job posting:', error);
      setError(error.response?.data?.detail || 'Job posting creation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom sx={{ textAlign: 'center', mb: 4 }}>
        Post a Job
      </Typography>
      
      <JobForm
        onSubmit={handleJobSubmit}
        loading={loading}
        error={error}
        success={success}
      />
    </Container>
  );
};

// Candidate jobs list Apply handler addition in existing component rendering is not fully shown here
// but we ensure route to new Profile page below

// Main App Component with Authentication
function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <div className="App">
          <BrowserRouter>
            <Navigation />
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              
              {/* Protected Routes */}
              <Route 
                path="/" 
                element={
                  <Navigate to="/dashboard" replace />
                } 
              />
              
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute allowGuest={true}>
                    <Dashboard />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/upload-resume" 
                element={
                  <ProtectedRoute requiredRoles={['candidate']}>
                    <ResumeUpload />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/post-job" 
                element={
                  <ProtectedRoute requiredRoles={['admin', 'recruiter']}>
                    <JobPosting />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/search" 
                element={
                  <ProtectedRoute allowGuest={true}>
                    <SearchCandidates />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/admin/users" 
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <UserManagement />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/admin/logs" 
                element={
                  <ProtectedRoute requiredRoles={['admin', 'recruiter']}>
                    <AccessLogs />
                  </ProtectedRoute>
                } 
              />

              <Route 
                path="/profile" 
                element={
                  <ProtectedRoute allowGuest={false}>
                    <Profile />
                  </ProtectedRoute>
                } 
              />
            </Routes>
          </BrowserRouter>
        </div>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;