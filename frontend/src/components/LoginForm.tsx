import { useState } from 'react'
import {
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  CircularProgress,
} from '@mui/material'
import type { AlertColor } from '@mui/material'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { login } from '../api/bonita'
import { useAuth } from '../contexts/AuthContext'

const loginSchema = z.object({
  username: z.string(),
  password: z.string(),
})

type LoginFormValues = z.infer<typeof loginSchema>

interface LoginFormProps {
  onSuccess: () => void
  onError: (message: string, severity?: AlertColor) => void
}

export const LoginForm = ({ onSuccess, onError }: LoginFormProps) => {
  const { login: authLogin } = useAuth()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    mode: 'onBlur',
  })

  const [isSubmitting, setIsSubmitting] = useState(false)

  const onSubmit = async (values: LoginFormValues) => {
    setIsSubmitting(true)
    try {
      const { role, username } = await login(values.username, values.password)
      authLogin(role, username)
      onSuccess()
    } catch (error) {
      console.error(error)
      onError('Credenciales inválidas o error de conexión.', 'error')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Paper elevation={6} sx={{ p: 4, width: '100%', maxWidth: 420 }}>
      <Typography variant="h5" component="h1" gutterBottom textAlign="center">
        Iniciar sesión
      </Typography>
      <Typography variant="body2" color="text.secondary" textAlign="center" mb={3}>
        Ingresá con tus credenciales provistas por el equipo administrador.
      </Typography>

      <Box component="form" onSubmit={handleSubmit(onSubmit)} display="grid" gap={2}>
        <TextField
          label="Usuario"
          autoComplete="username"
          {...register('username')}
          error={!!errors.username}
          helperText={errors.username?.message}
        />

        <TextField
          label="Contraseña"
          type="password"
          autoComplete="current-password"
          {...register('password')}
          error={!!errors.password}
          helperText={errors.password?.message}
        />

        <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
          {isSubmitting ? <CircularProgress size={24} /> : 'Ingresar'}
        </Button>
      </Box>
    </Paper>
  )
}
