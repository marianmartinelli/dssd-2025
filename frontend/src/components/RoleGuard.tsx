import type { ReactNode } from 'react'
import { useRoleAccess } from '../hooks/useRoleAccess'

interface RoleGuardProps {
    children: ReactNode
    allowedRoles?: string[]
    fallback?: ReactNode
}

/**
 * Componente para renderizar contenido condicionalmente basado en roles
 * 
 * @example
 * // Solo muestra el botón si el usuario es ONG
 * <RoleGuard allowedRoles={['ONG']}>
 *   <Button>Crear Proyecto</Button>
 * </RoleGuard>
 * 
 * @example
 * // Muestra contenido alternativo si no tiene el rol
 * <RoleGuard allowedRoles={['Admin']} fallback={<p>Sin permisos</p>}>
 *   <AdminPanel />
 * </RoleGuard>
 */
export const RoleGuard = ({ children, allowedRoles, fallback = null }: RoleGuardProps) => {
    const { hasAnyRole } = useRoleAccess()

    if (!allowedRoles || allowedRoles.length === 0) {
        return <>{children}</>
    }

    if (hasAnyRole(...allowedRoles)) {
        return <>{children}</>
    }

    return <>{fallback}</>
}
