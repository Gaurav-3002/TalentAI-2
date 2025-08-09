import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  RadioGroup,
  Radio,
  FormControlLabel,
  LinearProgress,
  Alert,
  Paper,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Quiz as QuizIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  ExpandMore as ExpandMoreIcon,
  Timer as TimerIcon,
} from '@mui/icons-material';
import { generateQuiz, calculateQuizScore } from '../utils/validationQuiz';

const ValidationQuiz = ({ 
  candidateSkills = [], 
  onComplete, 
  onSkip 
}) => {
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [quizResults, setQuizResults] = useState(null);
  const [timeLeft, setTimeLeft] = useState(300); // 5 minutes
  const [quizStarted, setQuizStarted] = useState(false);

  useEffect(() => {
    // Generate quiz questions based on candidate skills
    const quizQuestions = generateQuiz(candidateSkills);
    setQuestions(quizQuestions);
  }, [candidateSkills]);

  useEffect(() => {
    let timer;
    if (quizStarted && timeLeft > 0 && !showResults) {
      timer = setTimeout(() => {
        setTimeLeft(timeLeft - 1);
      }, 1000);
    } else if (timeLeft === 0 && !showResults) {
      // Time's up, finish quiz
      handleFinishQuiz();
    }
    return () => clearTimeout(timer);
  }, [timeLeft, quizStarted, showResults]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleStartQuiz = () => {
    setQuizStarted(true);
    setAnswers(new Array(questions.length).fill(-1));
  };

  const handleAnswerChange = (event) => {
    setSelectedAnswer(parseInt(event.target.value));
  };

  const handleNextQuestion = () => {
    const newAnswers = [...answers];
    newAnswers[currentQuestionIndex] = selectedAnswer;
    setAnswers(newAnswers);
    setSelectedAnswer('');

    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      handleFinishQuiz(newAnswers);
    }
  };

  const handleFinishQuiz = (finalAnswers = answers) => {
    const results = calculateQuizScore(finalAnswers, questions);
    const enhancedResults = {
      ...results,
      questions: questions,
      answers: finalAnswers,
      timeSpent: 300 - timeLeft,
      skills: candidateSkills
    };
    
    setQuizResults(enhancedResults);
    setShowResults(true);
    
    if (onComplete) {
      onComplete(enhancedResults);
    }
  };

  const currentQuestion = questions[currentQuestionIndex];
  const progress = questions.length > 0 ? ((currentQuestionIndex + 1) / questions.length) * 100 : 0;

  // Quiz Introduction
  if (!quizStarted && questions.length > 0) {
    return (
      <Card sx={{ maxWidth: 600, mx: 'auto' }}>
        <CardContent sx={{ p: 4, textAlign: 'center' }}>
          <QuizIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
          <Typography variant="h4" gutterBottom>
            Skill Validation Test
          </Typography>
          
          <Alert severity="info" sx={{ mb: 3, textAlign: 'left' }}>
            <Typography variant="body1" gutterBottom>
              <strong>Test Instructions:</strong>
            </Typography>
            <ul style={{ margin: 0, paddingLeft: '20px' }}>
              <li>This quiz contains {questions.length} questions</li>
              <li>Time limit: 5 minutes</li>
              <li>Questions are based on your skills</li>
              <li>Choose the best answer for each question</li>
              <li>You cannot go back to previous questions</li>
            </ul>
          </Alert>

          <Paper elevation={1} sx={{ p: 2, mb: 3, bgcolor: 'grey.50' }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Your Skills to be Tested:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
              {candidateSkills.slice(0, 8).map((skill) => (
                <Chip
                  key={skill}
                  label={skill}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              ))}
              {candidateSkills.length > 8 && (
                <Chip
                  label={`+${candidateSkills.length - 8} more`}
                  size="small"
                  variant="outlined"
                />
              )}
            </Box>
          </Paper>

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              size="large"
              onClick={handleStartQuiz}
              startIcon={<QuizIcon />}
              sx={{ px: 4 }}
            >
              Start Test
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={onSkip}
              sx={{ px: 4 }}
            >
              Skip for Now
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  }

  // Quiz Results
  if (showResults && quizResults) {
    const getScoreColor = () => {
      if (quizResults.score >= 80) return 'success.main';
      if (quizResults.score >= 60) return 'warning.main';
      return 'error.main';
    };

    const getScoreIcon = () => {
      if (quizResults.score >= 60) return <CheckCircleIcon sx={{ fontSize: 60, color: getScoreColor() }} />;
      return <CancelIcon sx={{ fontSize: 60, color: getScoreColor() }} />;
    };

    return (
      <Card sx={{ maxWidth: 700, mx: 'auto' }}>
        <CardContent sx={{ p: 4, textAlign: 'center' }}>
          {getScoreIcon()}
          
          <Typography variant="h4" sx={{ color: getScoreColor(), mb: 2 }}>
            Quiz Complete!
          </Typography>
          
          <Typography variant="h2" sx={{ color: getScoreColor(), mb: 3 }}>
            {quizResults.score.toFixed(1)}%
          </Typography>
          
          <Typography variant="h6" gutterBottom>
            {quizResults.correct} out of {quizResults.total} questions correct
          </Typography>
          
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Time taken: {Math.floor(quizResults.timeSpent / 60)}:{(quizResults.timeSpent % 60).toString().padStart(2, '0')}
          </Typography>

          {/* Score interpretation */}
          <Alert severity={quizResults.score >= 60 ? 'success' : 'warning'} sx={{ mb: 3 }}>
            <Typography variant="body2">
              {quizResults.score >= 80 && 'Excellent! You demonstrated strong knowledge in your skill areas.'}
              {quizResults.score >= 60 && quizResults.score < 80 && 'Good job! You showed solid understanding with room for improvement.'}
              {quizResults.score < 60 && 'Consider reviewing the topics covered. This score may affect your match rankings.'}
            </Typography>
          </Alert>

          {/* Detailed Results */}
          <Accordion sx={{ mb: 3, textAlign: 'left' }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">
                View Detailed Results
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {quizResults.questions.map((question, index) => {
                const userAnswer = quizResults.answers[index];
                const isCorrect = userAnswer === question.correct;
                
                return (
                  <Box key={question.id} sx={{ mb: 3, p: 2, border: '1px solid', borderColor: 'grey.300', borderRadius: 1 }}>
                    <Typography variant="subtitle2" sx={{ mb: 2 }}>
                      Q{index + 1}: {question.question}
                    </Typography>
                    
                    <Box sx={{ mb: 2 }}>
                      {question.options.map((option, optIndex) => {
                        let color = 'text.primary';
                        let fontWeight = 'normal';
                        
                        if (optIndex === question.correct) {
                          color = 'success.main';
                          fontWeight = 'bold';
                        } else if (optIndex === userAnswer && !isCorrect) {
                          color = 'error.main';
                          fontWeight = 'bold';
                        }
                        
                        return (
                          <Typography
                            key={optIndex}
                            variant="body2"
                            sx={{ color, fontWeight, mb: 0.5 }}
                          >
                            {optIndex === question.correct && '✓ '}
                            {optIndex === userAnswer && optIndex !== question.correct && '✗ '}
                            {String.fromCharCode(65 + optIndex)}. {option}
                          </Typography>
                        );
                      })}
                    </Box>
                    
                    <Alert severity={isCorrect ? 'success' : 'error'} sx={{ fontSize: '0.875rem' }}>
                      {question.explanation}
                    </Alert>
                  </Box>
                );
              })}
            </AccordionDetails>
          </Accordion>

          <Button
            variant="contained"
            size="large"
            onClick={() => window.location.href = '/'}
            sx={{ px: 4 }}
          >
            Continue to Dashboard
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Active Quiz
  if (quizStarted && currentQuestion) {
    return (
      <Card sx={{ maxWidth: 600, mx: 'auto' }}>
        <CardContent sx={{ p: 4 }}>
          {/* Header with progress and timer */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Question {currentQuestionIndex + 1} of {questions.length}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', color: timeLeft < 60 ? 'error.main' : 'text.secondary' }}>
              <TimerIcon sx={{ mr: 1 }} />
              <Typography variant="h6" sx={{ fontFamily: 'monospace' }}>
                {formatTime(timeLeft)}
              </Typography>
            </Box>
          </Box>

          {/* Progress bar */}
          <LinearProgress
            variant="determinate"
            value={progress}
            sx={{ mb: 4, height: 8, borderRadius: 4 }}
          />

          {/* Question */}
          <Typography variant="h6" sx={{ mb: 3, lineHeight: 1.5 }}>
            {currentQuestion.question}
          </Typography>

          {/* Answer options */}
          <RadioGroup
            value={selectedAnswer.toString()}
            onChange={handleAnswerChange}
            sx={{ mb: 4 }}
          >
            {currentQuestion.options.map((option, index) => (
              <FormControlLabel
                key={index}
                value={index.toString()}
                control={<Radio />}
                label={
                  <Typography variant="body1">
                    <strong>{String.fromCharCode(65 + index)}.</strong> {option}
                  </Typography>
                }
                sx={{
                  mb: 1,
                  p: 1,
                  borderRadius: 1,
                  '&:hover': { bgcolor: 'grey.50' },
                  '& .MuiRadio-root': { alignSelf: 'flex-start', mt: 0.5 }
                }}
              />
            ))}
          </RadioGroup>

          {/* Next button */}
          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={handleNextQuestion}
            disabled={selectedAnswer === ''}
            sx={{ py: 1.5 }}
          >
            {currentQuestionIndex < questions.length - 1 ? 'Next Question' : 'Finish Quiz'}
          </Button>
        </CardContent>
      </Card>
    );
  }

  return null;
};

export default ValidationQuiz;