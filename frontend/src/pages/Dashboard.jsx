import React, { useState, useEffect } from 'react'
import { userAPI, transactionAPI, documentAPI, queryAPI } from '../services/api'

const Dashboard = () => {
  const [balance, setBalance] = useState(0)
  const [topUpAmount, setTopUpAmount] = useState('')
  const [transactions, setTransactions] = useState([])
  const [documents, setDocuments] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [selectedDocument, setSelectedDocument] = useState(null)
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploadLoading, setUploadLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 3000)
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const [balanceRes, transactionsRes, documentsRes] = await Promise.all([
        userAPI.getBalance(),
        transactionAPI.getHistory(),
        documentAPI.getAll(),
      ])
      setBalance(balanceRes.data.balance)
      setTransactions(transactionsRes.data)
      setDocuments(documentsRes.data)
    } catch (error) {
      console.error('Failed to load data:', error)
    }
  }

  const handleTopUp = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    try {
      await userAPI.topUp(parseFloat(topUpAmount))
      setSuccess('Баланс успешно пополнен')
      setTopUpAmount('')
      loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка пополнения баланса')
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setUploadLoading(true)
    setError('')
    setSuccess('')

    try {
      await documentAPI.upload(file)
      setSuccess('Документ успешно загружен')
      setSelectedFile(null)
      e.target.value = ''
      loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка загрузки документа')
    } finally {
      setUploadLoading(false)
    }
  }

  const handleSendQuestion = async (e) => {
    e.preventDefault()
    if (!selectedDocument || !question.trim()) return

    const userMessage = { role: 'user', content: question }
    setMessages([...messages, userMessage])
    setQuestion('')
    setLoading(true)
    setError('')

    try {
      const response = await queryAPI.create(selectedDocument.id, question)

      const pollQuery = async (queryId) => {
        const queryResponse = await queryAPI.getById(queryId)
        const queryData = queryResponse.data

        if (queryData.status === 'completed' && queryData.answer) {
          const assistantMessage = {
            role: 'assistant',
            content: queryData.answer,
            cost: queryData.cost,
            tokens: queryData.total_tokens
          }
          setMessages(prev => [...prev, assistantMessage])
          setLoading(false)
          loadData()
        } else if (queryData.status === 'failed') {
          setError('Ошибка обработки запроса')
          setLoading(false)
          loadData()
        } else {
          setTimeout(() => pollQuery(queryId), 2000)
        }
      }

      await pollQuery(response.data.id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка отправки запроса')
      setLoading(false)
      loadData()
    }
  }

  const getStatusClass = (status) => {
    switch (status) {
      case 'ready': return 'status-ready'
      case 'processing': return 'status-processing'
      case 'uploaded': return 'status-uploaded'
      case 'failed': return 'status-failed'
      default: return ''
    }
  }

  return (
    <div>
      <div className="container">
        <div className="grid grid-2">
          <div className="card">
            <h2>Баланс: ${balance.toFixed(2)}</h2>
            <form onSubmit={handleTopUp}>
              <div className="form-group">
                <label>Сумма пополнения</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  className="input"
                  value={topUpAmount}
                  onChange={(e) => setTopUpAmount(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="btn btn-primary">
                Пополнить
              </button>
            </form>
            {success && <div className="success" style={{ marginTop: '10px' }}>{success}</div>}
            {error && <div className="error" style={{ marginTop: '10px' }}>{error}</div>}
          </div>

          <div className="card">
            <h2>История транзакций</h2>
            <div className="transactions-list">
              {transactions.slice(0, 5).map((transaction) => (
                <div key={transaction.id} className="transaction-item">
                  <span>{transaction.description}</span>
                  <span className={
                    transaction.transaction_type === 'top_up'
                      ? 'transaction-amount-positive'
                      : 'transaction-amount-negative'
                  }>
                    {transaction.transaction_type === 'top_up' ? '+' : '-'}
                    ${Math.abs(transaction.amount).toFixed(2)}
                  </span>
                </div>
              ))}
              {transactions.length === 0 && (
                <div className="loading">Нет транзакций</div>
              )}
            </div>
          </div>
        </div>

        <div className="card">
          <h2>Загрузка документа</h2>
          <div className="file-upload">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              id="file-upload"
              disabled={uploadLoading}
            />
            <label htmlFor="file-upload" style={{ cursor: 'pointer' }}>
              {uploadLoading ? 'Загрузка...' : 'Нажмите для загрузки PDF файла'}
            </label>
          </div>
        </div>

        <div className="card">
          <h2>Мои документы</h2>
          {documents.length === 0 ? (
            <div className="loading">Нет загруженных документов</div>
          ) : (
            documents.map((doc) => (
              <div
                key={doc.id}
                className={`document-item ${selectedDocument?.id === doc.id ? 'selected' : ''}`}
                onClick={() => doc.status === 'ready' && setSelectedDocument(doc)}
              >
                <strong>{doc.filename}</strong>
                <span className={`document-status ${getStatusClass(doc.status)}`}>
                  {doc.status}
                </span>
                <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                  Страниц: {doc.page_count} | Размер: {doc.file_size_mb} MB
                </div>
              </div>
            ))
          )}
        </div>

        {selectedDocument && (
          <div className="card">
            <h2>Чат с документом: {selectedDocument.filename}</h2>
            <div className="chat-container">
              <div className="messages-container">
                {messages.length === 0 && (
                  <div className="loading">Задайте вопрос по документу</div>
                )}
                {messages.map((msg, idx) => (
                  <div key={idx} className={`message message-${msg.role}`}>
                    <div>{msg.content}</div>
                    {msg.cost && (
                      <div style={{ fontSize: '12px', marginTop: '8px', opacity: 0.8 }}>
                        Стоимость: ${msg.cost.toFixed(4)} | Токены: {msg.tokens}
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="message message-assistant">
                    Обрабатываю запрос...
                  </div>
                )}
              </div>
              <form onSubmit={handleSendQuestion} className="chat-input-container">
                <input
                  type="text"
                  className="input chat-input"
                  placeholder="Задайте вопрос..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  disabled={loading}
                />
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  Отправить
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
