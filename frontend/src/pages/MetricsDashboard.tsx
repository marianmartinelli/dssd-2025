import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import {
  Typography,
  Box,
  Container,
  Grid,
  Paper,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Group as UsersIcon,
  TrendingUp as TrendingUpIcon,
  AccessTime as ClockIcon,
  Warning as AlertTriangleIcon,
  Lock as LockIcon,
  CheckCircle as CheckCircleIcon,
  BarChart as BarChart3Icon,
  List as ListIcon,
} from '@mui/icons-material';

// --- DEFINICIONES DE TIPOS (TYPESCRIPT INTERFACES) ---

// Tipo de dato para el ranking de ONGs (Indicador 1)
interface OngRankingItem {
  ong_name: string;
  colaboraciones: number;
}

// Tipo de dato para los indicadores clave de rendimiento (KPIs)
interface KpiData {
  successRate: number; // Indicador 3: % de Éxito
  lateRate: number;    // Indicador 4: % de Desvío
  activeProjects: number;
}

// Tipo de dato para la respuesta completa de la API
interface MetricsData {
  ongRankingData: OngRankingItem[];
  kpiData: KpiData;
}

// Propiedades del componente KpiCard
interface KpiCardProps {
  title: string;
  value: string | number;
  icon: JSX.Element;
  description: string;
  rate: number; // Tasa para determinar el color (para Indicadores 3 y 4)
}

// --- CONFIGURACIÓN DE DATOS SIMULADOS ---
const fetchMetrics = async (): Promise<{ data?: MetricsData, error?: string }> => {
  const token = localStorage.getItem('projectplanning_token')
  try {
    // Obtener métricas agregadas (sin project_id)
    const responses = await Promise.all([
      fetch('http://localhost:8000/api/v1/metrics/global/success_rate', {
        headers: { Authorization: `Bearer ${token}` },
      }),
      fetch('http://localhost:8000/api/v1/metrics/global/late_rate', {
        headers: { Authorization: `Bearer ${token}` },
      }),
      fetch('http://localhost:8000/api/v1/metrics/global/active_projects', {
        headers: { Authorization: `Bearer ${token}` },
      }),
      fetch('http://localhost:8000/api/v1/metrics/global/ong_ranking', {
        headers: { Authorization: `Bearer ${token}` },
      }),
    ])

    // Validar respuestas
    for (const res of responses) {
      if (!res.ok) {
        return { error: `HTTP ${res.status}` }
      }
    }

    const [successRes, lateRes, activeRes, rankingRes] = await Promise.all(
      responses.map(r => r.json())
    )

    const data: MetricsData = {
      kpiData: {
        successRate: successRes.successRate ?? 0,
        lateRate: lateRes.lateRate ?? 0,
        activeProjects: activeRes.count ?? 0,
      },
      ongRankingData: rankingRes.ranking ?? [],
    }
    
    return { data }
  } catch (error) {
    return { error: error instanceof Error ? error.message : 'Unknown error' }
  }
};

