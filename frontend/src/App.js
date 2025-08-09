import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useNavigate } from "react-router-dom";
import {
  ThemeProvider,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  TextField,
  FormData as FormDataClass,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Upload as UploadIcon,
  Work as WorkIcon,
  Search as SearchIcon,
  Person as PersonIcon,
} from '@mui/icons-material';

// Import components and services
import theme from './utils/theme';
import api from './services/api';
import JobForm from './components/JobForm';
import CandidateList from './components/CandidateList';
import ValidationQuiz from './components/ValidationQuiz';

// Navigation Component with Material UI
const Navigation = () => {
  return (
    <AppBar position="static" elevation={2}>
      <Toolbar>
        <Typography
          variant="h6"
          component={Link}
          to="/"
          sx={{
            flexGrow: 1,
            textDecoration: 'none',
            color: 'inherit',
            fontWeight: 'bold'
          }}
        >
          🎯 Job Matcher
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            color="inherit"
            component={Link}
            to="/"
            startIcon={<DashboardIcon />}
            sx={{ textTransform: 'none' }}
          >
            Dashboard
          </Button>
          <Button
            color="inherit"
            component={Link}
            to="/upload-resume"
            startIcon={<UploadIcon />}
            sx={{ textTransform: 'none' }}
          >
            Upload Resume
          </Button>
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
        </Box>
      </Toolbar>
    </AppBar>
  );
};

// Dashboard Component with Material UI
const Dashboard = () => {
  const [stats, setStats] = useState({
    candidatesCount: 0,
    jobsCount: 0
  });
  const [recentCandidates, setRecentCandidates] = useState([]);
  const [recentJobs, setRecentJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const data = await api.getDashboardData();
      setRecentCandidates(data.candidates.slice(0, 5));
      setRecentJobs(data.jobs.slice(0, 5));
      setStats(data.stats);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
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

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom sx={{ textAlign: 'center', mb: 4 }}>
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

      {/* Recent Data */}
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
                emptyMessage="No candidates yet. Start by uploading some resumes!"
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
                  <WorkIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
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
    </Container>
  );
};

// Resume Upload Component with Material UI and Validation Test
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
  const navigate = useNavigate();

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
      navigate('/');
    }, 3000);
  };

  const handleSkipQuiz = () => {
    navigate('/');
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

// Job Posting Component with Material UI
const JobPosting = () => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleJobSubmit = async (jobData) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.createJob(jobData);
      setSuccess(response);
      setTimeout(() => {
        navigate('/');
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

// Search Component with Material UI
const SearchCandidates = () => {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);
  const [k, setK] = useState(10);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const jobsData = await api.getJobs();
      setJobs(jobsData);
    } catch (error) {
      console.error('Error fetching jobs:', error);
      setError('Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!selectedJob) {
      setError('Please select a job posting');
      return;
    }

    setSearching(true);
    setError(null);
    setResults([]);
    
    try {
      const searchResults = await api.searchCandidates(selectedJob, k);
      setResults(searchResults || []);
    } catch (error) {
      console.error('Error searching candidates:', error);
      setError(error.response?.data?.detail || 'Search failed');
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading jobs...
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom sx={{ textAlign: 'center', mb: 4 }}>
        Search Candidates
      </Typography>
      
      {/* Search Form */}
      <Card elevation={3} sx={{ mb: 4 }}>
        <CardContent sx={{ p: 3 }}>
          <Grid container spacing={3} alignItems="end">
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Select Job Posting</InputLabel>
                <Select
                  value={selectedJob}
                  onChange={(e) => setSelectedJob(e.target.value)}
                  label="Select Job Posting"
                >
                  <MenuItem value="">Choose a job posting...</MenuItem>
                  {jobs.map((job) => (
                    <MenuItem key={job.id} value={job.id}>
                      {job.title} - {job.company}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Number of Results"
                type="number"
                value={k}
                onChange={(e) => setK(parseInt(e.target.value) || 10)}
                inputProps={{ min: 1, max: 50 }}
                variant="outlined"
              />
            </Grid>
            
            <Grid item xs={12} md={3}>
              <Button
                variant="contained"
                size="large"
                fullWidth
                onClick={handleSearch}
                disabled={searching || !selectedJob}
                startIcon={searching ? <CircularProgress size={20} /> : <SearchIcon />}
                sx={{ py: 1.5 }}
              >
                {searching ? 'Searching...' : 'Search'}
              </Button>
            </Grid>

            {error && (
              <Grid item xs={12}>
                <Alert severity="error">
                  {error}
                </Alert>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>

      {/* Results */}
      <CandidateList
        candidates={[]}
        matchResults={results}
        loading={searching}
        error={null}
        title={results.length > 0 ? `Top ${results.length} Matching Candidates` : "Search Results"}
        showScoreBreakdown={true}
        emptyMessage="Select a job posting and click search to find matching candidates."
        isSearchResults={true}
      />
    </Container>
  );
};

// Main App Component
function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="App">
        <BrowserRouter>
          <Navigation />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload-resume" element={<ResumeUpload />} />
            <Route path="/post-job" element={<JobPosting />} />
            <Route path="/search" element={<SearchCandidates />} />
          </Routes>
        </BrowserRouter>
      </div>
    </ThemeProvider>
  );
}

export default App;