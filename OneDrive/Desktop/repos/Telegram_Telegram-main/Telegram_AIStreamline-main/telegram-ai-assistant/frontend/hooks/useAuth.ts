import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { AUTH_CONFIG } from '../utils/constants'

interface User {
  id: number
  name: string
  email: string
  role: 'admin' | 'user'
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

export function useAuth() {
  const router = useRouter()
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  })

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem(AUTH_CONFIG.TOKEN_KEY)
      if (!token) {
        setAuthState({ user: null, isAuthenticated: false, isLoading: false })
        return
      }

      // TODO: Implement token validation with backend
      // For now, we'll just check if token exists
      setAuthState({
        user: {
          id: 1,
          name: 'Admin User',
          email: 'admin@example.com',
          role: 'admin',
        },
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      console.error('Auth check failed:', error)
      setAuthState({ user: null, isAuthenticated: false, isLoading: false })
    }
  }

  const login = async (email: string, password: string) => {
    try {
      // TODO: Implement actual login with backend
      const token = 'dummy_token'
      localStorage.setItem(AUTH_CONFIG.TOKEN_KEY, token)
      
      setAuthState({
        user: {
          id: 1,
          name: 'Admin User',
          email: email,
          role: 'admin',
        },
        isAuthenticated: true,
        isLoading: false,
      })

      router.push('/')
      return { success: true }
    } catch (error) {
      console.error('Login failed:', error)
      return { success: false, error: 'Invalid credentials' }
    }
  }

  const logout = () => {
    localStorage.removeItem(AUTH_CONFIG.TOKEN_KEY)
    setAuthState({ user: null, isAuthenticated: false, isLoading: false })
    router.push('/login')
  }

  const updateUser = (userData: Partial<User>) => {
    if (authState.user) {
      setAuthState({
        ...authState,
        user: { ...authState.user, ...userData },
      })
    }
  }

  return {
    user: authState.user,
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    login,
    logout,
    updateUser,
  }
}
