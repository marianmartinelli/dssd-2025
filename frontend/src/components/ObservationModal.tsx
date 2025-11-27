import { useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Button,
    Stack,
} from '@mui/material'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createObservation } from '../api/bonita'

interface ObservationModalProps {
    open: boolean
    projectId: number
    onClose: () => void
    onSuccess?: () => void
    onError?: (message: string) => void
}

export const ObservationModal = ({
    open,
    projectId,
    onClose,
    onSuccess,
    onError,
}: ObservationModalProps) => {
    const [title, setTitle] = useState('')
    const [description, setDescription] = useState('')
    const queryClient = useQueryClient()

    const mutation = useMutation({
        mutationFn: createObservation,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['project', String(projectId)] })
            handleClose()
            onSuccess?.()
        },
        onError: (error: Error) => {
            onError?.(error.message || 'Error al crear la observación')
        },
    })

    const handleClose = () => {
        setTitle('')
        setDescription('')
        onClose()
    }

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault()
        if (title.trim().length < 3) {
            onError?.('El título debe tener al menos 3 caracteres')
            return
        }
        if (description.trim() && description.trim().length < 5) {
            onError?.('La descripción debe tener al menos 5 caracteres')
            return
        }
        mutation.mutate({
            projectId,
            title: title.trim(),
            description: description.trim() || undefined,
        })
    }

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
            <form onSubmit={handleSubmit}>
                <DialogTitle>Registrar Observación</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1 }}>
                        <TextField
                            label="Título"
                            value={title}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)}
                            required
                            fullWidth
                            autoFocus
                            inputProps={{ minLength: 3, maxLength: 150 }}
                            helperText="Mínimo 3 caracteres, máximo 150"
                        />
                        <TextField
                            label="Descripción"
                            value={description}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDescription(e.target.value)}
                            multiline
                            rows={4}
                            fullWidth
                            inputProps={{ minLength: 5, maxLength: 1000 }}
                            helperText="Mínimo 5 caracteres, máximo 1000"
                        />
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleClose} disabled={mutation.isPending}>
                        Cancelar
                    </Button>
                    <Button
                        type="submit"
                        variant="contained"
                        disabled={mutation.isPending || title.trim().length < 3}
                    >
                        {mutation.isPending ? 'Guardando...' : 'Guardar'}
                    </Button>
                </DialogActions>
            </form>
        </Dialog>
    )
}
