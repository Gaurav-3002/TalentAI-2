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
      } else {
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
        <Grid item xs={12} md={6}>
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
        
        <Grid item xs={12} md={6}>
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
                    Total Jobs
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
      {isGuestUser() ? (
        // Guest user gets a special welcome section with demo information
        <Card elevation={2} sx={{ mb: 4 }}>
          <CardContent sx={{ py: 6, textAlign: 'center' }}>
            <Box
              component="img"
              src="https://customer-assets.emergentagent.com/job_9ed72db7-5d32-4d00-a440-3eb81b39448c/artifacts/xn7kefv8_Top-10-Job-Portals-in-India-That-Makes-Them-Good-min.jpg"
              alt="Job Portal Demo"
              sx={{
                width: '100%',
                maxWidth: 400,
                height: 'auto',
                mb: 3,
                borderRadius: 2,
              }}
            />
            <Typography variant="h4" gutterBottom color="primary.main">
              Welcome to Job Matcher Demo! 🎯
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 600, mx: 'auto' }}>
              You're currently in <strong>Guest Mode</strong> with limited access. Explore our job matching platform 
              and browse available opportunities. For full access including resume upload and job posting, please create an account.
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Button 
                variant="contained" 
                size="large" 
                onClick={() => window.location.href = '/search'}
              >
                🔍 Browse Jobs
              </Button>
              <Button 
                variant="outlined" 
                size="large"
                onClick={() => window.location.href = '/register'}
              >
                📝 Create Full Account
              </Button>
              <Button 
                variant="text" 
                size="large"
                onClick={() => window.location.href = '/login'}
              >
                🔐 Login
              </Button>
            </Box>
          </CardContent>
        </Card>
      ) : isRecruiter() && (
        <>
          {/* Show main empty state if no candidates and no jobs */}
          {recentCandidates.length === 0 && recentJobs.length === 0 ? (
            <Card elevation={2} sx={{ mb: 4 }}>
              <CardContent sx={{ py: 8, textAlign: 'center' }}>
                <Box
                  component="img"
                  src="https://customer-assets.emergentagent.com/job_9ed72db7-5d32-4d00-a440-3eb81b39448c/artifacts/xn7kefv8_Top-10-Job-Portals-in-India-That-Makes-Them-Good-min.jpg"
                  alt="Job Portal"
                  sx={{
                    width: '100%',
                    maxWidth: 400,
                    height: 'auto',
                    mb: 3,
                    borderRadius: 2,
                  }}
                />
                <Typography variant="h4" gutterBottom color="primary.main">
                  Welcome to Your Job Matching Platform!
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 600, mx: 'auto' }}>
                  Get started by creating job postings and having candidates upload their resumes. 
                  Our AI-powered matching system will help you find the perfect candidates for your roles.
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
                  <Button 
                    variant="contained" 
                    size="large" 
                    onClick={() => window.location.href = '/post-job'}
                  >
                    Create Your First Job
                  </Button>
                  <Button 
                    variant="outlined" 
                    size="large"
                    onClick={() => window.location.href = '/upload-resume'}
                  >
                    Upload Resume
                  </Button>
                </Box>
              </CardContent>
            </Card>
          ) : (
            <Grid container spacing={3}>
              {/* Recent Candidates */}
              <Grid item xs={12} md={6}>
                <Card elevation={2}>
                  <CardContent>
                    <Typography variant="h5" gutterBottom>
                      Recent Candidates
                    </Typography>
                    <CandidateList
                      candidates={recentCandidates}
                      title=""
                      emptyMessage="No candidates yet. Start by having candidates upload resumes!"
                      blindMode={false}
                    />
                  </CardContent>
                </Card>
              </Grid>

              {/* Recent Jobs */}
              <Grid item xs={12} md={6}>
                <Card elevation={2}>
                  <CardContent>
                    <Typography variant="h5" gutterBottom>
                      Recent Job Postings
                    </Typography>
                    {recentJobs.length === 0 ? (
                      <Box sx={{ textAlign: 'center', py: 4 }}>
                        <Box
                          component="img"
                          src="https://customer-assets.emergentagent.com/job_bug-fix-central-1/artifacts/toa0hkqk_medium_Top_IT_jobs_that_will_be_in_demand_in_the_future_ae76ae783e_363a0b1311.png"
                          alt="IT Jobs in Demand"
                          sx={{
                            width: '100%',
                            maxWidth: 200,
                            height: 'auto',
                            mb: 2,
                            borderRadius: 1,
                          }}
                        />
                        <Typography variant="body1" color="text.secondary">
                          No job postings yet. Create your first job posting!
                        </Typography>
                      </Box>
                    ) : (
                      <Box sx={{ mt: 2 }}>
                        {recentJobs.map((job) => (
                          <Card key={job.id} variant="outlined" sx={{ mb: 2 }}>
                            <CardContent sx={{ py: 2 }}>
                              <Typography variant="h6" sx={{ mb: 1 }}>
                                {job.title}
                              </Typography>
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                {job.company} • {job.location}
                              </Typography>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {job.required_skills.slice(0, 3).map((skill) => (
                                  <Typography
                                    key={skill}
                                    variant="caption"
                                    sx={{
                                      backgroundColor: 'success.light',
                                      color: 'success.contrastText',
                                      px: 1,
                                      py: 0.5,
                                      borderRadius: 1,
                                      fontSize: '0.7rem',
                                    }}
                                  >
                                    {skill}
                                  </Typography>
                                ))}
                                {job.required_skills.length > 3 && (
                                  <Typography
                                    variant="caption"
                                    sx={{
                                      backgroundColor: 'grey.200',
                                      color: 'text.secondary',
                                      px: 1,
                                      py: 0.5,
                                      borderRadius: 1,
                                      fontSize: '0.7rem',
                                    }}
                                  >
                                    +{job.required_skills.length - 3} more
                                  </Typography>
                                )}
                              </Box>
                            </CardContent>
                          </Card>
                        ))}
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </>
      )}
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

              <Grid item xs={12}>
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
            </Routes>
          </BrowserRouter>
        </div>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;