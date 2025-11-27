import { useAuth } from '../contexts/AuthContext'

/**
 * Hook para verificar permisos basados en roles
 */
export const useRoleAccess = () => {
  const { userRole } = useAuth()

  return {
    userRole,
    isONG: userRole === 'ONG',
    isAdmin: userRole === 'Admin' || userRole === 'Administrator',
    isReviewer: userRole === 'Reviewer' || userRole === 'Evaluador',
    hasRole: (role: string) => userRole === role,
    hasAnyRole: (...roles: string[]) => roles.includes(userRole || ''),
  }
}
