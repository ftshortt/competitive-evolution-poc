import axios from 'axios';

const API_BASE_URL = '/api';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Send a chat message to the assistant
 * @param {string} message - The message to send
 * @returns {Promise<Object>} Response containing the assistant's message
 */
export const sendChatMessage = async (message) => {
  try {
    const response = await apiClient.post('/chat', { message });
    return response.data;
  } catch (error) {
    console.error('Error sending chat message:', error);
    throw error;
  }
};

/**
 * Start the experiment
 * @returns {Promise<Object>} Response containing the experiment status
 */
export const startExperiment = async () => {
  try {
    const response = await apiClient.post('/experiment/start');
    return response.data;
  } catch (error) {
    console.error('Error starting experiment:', error);
    throw error;
  }
};

/**
 * Stop the experiment
 * @returns {Promise<Object>} Response containing the experiment status
 */
export const stopExperiment = async () => {
  try {
    const response = await apiClient.post('/experiment/stop');
    return response.data;
  } catch (error) {
    console.error('Error stopping experiment:', error);
    throw error;
  }
};

/**
 * Get the current experiment status
 * @returns {Promise<Object>} Response containing current status, generation, fitness, and pool count
 */
export const getStatus = async () => {
  try {
    const response = await apiClient.get('/experiment/status');
    return response.data;
  } catch (error) {
    console.error('Error fetching status:', error);
    throw error;
  }
};

export default {
  sendChatMessage,
  startExperiment,
  stopExperiment,
  getStatus,
};
