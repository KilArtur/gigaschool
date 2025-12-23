import React, { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { userAPI } from '../services/api'

const Header = () => {
  const { user, logout } = useAuth()
  const [balance, setBalance] = useState(null)

  useEffect(() => {
    loadBalance()
    const interval = setInterval(loadBalance, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadBalance = async () => {
    try {
      const response = await userAPI.getBalance()
      setBalance(response.data.balance)
    } catch (error) {
      console.error('Failed to load balance:', error)
    }
  }

  return (
    <div className="header">
      <div className="header-content">
        <div className="logo">GigaSchool RAG</div>
        <div className="nav">
          <span className="nav-link">{user?.username}</span>
          {balance !== null && (
            <span className="balance-badge">Баланс: ${balance.toFixed(2)}</span>
          )}
          <button onClick={logout} className="btn btn-secondary">
            Выйти
          </button>
        </div>
      </div>
    </div>
  )
}

export default Header
