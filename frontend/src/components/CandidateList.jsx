import React from 'react';
import {
  Box,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  Paper,
} from '@mui/material';
import {
  People as PeopleIcon,
  SearchOff as SearchOffIcon,
} from '@mui/icons-material';
import CandidateCard from './CandidateCard';

const CandidateList = ({ 
  candidates = [], 
  matchResults = [], 
  loading = false, 
  error = null,
  title = "Candidates",
  showScoreBreakdown = false,
  emptyMessage = "No candidates found.",
  isSearchResults = false
}) => {

  // Loading state
  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
        <CircularProgress size={60} sx={{ mb: 2 }} />
        <Typography variant="body1" color="text.secondary">
          {isSearchResults ? 'Searching for candidates...' : 'Loading candidates...'}
        </Typography>
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  // Determine what to render
  const hasMatchResults = matchResults && matchResults.length > 0;
  const hasCandidates = candidates && candidates.length > 0;
  const hasData = hasMatchResults || hasCandidates;

  // Empty state
  if (!hasData) {
    return (
      <Paper elevation={1} sx={{ p: 6, textAlign: 'center', bgcolor: 'grey.50' }}>
        {isSearchResults ? (
          <>
            <Box
              component="img"
              src="https://customer-assets.emergentagent.com/job_bug-fix-central-1/artifacts/gdn5uo0b_choice-worker-concept-illustrated_52683-44076.avif"
              alt="No candidates found"
              sx={{
                width: '100%',
                maxWidth: 200,
                height: 'auto',
                mb: 2,
                borderRadius: 1,
              }}
            />
          </>
        ) : (
          <PeopleIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        )}
        <Typography variant="h6" color="text.secondary" gutterBottom>
          {emptyMessage}
        </Typography>
        {isSearchResults && (
          <Typography variant="body2" color="text.secondary">
            Try selecting a different job posting or adjusting your search criteria.
          </Typography>
        )}
      </Paper>
    );
  }

  return (
    <Box>
      {/* Title Section */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <PeopleIcon sx={{ mr: 2, color: 'primary.main' }} />
          {title}
        </Typography>
        
        {hasMatchResults && (
          <Typography variant="body1" color="text.secondary">
            Top {matchResults.length} matching candidates, ranked by compatibility score
          </Typography>
        )}
        
        {hasCandidates && !hasMatchResults && (
          <Typography variant="body1" color="text.secondary">
            {candidates.length} candidate{candidates.length !== 1 ? 's' : ''} found
          </Typography>
        )}
      </Box>

      {/* Candidates Grid */}
      <Grid container spacing={2}>
        <Grid item xs={12}>
          {/* Render match results if available */}
          {hasMatchResults && matchResults.map((matchResult, index) => (
            <CandidateCard
              key={matchResult.candidate_id}
              candidate={null}
              matchResult={matchResult}
              rank={index + 1}
              showScoreBreakdown={showScoreBreakdown}
            />
          ))}
          
          {/* Render regular candidates if no match results */}
          {!hasMatchResults && hasCandidates && candidates.map((candidate) => (
            <CandidateCard
              key={candidate.id}
              candidate={candidate}
              matchResult={null}
              showScoreBreakdown={false}
            />
          ))}
        </Grid>
      </Grid>
      
      {/* Results Summary */}
      {hasMatchResults && (
        <Paper elevation={1} sx={{ p: 2, mt: 3, bgcolor: 'info.light', color: 'info.contrastText' }}>
          <Typography variant="body2">
            💡 <strong>Tip:</strong> Scores are calculated using semantic similarity (40%), 
            skill overlap (40%), and experience match (20%). Higher scores indicate better matches.
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default CandidateList;