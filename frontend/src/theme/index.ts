import { createTheme } from '@mui/material/styles'

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1565c0',
    },
    secondary: {
      main: '#00acc1',
    },
    background: {
      default: '#f7f9fc',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
      '@media (max-width: 599px)': {
        fontSize: '1.5rem',
      },
      '@media (min-width: 600px)': {
        fontSize: '1.75rem',
      },
      '@media (min-width: 960px)': {
        fontSize: '2rem',
      },
    },
    h6: {
      fontWeight: 500,
      '@media (max-width: 599px)': {
        fontSize: '1rem',
      },
      '@media (min-width: 600px)': {
        fontSize: '1.125rem',
      },
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiTextField: {
      defaultProps: {
        variant: 'outlined',
        fullWidth: true,
        size: 'small',
      },
      styleOverrides: {
        root: {
          '& .MuiInputBase-root': {
            borderRadius: 8,
            '@media (min-width: 600px)': {
              borderRadius: 10,
            },
          },
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          '@media (min-width: 600px)': {
            borderRadius: 10,
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
          '@media (min-width: 600px)': {
            borderRadius: 10,
            padding: '10px 20px',
          },
        },
        sizeLarge: {
          padding: '12px 24px',
          fontSize: '1rem',
          '@media (max-width: 599px)': {
            padding: '14px 20px',
            fontSize: '1.1rem',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          '@media (min-width: 600px)': {
            borderRadius: 10,
          },
        },
      },
    },
    MuiStack: {
      defaultProps: {
        useFlexGap: true,
      },
    },
  },
})
