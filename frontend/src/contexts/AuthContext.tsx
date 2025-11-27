import { createContext, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'

interface AuthContextType {
    isAuthenticated: boolean
    userRole: string | null
    username: string | null
    login: (role: string, username: string) => void
    logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(() => {
        return !!localStorage.getItem('projectplanning_token')
    })

    const [userRole, setUserRole] = useState<string | null>(() => {
        return localStorage.getItem('projectplanning_user_role')
    })

    const [username, setUsername] = useState<string | null>(() => {
        return localStorage.getItem('projectplanning_username')
    })

    const login = (role: string, user: string) => {
        localStorage.setItem('projectplanning_user_role', role)
        localStorage.setItem('projectplanning_username', user)
        setUserRole(role)
        setUsername(user)
        setIsAuthenticated(true)
    }

    const logout = () => {
        localStorage.removeItem('projectplanning_token')
        localStorage.removeItem('projectplanning_user_role')
        localStorage.removeItem('projectplanning_username')
        setUserRole(null)
        setUsername(null)
        setIsAuthenticated(false)
    }

    // Sincronizar con cambios en localStorage (por ejemplo, logout en otra pestaña)
    useEffect(() => {
        const handleStorageChange = () => {
            const token = localStorage.getItem('projectplanning_token')
            const role = localStorage.getItem('projectplanning_user_role')
            const user = localStorage.getItem('projectplanning_username')

            setIsAuthenticated(!!token)
            setUserRole(role)
            setUsername(user)
        }

        window.addEventListener('storage', handleStorageChange)
        return () => window.removeEventListener('storage', handleStorageChange)
    }, [])

    return (
        <AuthContext.Provider value={{ isAuthenticated, userRole, username, login, logout }}>
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
