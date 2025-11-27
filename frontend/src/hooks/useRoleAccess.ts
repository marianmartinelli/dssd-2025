import { useAuth } from '../contexts/AuthContext'

/**
 * Hook para verificar permisos basados en roles
 */
export const useRoleAccess = () => {
  const { userRole } = useAuth()

  return {
    userRole,
    isONG: userRole === 'ONG',
    isConsejo: userRole === 'Consejo Directivo',
    isGerente: userRole === 'Gerente',
    hasRole: (role: string) => userRole === role,
    hasAnyRole: (...roles: string[]) => roles.includes(userRole || ''),
  }
}
