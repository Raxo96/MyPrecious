import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const portfolioApi = {
  getPortfolio: (id = 1) => apiClient.get(`/portfolios/${id}`),
  getPositions: (id = 1) => apiClient.get(`/portfolios/${id}/positions`),
  getChart: (id = 1, days = 30) => apiClient.get(`/portfolios/${id}/history?days=${days}`),
}

export const assetApi = {
  search: (query, limit = 20) => apiClient.get(`/assets/search?q=${query}&limit=${limit}`),
  getAsset: (id) => apiClient.get(`/assets/${id}`),
  getChart: (id, range = '1M') => apiClient.get(`/assets/${id}/chart?range=${range}`),
}

export const transactionApi = {
  create: (transaction) => apiClient.post('/transactions', transaction),
  getAll: (portfolioId) => apiClient.get(`/transactions?portfolio_id=${portfolioId}`),
}

export default apiClient