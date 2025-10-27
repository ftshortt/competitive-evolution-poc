import axios from 'axios';
const API_BASE_URL = '/api';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Chat
export const sendChatMessage = async (message, agent_id) => {
  const payload = agent_id ? { message, agent_id } : { message };
  const { data } = await apiClient.post('/chat', payload);
  return data;
};

// Agent lifecycle
export const spawnAgent = async ({ parent_id, traits, name }) => {
  const { data } = await apiClient.post('/agent/spawn', { parent_id, traits, name });
  return data;
};

export const retireAgent = async ({ agent_id }) => {
  const { data } = await apiClient.post('/agent/retire', { agent_id });
  return data;
};

export const getAgentStatus = async () => {
  const { data } = await apiClient.get('/agent/status');
  return data;
};

export const getAgentFamily = async (agent_id) => {
  const { data } = await apiClient.get(`/agent/family/${agent_id}`);
  return data;
};

export const postAgentTopic = async ({ agent_id, topic, category }) => {
  const { data } = await apiClient.post('/agent/topic', { agent_id, topic, category });
  return data;
};

// Experiment controls (existing)
export const startExperiment = async () => {
  const { data } = await apiClient.post('/experiment/start');
  return data;
};

export const stopExperiment = async () => {
  const { data } = await apiClient.post('/experiment/stop');
  return data;
};

export const getStatus = async () => {
  const { data } = await apiClient.get('/experiment/status');
  return data;
};

export default {
  sendChatMessage,
  spawnAgent,
  retireAgent,
  getAgentStatus,
  getAgentFamily,
  postAgentTopic,
  startExperiment,
  stopExperiment,
  getStatus,
};
