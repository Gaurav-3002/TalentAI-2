import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isGuest, setIsGuest] = useState(false);

  // Initialize auth state from localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('user_data');
    const storedGuest = localStorage.getItem('guest_mode');
    
    if (storedGuest === 'true') {
      // Guest mode
      setIsGuest(true);
      setIsAuthenticated(true);
      setUser({
        id: 'guest',
        email: 'guest@demo.com',
        full_name: 'Guest User',
        role: 'guest',
        is_active: true,
        is_verified: false
      });
    } else if (storedToken && storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setToken(storedToken);
        setUser(userData);
        setIsAuthenticated(true);
        
        // Set the token in API headers
        api.setAuthToken(storedToken);
        
        // Verify token is still valid
        api.getCurrentUser()
          .then(currentUser => {
            setUser(currentUser);
            setIsAuthenticated(true);
          })
          .catch(() => {
            // Token is invalid, clear auth state
            logout();
          });
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        logout();
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const response = await api.login(email, password);
      const { access_token, user: userData } = response;
      
      // Store auth data
      localStorage.setItem('auth_token', access_token);
      localStorage.setItem('user_data', JSON.stringify(userData));
      
      // Update state
      setToken(access_token);
      setUser(userData);
      setIsAuthenticated(true);
      
      // Set token in API headers
      api.setAuthToken(access_token);
      
      return { success: true, user: userData };
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await api.register(userData);
      return { success: true, user: response };
    } catch (error) {
      console.error('Registration error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const loginAsGuest = () => {
    // Set guest mode
    localStorage.setItem('guest_mode', 'true');
    
    // Create guest user object
    const guestUser = {
      id: 'guest',
      email: 'guest@demo.com',
      full_name: 'Guest User',
      role: 'guest',
      is_active: true,
      is_verified: false
    };
    
    // Update state
    setUser(guestUser);
    setIsAuthenticated(true);
    setIsGuest(true);
    
    return { success: true, user: guestUser };
  };

  const logout = () => {
    // Clear stored data
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    localStorage.removeItem('guest_mode');
    
    // Reset state
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    setIsGuest(false);
    
    // Clear token from API headers
    api.setAuthToken(null);
  };

  const hasRole = (requiredRoles) => {
    if (!user || !user.role) return false;
    if (Array.isArray(requiredRoles)) {
      return requiredRoles.includes(user.role);
    }
    return user.role === requiredRoles;
  };

  const isAdmin = () => hasRole('admin');
  const isRecruiter = () => hasRole(['admin', 'recruiter']);
  const isCandidate = () => hasRole('candidate');
  const isGuestUser = () => isGuest || hasRole('guest');

  const value = {
    user,
    token,
    loading,
    isAuthenticated,
    isGuest,
    login,
    register,
    loginAsGuest,
    logout,
    hasRole,
    isAdmin,
    isRecruiter,
    isCandidate,
    isGuestUser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;