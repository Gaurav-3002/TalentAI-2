import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Grid,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  useTheme,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Person as PersonIcon,
  Email as EmailIcon,
  Work as WorkIcon,
} from '@mui/icons-material';
import ScoreChart from './ScoreChart';

const CandidateCard = ({ candidate, matchResult, rank, showScoreBreakdown = false }) => {
  const theme = useTheme();

  // If it's a simple candidate (not a match result)
  if (!matchResult) {
    return (
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <PersonIcon sx={{ mr: 1, color: theme.palette.primary.main }} />
            <Typography variant="h6" component="div">
              {candidate.name}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <EmailIcon sx={{ mr: 1, color: theme.palette.text.secondary, fontSize: 'small' }} />
            <Typography variant="body2" color="text.secondary">
              {candidate.email}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <WorkIcon sx={{ mr: 1, color: theme.palette.text.secondary, fontSize: 'small' }} />
            <Typography variant="body2" color="text.secondary">
              {candidate.experience_years} years experience
            </Typography>
          </Box>

          {candidate.skills && candidate.skills.length > 0 && (
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Skills:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {candidate.skills.slice(0, 5).map((skill) => (
                  <Chip
                    key={skill}
                    label={skill}
                    size="small"
                    variant="outlined"
                    color="primary"
                  />
                ))}
                {candidate.skills.length > 5 && (
                  <Chip
                    label={`+${candidate.skills.length - 5} more`}
                    size="small"
                    variant="outlined"
                    color="default"
                  />
                )}
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>
    );
  }

  // Match result card with detailed scoring
  const getScoreColor = (score) => {
    if (score >= 0.8) return theme.palette.success.main;
    if (score >= 0.6) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        {/* Header with rank and overall score */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h5" component="div" sx={{ mb: 1 }}>
              {rank && `#${rank} `}{matchResult.candidate_name}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <EmailIcon sx={{ mr: 1, color: theme.palette.text.secondary, fontSize: 'small' }} />
              <Typography variant="body2" color="text.secondary">
                {matchResult.candidate_email}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <WorkIcon sx={{ mr: 1, color: theme.palette.text.secondary, fontSize: 'small' }} />
              <Typography variant="body2" color="text.secondary">
                {matchResult.candidate_experience_years} years experience
              </Typography>
            </Box>
          </Box>
          
          {/* Overall Score Badge */}
          <Box
            sx={{
              textAlign: 'center',
              p: 2,
              borderRadius: 2,
              backgroundColor: `${getScoreColor(matchResult.total_score)}20`,
              border: `2px solid ${getScoreColor(matchResult.total_score)}`,
              minWidth: 120,
            }}
          >
            <Typography
              variant="h4"
              sx={{ 
                fontWeight: 'bold', 
                color: getScoreColor(matchResult.total_score),
                lineHeight: 1,
              }}
            >
              {(matchResult.total_score * 100).toFixed(1)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Match Score
            </Typography>
          </Box>
        </Box>

        {/* Skills Section */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" sx={{ mb: 2 }}>
            Skills Analysis
          </Typography>
          <Grid container spacing={2}>
            {/* Matched Skills */}
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="success.main" sx={{ mb: 1 }}>
                ✓ Matched Skills ({matchResult.score_breakdown.matched_skills.length})
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                {matchResult.score_breakdown.matched_skills.map((skill) => (
                  <Chip
                    key={skill}
                    label={skill}
                    size="small"
                    color="success"
                    variant="filled"
                  />
                ))}
              </Box>
            </Grid>
            
            {/* Missing Skills */}
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="error.main" sx={{ mb: 1 }}>
                ✗ Missing Skills ({matchResult.score_breakdown.missing_skills.length})
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                {matchResult.score_breakdown.missing_skills.map((skill) => (
                  <Chip
                    key={skill}
                    label={skill}
                    size="small"
                    color="error"
                    variant="outlined"
                  />
                ))}
              </Box>
            </Grid>
          </Grid>
        </Box>

        {/* Quick Score Bars */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 2 }}>
            Score Components
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Semantic Match ({(matchResult.semantic_score * 100).toFixed(1)}%)
              </Typography>
              <LinearProgress
                variant="determinate"
                value={matchResult.semantic_score * 100}
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary">
                40% weight
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Skill Overlap ({(matchResult.skill_overlap_score * 100).toFixed(1)}%)
              </Typography>
              <LinearProgress
                variant="determinate"
                value={matchResult.skill_overlap_score * 100}
                color="success"
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary">
                40% weight
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Experience Match ({(matchResult.experience_match_score * 100).toFixed(1)}%)
              </Typography>
              <LinearProgress
                variant="determinate"
                value={matchResult.experience_match_score * 100}
                color="warning"
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary">
                20% weight
              </Typography>
            </Grid>
          </Grid>
        </Box>

        {/* Detailed Score Breakdown (Expandable) */}
        {showScoreBreakdown && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">
                Detailed Score Breakdown (Chart)
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <ScoreChart matchResult={matchResult} showTitle={false} />
            </AccordionDetails>
          </Accordion>
        )}
      </CardContent>
    </Card>
  );
};

export default CandidateCard;