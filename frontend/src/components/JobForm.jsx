import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
} from '@mui/material';
import {
  Work as WorkIcon,
  Send as SendIcon,
  Add as AddIcon,
} from '@mui/icons-material';

const JobForm = ({ onSubmit, loading = false, error = null, success = null }) => {
  const [formData, setFormData] = useState({
    title: '',
    company: '',
    requiredSkills: [],
    location: '',
    salary: '',
    description: '',
    minExperienceYears: 0
  });

  const [skillInput, setSkillInput] = useState('');

  // Predefined skill suggestions
  const skillSuggestions = [
    'JavaScript', 'Python', 'React', 'Node.js', 'Java', 'TypeScript',
    'Angular', 'Vue.js', 'Django', 'Flask', 'Spring Boot', 'MongoDB',
    'MySQL', 'PostgreSQL', 'AWS', 'Docker', 'Kubernetes', 'Git',
    'Machine Learning', 'TensorFlow', 'PyTorch', 'Data Analysis',
    'HTML', 'CSS', 'Sass', 'Redux', 'Express.js', 'GraphQL'
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAddSkill = () => {
    if (skillInput.trim() && !formData.requiredSkills.includes(skillInput.trim())) {
      setFormData(prev => ({
        ...prev,
        requiredSkills: [...prev.requiredSkills, skillInput.trim()]
      }));
      setSkillInput('');
    }
  };

  const handleRemoveSkill = (skillToRemove) => {
    setFormData(prev => ({
      ...prev,
      requiredSkills: prev.requiredSkills.filter(skill => skill !== skillToRemove)
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate required fields
    if (!formData.title.trim() || !formData.company.trim() || !formData.description.trim()) {
      return;
    }
    
    if (formData.requiredSkills.length === 0) {
      return;
    }

    // Format data for API
    const jobData = {
      title: formData.title.trim(),
      company: formData.company.trim(),
      required_skills: formData.requiredSkills,
      location: formData.location.trim(),
      salary: formData.salary.trim(),
      description: formData.description.trim(),
      min_experience_years: parseInt(formData.minExperienceYears) || 0
    };

    onSubmit(jobData);
  };

  const handleSkillSuggestionClick = (skill) => {
    if (!formData.requiredSkills.includes(skill)) {
      setFormData(prev => ({
        ...prev,
        requiredSkills: [...prev.requiredSkills, skill]
      }));
    }
  };

  return (
    <Card sx={{ maxWidth: 800, mx: 'auto' }}>
      <CardContent sx={{ p: 4 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <WorkIcon sx={{ fontSize: 32, color: 'primary.main', mr: 2 }} />
          <Typography variant="h4" component="h1">
            Post a Job
          </Typography>
        </Box>

        {/* Form */}
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            {/* Job Title and Company */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Job Title"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                required
                placeholder="e.g., Software Engineer"
                variant="outlined"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Company"
                name="company"
                value={formData.company}
                onChange={handleInputChange}
                required
                placeholder="e.g., Tech Corp"
                variant="outlined"
              />
            </Grid>

            {/* Location and Salary */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Location"
                name="location"
                value={formData.location}
                onChange={handleInputChange}
                placeholder="e.g., San Francisco, CA or Remote"
                variant="outlined"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Salary Range"
                name="salary"
                value={formData.salary}
                onChange={handleInputChange}
                placeholder="e.g., $80,000 - $120,000"
                variant="outlined"
              />
            </Grid>

            {/* Experience Level */}
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Minimum Experience (Years)</InputLabel>
                <Select
                  name="minExperienceYears"
                  value={formData.minExperienceYears}
                  onChange={handleInputChange}
                  label="Minimum Experience (Years)"
                >
                  <MenuItem value={0}>Entry Level (0 years)</MenuItem>
                  <MenuItem value={1}>1 year</MenuItem>
                  <MenuItem value={2}>2 years</MenuItem>
                  <MenuItem value={3}>3 years</MenuItem>
                  <MenuItem value={5}>5+ years</MenuItem>
                  <MenuItem value={10}>10+ years</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Skills Section */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Required Skills *
              </Typography>
              
              {/* Skill Input */}
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <TextField
                  label="Add Skill"
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  placeholder="e.g., JavaScript"
                  variant="outlined"
                  size="small"
                  sx={{ flex: 1 }}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddSkill();
                    }
                  }}
                />
                <Button
                  variant="contained"
                  onClick={handleAddSkill}
                  disabled={!skillInput.trim()}
                  startIcon={<AddIcon />}
                  size="large"
                >
                  Add
                </Button>
              </Box>

              {/* Selected Skills */}
              {formData.requiredSkills.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    Selected Skills ({formData.requiredSkills.length}):
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {formData.requiredSkills.map((skill) => (
                      <Chip
                        key={skill}
                        label={skill}
                        onDelete={() => handleRemoveSkill(skill)}
                        color="primary"
                        variant="filled"
                      />
                    ))}
                  </Box>
                </Box>
              )}

              {/* Skill Suggestions */}
              <Paper elevation={1} sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Popular Skills (Click to add):
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {skillSuggestions
                    .filter(skill => !formData.requiredSkills.includes(skill))
                    .slice(0, 12)
                    .map((skill) => (
                    <Chip
                      key={skill}
                      label={skill}
                      onClick={() => handleSkillSuggestionClick(skill)}
                      variant="outlined"
                      size="small"
                      sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'primary.light' } }}
                    />
                  ))}
                </Box>
              </Paper>
            </Grid>

            {/* Job Description */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Job Description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                required
                multiline
                rows={6}
                placeholder="Describe the job responsibilities, requirements, company culture, and any other relevant details..."
                variant="outlined"
              />
            </Grid>

            {/* Error/Success Messages */}
            {error && (
              <Grid item xs={12}>
                <Alert severity="error">
                  {error}
                </Alert>
              </Grid>
            )}

            {success && (
              <Grid item xs={12}>
                <Alert severity="success">
                  Job posted successfully! Job ID: {success.id}
                </Alert>
              </Grid>
            )}

            {/* Submit Button */}
            <Grid item xs={12}>
              <Button
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                disabled={loading || !formData.title.trim() || !formData.company.trim() || !formData.description.trim() || formData.requiredSkills.length === 0}
                startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
                sx={{ py: 1.5, fontSize: '1.1rem' }}
              >
                {loading ? 'Creating Job Posting...' : 'Post Job'}
              </Button>
            </Grid>
          </Grid>
        </Box>
      </CardContent>
    </Card>
  );
};

export default JobForm;