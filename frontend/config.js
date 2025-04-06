// Get the current hostname
const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // If it's localhost, use localhost, otherwise use the current hostname
    return hostname === 'localhost' 
      ? 'http://localhost:8000'
      : `http://${hostname}:8000`;
  }
  // Default to localhost for server-side rendering
  return 'http://localhost:8000';
};

export const API_URL = getApiUrl(); 