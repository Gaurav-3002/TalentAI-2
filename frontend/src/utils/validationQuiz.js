// Sample validation quiz questions for different skill areas
export const validationQuestions = {
  javascript: [
    {
      id: 1,
      question: "What is the output of: console.log(typeof null)?",
      options: ["null", "object", "undefined", "string"],
      correct: 1,
      explanation: "In JavaScript, typeof null returns 'object' due to a historical bug that was never fixed for backward compatibility."
    },
    {
      id: 2,
      question: "Which method is used to add an element to the end of an array?",
      options: ["push()", "pop()", "shift()", "unshift()"],
      correct: 0,
      explanation: "push() adds elements to the end of an array and returns the new length."
    },
    {
      id: 3,
      question: "What does 'hoisting' mean in JavaScript?",
      options: [
        "Moving variables to global scope",
        "Variable and function declarations are moved to the top of their scope",
        "Creating new variables",
        "Deleting variables"
      ],
      correct: 1,
      explanation: "Hoisting is JavaScript's default behavior of moving declarations to the top of their scope."
    }
  ],
  python: [
    {
      id: 1,
      question: "What is the output of: print(type([]))?",
      options: ["<class 'array'>", "<class 'list'>", "<class 'tuple'>", "<class 'dict'>"],
      correct: 1,
      explanation: "[] creates an empty list in Python, so type([]) returns <class 'list'>."
    },
    {
      id: 2,
      question: "Which Python keyword is used to create a function?",
      options: ["func", "def", "function", "define"],
      correct: 1,
      explanation: "The 'def' keyword is used to define functions in Python."
    },
    {
      id: 3,
      question: "What is the difference between a list and a tuple in Python?",
      options: [
        "Lists are mutable, tuples are immutable",
        "Lists are immutable, tuples are mutable",
        "No difference",
        "Lists are faster than tuples"
      ],
      correct: 0,
      explanation: "Lists are mutable (can be changed after creation), while tuples are immutable (cannot be changed after creation)."
    }
  ],
  react: [
    {
      id: 1,
      question: "What is a React Hook?",
      options: [
        "A React component",
        "A function that lets you use state and lifecycle features in functional components",
        "A React library",
        "A React router"
      ],
      correct: 1,
      explanation: "Hooks are functions that let you use state and other React features in functional components."
    },
    {
      id: 2,
      question: "Which hook is used to manage state in functional components?",
      options: ["useEffect", "useState", "useContext", "useReducer"],
      correct: 1,
      explanation: "useState is the hook used to add state to functional components."
    },
    {
      id: 3,
      question: "What does JSX stand for?",
      options: [
        "JavaScript XML",
        "Java Syntax Extension",
        "JavaScript Extension",
        "JSON XML"
      ],
      correct: 0,
      explanation: "JSX stands for JavaScript XML and allows you to write HTML-like syntax in JavaScript."
    }
  ],
  general: [
    {
      id: 1,
      question: "What does API stand for?",
      options: [
        "Application Programming Interface",
        "Application Program Integration",
        "Advanced Programming Interface",
        "Automated Programming Interface"
      ],
      correct: 0,
      explanation: "API stands for Application Programming Interface."
    },
    {
      id: 2,
      question: "What is the purpose of version control systems like Git?",
      options: [
        "To compile code",
        "To track changes in code and collaborate with others",
        "To run applications",
        "To create databases"
      ],
      correct: 1,
      explanation: "Version control systems like Git help track changes in code and enable collaboration among developers."
    },
    {
      id: 3,
      question: "What does HTTP stand for?",
      options: [
        "HyperText Transfer Protocol",
        "High Text Transfer Protocol",
        "HyperText Transmission Protocol",
        "High Technology Transfer Protocol"
      ],
      correct: 0,
      explanation: "HTTP stands for HyperText Transfer Protocol."
    }
  ]
};

// Generate a quiz based on candidate skills
export const generateQuiz = (candidateSkills) => {
  let questions = [];
  
  // Add skill-specific questions
  candidateSkills.forEach(skill => {
    const skillKey = skill.toLowerCase();
    if (validationQuestions[skillKey]) {
      questions = questions.concat(validationQuestions[skillKey]);
    }
  });
  
  // Always add some general questions
  questions = questions.concat(validationQuestions.general);
  
  // Shuffle and limit to 5 questions
  const shuffled = questions.sort(() => 0.5 - Math.random());
  return shuffled.slice(0, 5);
};

// Calculate quiz score
export const calculateQuizScore = (answers, questions) => {
  let correct = 0;
  answers.forEach((answer, index) => {
    if (answer === questions[index].correct) {
      correct++;
    }
  });
  
  return {
    score: (correct / questions.length) * 100,
    correct: correct,
    total: questions.length
  };
};