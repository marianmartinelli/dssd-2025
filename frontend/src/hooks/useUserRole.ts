/**
 * Hook para obtener el rol del usuario autenticado
 */
export const useUserRole = (): string | null => {
  const role = localStorage.getItem('projectplanning_user_role')
  return role
}
