import axios from 'axios'

const API_URL = '/api/v1'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const authAPI = {
  register: (username, email, password) =>
    api.post('/auth/register', { username, email, password }),
  login: (username, password) =>
    api.post('/auth/login', { username, password }),
}

export const userAPI = {
  getMe: () => api.get('/user/me'),
  getBalance: () => api.get('/user/balance'),
  topUp: (amount) => api.post('/user/balance/top-up', { amount }),
}

export const documentAPI = {
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
  getAll: () => api.get('/documents/'),
  getById: (id) => api.get(`/documents/${id}`),
}

export const queryAPI = {
  create: (document_id, question) =>
    api.post('/queries/', { document_id, question }),
  getHistory: () => api.get('/queries/history'),
  getById: (id) => api.get(`/queries/${id}`),
}

export const transactionAPI = {
  getHistory: () => api.get('/transactions/history'),
}

export default api
