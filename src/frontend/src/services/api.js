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
  getAsset: (symbol) => apiClient.get(`/assets/${symbol}`),
  getChart: (symbol) => apiClient.get(`/assets/${symbol}/chart`),
}

export const transactionApi = {
  create: (transaction) => apiClient.post('/transactions', transaction),
  getAll: (portfolioId) => apiClient.get(`/transactions?portfolio_id=${portfolioId}`),
}

export const fetcherApi = {
  getStatus: () => apiClient.get('/fetcher/status'),
  getLogs: (limit = 100, offset = 0, level = null) => {
    const params = new URLSearchParams({ limit, offset })
    if (level) params.append('level', level)
    return apiClient.get(`/fetcher/logs?${params}`)
  },
  getStatistics: () => apiClient.get('/fetcher/statistics'),
  getRecentUpdates: (limit = 50) => apiClient.get(`/fetcher/recent-updates?limit=${limit}`),
  triggerUpdate: () => apiClient.post('/fetcher/trigger-update'),
}

export default apiClient