// --- COMPONENTE AUXILIAR (BASADO EN MUI) ---
const KpiCard: React.FC<KpiCardProps> = ({ title, value, icon, description, rate }) => {
  let color: 'success' | 'warning' | 'error' | 'primary' = 'primary';
  let iconColor: 'success' | 'warning' | 'error' | 'primary' = 'primary';

  // Lógica para Indicadores 3 y 4 (Éxito y Desvío)
  if (title.includes('% Proyectos Éxito')) {
    if (rate >= 75) { iconColor = 'success'; }
    else if (rate >= 50) { iconColor = 'warning'; }
    else { iconColor = 'error'; }
  } else if (title.includes('% Proyectos Fuera')) {
    if (rate < 25) { iconColor = 'success'; }
    else if (rate < 50) { iconColor = 'warning'; }
    else { iconColor = 'error'; }
  } else if (title.includes('Activos')) {
    iconColor = 'warning';
  } else {
    iconColor = 'primary';
  }

  const IconComponent = React.cloneElement(icon, { color: iconColor, sx: { fontSize: 30 } });

  return (
    <Paper elevation={4} sx={{ p: 3, borderLeft: 5, borderColor: `${iconColor}.main`, height: '100%' }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="overline" color="text.secondary" noWrap>
          {title}
        </Typography>
        {IconComponent}
      </Box>
      <Typography variant="h4" component="div" sx={{ fontWeight: 700, mb: 0.5 }}>
        {value}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {description}
      </Typography>
    </Paper>
  );
};

// --- COMPONENTE PRINCIPAL (BASADO EN MUI) ---
const MetricsDashboard: React.FC = () => {
  const [data, setData] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      const result = await fetchMetrics();
      
      if (result.error) {
        setError(result.error);
        setData(null);
      } else if (result.data) {
        setData(result.data);
      }
      setLoading(false);
    };

    loadData();
  }, []);

  // Vista de Error
  if (error) {
    return (
      <Container maxWidth="sm" sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '80vh', p: 4 }}>
        <Paper elevation={6} sx={{ p: 5, textAlign: 'center', borderTop: 8, borderColor: 'error.main' }}>
          <LockIcon color="error" sx={{ fontSize: 60, mb: 2 }} />
          <Typography variant="h5" gutterBottom>Error al Cargar Métricas</Typography>
          <Typography color="text.secondary" mb={3}>{error}</Typography>
        </Paper>
      </Container>
    );
  }

  // Vista de Carga
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '70vh', flexDirection: 'column' }}>
        <CircularProgress color="primary" size={50} />
        <Typography variant="h6" sx={{ mt: 2, color: 'primary.main' }}>
          Cargando Tablero de Gerencia...
        </Typography>
      </Box>
    );
  }

  if (!data) return null; 

  // Vista del Tablero
  return (
    <Box sx={{ flexGrow: 1, py: 4 }}>
      <Container maxWidth="lg">
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600, mb: 4, display: 'flex', alignItems: 'center' }}>
          <BarChart3Icon color="primary" sx={{ mr: 1, fontSize: 32 }} />
          Tablero de Control Gerencial
        </Typography>

        {/* TARJETAS DE INDICADORES (KPIs) */}
        <Grid container spacing={4} mb={4}>
          
          {/* Indicador 3: Éxito en Ejecución y Plazo */}
          <Grid item xs={12} sm={6} md={3}>
            <KpiCard
              title="% Proyectos Éxito/Plazo"
              value={`${data.kpiData.successRate}%`}
              rate={data.kpiData.successRate}
              icon={<CheckCircleIcon />}
              description="Casos que finalizan exitosamente y en término."
            />
          </Grid>

          {/* Indicador 4: Desvío del Plazo */}
          <Grid item xs={12} sm={6} md={3}>
            <KpiCard
              title="% Proyectos Fuera de Plazo"
              value={`${data.kpiData.lateRate}%`}
              rate={data.kpiData.lateRate}
              icon={<AlertTriangleIcon />}
              description="Casos que terminan fuera del cronograma original."
            />
          </Grid>

          {/* Métrica de ejemplo: Proyectos Activos */}
          <Grid item xs={12} sm={6} md={3}>
            <KpiCard
              title="Proyectos Activos"
              value={data.kpiData.activeProjects}
              rate={0}
              icon={<ListIcon />}
              description="Procesos de Proyecto en estado 'En Ejecución'."
            />
          </Grid>

          {/* Métrica de ejemplo: Tasa de Compromiso */}
          <Grid item xs={12} sm={6} md={3}>
            <KpiCard
              title="Compromiso Cumplido"
              value="92%"
              rate={92}
              icon={<TrendingUpIcon />}
              description="Compromisos marcados como 'Commit & Complete'."
            />
          </Grid>
        </Grid>

        {/* GRÁFICO PRINCIPAL: Indicador 1 */}
        <Grid container spacing={4}>
          <Grid item xs={12} lg={8}>
            <Paper elevation={4} sx={{ p: 3, height: 450 }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <UsersIcon color="primary" sx={{ mr: 1 }} />
                Indicador 1: Top ONGs Colaboradoras
              </Typography>
              <Typography variant="body2" color="text.secondary" mb={2}>
                ONGs con la mayor cantidad de actividades de colaboración ejecutadas.
              </Typography>
              <Box sx={{ height: 320 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data.ongRankingData}
                    layout="vertical"
                    margin={{ top: 10, right: 30, left: 100, bottom: 10 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="ong_name" width={100} />
                    <Tooltip 
                      cursor={{ fill: 'rgba(63, 81, 181, 0.1)' }} 
                      formatter={(value: any) => [`${value} Colaboraciones`, 'Total Ejecutadas']} 
                    />
                    <Bar dataKey="colaboraciones" fill="#3f51b5" radius={[4, 4, 0, 0]} name="Colaboraciones Ejecutadas" />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </Paper>
          </Grid>
        </Grid>

        {/* Pie de página */}
        <Box component="footer" py={3} textAlign="center" mt={4}>
          <Typography variant="body2" color="text.secondary">
            Datos sincronizados con la Base de Datos (PostgreSQL) y Bonita BPM.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default MetricsDashboard;