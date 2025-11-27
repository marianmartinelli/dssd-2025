import { useState } from 'react'
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Button,
    Stack,
    MenuItem,
} from '@mui/material'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createCollaboration } from '../api/bonita'
import type { CollaborationCreatePayload } from '../types/project'

interface CreateCollaborationModalProps {
    open: boolean
    projectId: number
    stageId: number
    stageName: string
    onClose: () => void
    onSuccess?: () => void
    onError?: (message: string) => void
}

const CURRENCIES = ['ARS', 'USD', 'EUR', 'BRL', 'UYU']

export const CreateCollaborationModal = ({
    open,
    projectId,
    stageId,
    stageName,
    onClose,
    onSuccess,
    onError,
}: CreateCollaborationModalProps) => {
    const [title, setTitle] = useState('')
    const [description, setDescription] = useState('')
    const [requestedAmount, setRequestedAmount] = useState('')
    const [amountCurrency, setAmountCurrency] = useState('ARS')
    const queryClient = useQueryClient()

    const mutation = useMutation({
        mutationFn: createCollaboration,
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ['collaborations', projectId, stageId]
            })
            handleClose()
            onSuccess?.()
        },
        onError: (error: Error) => {
            onError?.(error.message || 'Error al crear la colaboración')
        },
    })

    const handleClose = () => {
        setTitle('')
        setDescription('')
        setRequestedAmount('')
        setAmountCurrency('ARS')
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
        if (requestedAmount && parseFloat(requestedAmount) < 0) {
            onError?.('El monto solicitado debe ser mayor o igual a 0')
            return
        }

        const payload: CollaborationCreatePayload = {
            projectId,
            stageId,
            title: title.trim(),
            description: description.trim() || undefined,
            requestedAmount: requestedAmount ? parseFloat(requestedAmount) : undefined,
            amountCurrency: requestedAmount ? amountCurrency : undefined,
        }

        mutation.mutate(payload)
    }

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
            <form onSubmit={handleSubmit}>
                <DialogTitle>
                    Crear Compromiso de Colaboración - {stageName}
                </DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1 }}>
                        <TextField
                            label="Título"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            required
                            fullWidth
                            autoFocus
                            inputProps={{ minLength: 3, maxLength: 150 }}
                            helperText="Mínimo 3 caracteres, máximo 150"
                        />
                        <TextField
                            label="Descripción"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            multiline
                            rows={4}
                            fullWidth
                            inputProps={{ minLength: 5, maxLength: 1000 }}
                            helperText="Opcional. Mínimo 5 caracteres, máximo 1000"
                        />
                        <TextField
                            label="Monto solicitado"
                            value={requestedAmount}
                            onChange={(e) => setRequestedAmount(e.target.value)}
                            type="number"
                            fullWidth
                            inputProps={{ min: 0, step: 0.01 }}
                            helperText="Opcional. Monto a solicitar para esta colaboración"
                        />
                        {requestedAmount && (
                            <TextField
                                label="Moneda"
                                value={amountCurrency}
                                onChange={(e) => setAmountCurrency(e.target.value)}
                                select
                                fullWidth
                                required={!!requestedAmount}
                            >
                                {CURRENCIES.map((currency) => (
                                    <MenuItem key={currency} value={currency}>
                                        {currency}
                                    </MenuItem>
                                ))}
                            </TextField>
                        )}
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
                        {mutation.isPending ? 'Creando...' : 'Crear'}
                    </Button>
                </DialogActions>
            </form>
        </Dialog>
    )
}
