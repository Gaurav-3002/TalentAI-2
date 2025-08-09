import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Box, Paper, Typography, useTheme } from '@mui/material';

const ScoreChart = ({ matchResult, showTitle = true }) => {
  const theme = useTheme();

  if (!matchResult) {
    return null;
  }

  const data = [
    {
      name: 'Semantic\nSimilarity',
      score: (matchResult.semantic_score * 100).toFixed(1),
      weight: 40,
      color: theme.palette.primary.main,
    },
    {
      name: 'Skill\nOverlap',
      score: (matchResult.skill_overlap_score * 100).toFixed(1),
      weight: 40,
      color: theme.palette.success.main,
    },
    {
      name: 'Experience\nMatch',
      score: (matchResult.experience_match_score * 100).toFixed(1),
      weight: 20,
      color: theme.palette.warning.main,
    },
  ];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Paper elevation={3} sx={{ p: 2, maxWidth: 200 }}>
          <Typography variant="body2" fontWeight="bold">
            {label}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Score: {data.score}%
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Weight: {data.weight}%
          </Typography>
        </Paper>
      );
    }
    return null;
  };

  const CustomBar = (props) => {
    const { fill, payload, ...rest } = props;
    return <Bar {...rest} fill={payload.color} />;
  };

  return (
    <Box>
      {showTitle && (
        <Typography variant="h6" gutterBottom>
          Score Breakdown
        </Typography>
      )}
      <Paper elevation={2} sx={{ p: 2, height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{
              top: 20,
              right: 30,
              left: 20,
              bottom: 60,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.grey[300]} />
            <XAxis 
              dataKey="name" 
              tick={{ fontSize: 12 }}
              interval={0}
              angle={0}
              textAnchor="middle"
              height={80}
            />
            <YAxis 
              domain={[0, 100]}
              tick={{ fontSize: 12 }}
              label={{ value: 'Score (%)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar 
              dataKey="score" 
              radius={[4, 4, 0, 0]}
              shape={<CustomBar />}
            />
          </BarChart>
        </ResponsiveContainer>
      </Paper>
      
      {/* Overall Score Display */}
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Typography variant="h6" color="primary">
          Overall Match Score: {(matchResult.total_score * 100).toFixed(1)}%
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Weighted average of all factors
        </Typography>
      </Box>
    </Box>
  );
};

export default ScoreChart;