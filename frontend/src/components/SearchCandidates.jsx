import React, { useState, useEffect } from 'react';
import {
  Container,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  Box,
  Grid,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Tooltip,
  Divider
} from '@mui/material';
import {
  Search as SearchIcon,
  VisibilityOff as BlindIcon,
  Visibility as VisibleIcon
} from '@mui/icons-material';
import api from '../services/api';
import CandidateList from './CandidateList';
import { useAuth } from '../contexts/AuthContext';

const SearchCandidates = () => {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);
  const [k, setK] = useState(10);
  const [blindScreening, setBlindScreening] = useState(false);

  const { isRecruiter, isGuestUser } = useAuth();

  useEffect(() => {
    if (isRecruiter() || isGuestUser()) {
      fetchJobs();
    }
  }, [isRecruiter, isGuestUser]);

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
      if (isGuestUser()) {
        // For guest users, show job details instead of candidate search
        const selectedJobData = jobs.find(job => job.id === selectedJob);
        if (selectedJobData) {
          // Set a special result to show job details
          setResults([{
            isJobDisplay: true,
            job: selectedJobData
          }]);
        }
      } else {
        const searchResults = await api.searchCandidates(selectedJob, k, blindScreening);
        setResults(searchResults || []);
        
        // Log this search action
        if (searchResults && searchResults.length > 0) {
          const selectedJobData = jobs.find(job => job.id === selectedJob);
          await api.createAccessLog(
            searchResults[0].candidate_id,
            'search',
            `Search performed for ${selectedJobData?.title} with blind_screening=${blindScreening}`
          );
        }
      }
    } catch (error) {
      console.error('Error searching candidates:', error);
      setError(error.response?.data?.detail || 'Search failed');
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  if (!isRecruiter() && !isGuestUser()) {
    return (
      <Container maxWidth="lg" sx={{ py: 8, textAlign: 'center' }}>
        <Typography variant="h4" color="error" gutterBottom>
          Access Denied
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Only recruiters and administrators can search candidates.
        </Typography>
      </Container>
    );
  }

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
      <Typography variant="h3" component="h1" gutterBottom sx={{ textAlign: 'center', mb: 2 }}>
        {isGuestUser() ? 'Browse Available Jobs' : 'Search Candidates'}
      </Typography>
      
      {isGuestUser() && (
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography variant="body1" color="info.main" sx={{ 
            backgroundColor: 'info.light', 
            p: 2, 
            borderRadius: 1,
            display: 'inline-block',
            maxWidth: 600
          }}>
            🎯 <strong>Guest Mode:</strong> You can browse available job postings and see job requirements. 
            For full access including candidate profiles, please create an account.
          </Typography>
        </Box>
      )}
      
      {/* Search Form */}
      {jobs.length === 0 ? (
        <Card elevation={3} sx={{ mb: 4 }}>
          <CardContent sx={{ p: 6, textAlign: 'center' }}>
            <Box
              component="img"
              src="https://customer-assets.emergentagent.com/job_bug-fix-central-1/artifacts/ax6ta69e_11072023_230143_Job-Portal-App-Development.png"
              alt="Job Portal Development"
              sx={{
                width: '100%',
                maxWidth: 300,
                height: 'auto',
                mb: 3,
                borderRadius: 2,
              }}
            />
            <Typography variant="h5" gutterBottom color="primary.main">
              No Job Postings Available
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 500, mx: 'auto' }}>
              There are no job postings created yet. Create a job posting first to search for matching candidates.
            </Typography>
            <Button 
              variant="contained" 
              size="large" 
              onClick={() => window.location.href = '/post-job'}
            >
              Create Job Posting
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card elevation={3} sx={{ mb: 4 }}>
          <CardContent sx={{ p: 3 }}>
            <Grid container spacing={3} alignItems="end">
              <Grid item xs={12} md={5}>
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
              
              <Grid item xs={12} md={2}>
                <TextField
                  fullWidth
                  label="Results"
                  type="number"
                  value={k}
                  onChange={(e) => setK(parseInt(e.target.value) || 10)}
                  inputProps={{ min: 1, max: 50 }}
                  variant="outlined"
                />
              </Grid>
              
              <Grid item xs={12} md={3}>
                <Tooltip title={blindScreening ? "Blind screening enabled - candidate names and emails will be masked" : "Blind screening disabled - full candidate information visible"}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={blindScreening}
                        onChange={(e) => setBlindScreening(e.target.checked)}
                        icon={<VisibleIcon />}
                        checkedIcon={<BlindIcon />}
                      />
                    }
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {blindScreening ? <BlindIcon /> : <VisibleIcon />}
                        Blind Screening
                      </Box>
                    }
                  />
                </Tooltip>
              </Grid>
              
              <Grid item xs={12} md={2}>
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

            {blindScreening && (
              <>
                <Divider sx={{ mt: 3, mb: 2 }} />
                <Alert severity="info" sx={{ backgroundColor: 'primary.light', color: 'primary.contrastText' }}>
                  <Typography variant="body2">
                    <strong>🔒 Blind Screening Active:</strong> Candidate personal information (names and emails) will be masked to reduce unconscious bias. 
                    Skills, experience, and match scores remain visible for fair evaluation.
                  </Typography>
                </Alert>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* Results */}
      <CandidateList
        candidates={[]}
        matchResults={results}
        loading={searching}
        error={null}
        title={results.length > 0 ? `Top ${results.length} Matching Candidates ${blindScreening ? '(Blind Mode)' : ''}` : "Search Results"}
        showScoreBreakdown={true}
        emptyMessage="Select a job posting and click search to find matching candidates."
        isSearchResults={true}
        blindMode={blindScreening}
      />
    </Container>
  );
};

export default SearchCandidates;