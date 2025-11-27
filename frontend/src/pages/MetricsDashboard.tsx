import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import {
  Typography,
  Box,
  Container,
  Grid,
  Paper,
  CircularProgress,
} from '@mui/material';
import {
  Group as UsersIcon,
  AccessTime as ClockIcon,
  Warning as AlertTriangleIcon,
  Lock as LockIcon,
  CheckCircle as CheckCircleIcon,
  BarChart as BarChart3Icon,
} from '@mui/icons-material';
import { useRoleAccess } from '../hooks/useRoleAccess';
import { Navigate } from 'react-router-dom';

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
  total_active: number;
  on_time: number;
  delayed: number;
}

interface DemandSupplyItem {
  support_type: string
  total_requests: number
  approved_requests: number
  top_3_ongs: { ong_name: string; commitments: number }[]
}

// Tipo de dato para la respuesta completa de la API
interface MetricsData {
  kpiData: KpiData;
  ongRankingData: OngRankingItem[];
  demandSupply: DemandSupplyItem[];
}

// Propiedades del componente KpiCard
interface KpiCardProps {
  title: string;
  value: string | number;
  icon: JSX.Element;
  description: string;
  rate: number; // Tasa para determinar el color (para Indicadores 3 y 4)
}

const API_BASE = 'http://localhost:8000/api/v1/metrics'

const fetchMetrics = async (): Promise<{ data?: MetricsData, error?: string }> => {
  const token = localStorage.getItem('projectplanning_token')
  try {
    // Un único endpoint que devuelve successRate y lateRate
    const [successRes, rankingRes, demandRes] = await Promise.all([
      fetch(`${API_BASE}/global/success_rate`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
      fetch(`${API_BASE}/global/ong_ranking`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
      fetch(`${API_BASE}/global/demand_supply`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    ])

    for (const res of [successRes, rankingRes, demandRes]) {
      if (!res.ok) return { error: `HTTP ${res.status}` }
    }

    const [success, rank, demand] = await Promise.all(
      [successRes, rankingRes, demandRes].map(r => r.json())
    )

    const data: MetricsData = {
      kpiData: {
        successRate: success.successRate ?? 0,
        lateRate: success.lateRate ?? 0,
        total_active: success.total_active ?? 0,
        on_time: success.on_time ?? 0,
        delayed: success.delayed ?? 0,
      },
      ongRankingData: rank.ranking ?? [],
      demandSupply: demand.demand_supply ?? [],
    }

    return { data }
  } catch (error) {
    return { error: error instanceof Error ? error.message : 'Unknown error' }
  }
};

// --- COMPONENTE AUXILIAR (BASADO EN MUI) ---
const KpiCard: React.FC<KpiCardProps> = ({ title, value, icon, description, rate }) => {
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
  const { hasRole } = useRoleAccess()
  
  if (!hasRole('Gerente')) {
    return <Navigate to="/projects" replace />
  }

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
              description={`${data.kpiData.on_time} de ${data.kpiData.total_active} casos activos en término`}
            />
          </Grid>

          {/* Indicador 4: Desvío del Plazo */}
          <Grid item xs={12} sm={6} md={3}>
            <KpiCard
              title="% Proyectos Fuera de Plazo"
              value={`${data.kpiData.lateRate}%`}
              rate={data.kpiData.lateRate}
              icon={<AlertTriangleIcon />}
              description={`${data.kpiData.delayed} de ${data.kpiData.total_active} casos activos demorados`}
            />
          </Grid>
          
        </Grid>

        {/* GRÁFICOS Y MÉTRICAS */}
        <Grid container spacing={4}>
          {/* Indicador 1: Top ONGs Colaboradoras */}
          <Grid item xs={12} lg={8}>
            <Paper elevation={4} sx={{ p: 3, height: 450 }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <UsersIcon color="primary" sx={{ mr: 1 }} />
                Top ONGs Colaboradoras
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

          {/* Indicador 2: Demanda y Oferta */}
          <Grid item xs={12} lg={4}>
            {data?.demandSupply && data.demandSupply.length > 0 ? (
              // Una única tarjeta Paper que contendrá toda la lista
              <Paper elevation={4} sx={{ p: 3, height: '100%' }}>
                
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, borderBottom: 1, borderColor: 'divider', pb: 1, mb: 2 }}>
                  Rubro Más Solicitado / Top ONGs que lo proveen
                </Typography>

                {/* Iteración sobre cada rubro solicitado */}
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  {data.demandSupply.map((item) => (
                    <Box key={item.support_type}>
                      {/* Título del Rubro y Solicitud/Aprobación */}
                      <Typography variant="body1" sx={{ fontWeight: 600, mb: 0.5 }}>
                        {getSupportTypeLabel(item.support_type)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" mb={1}>
                        Solicitado: {item.total_requests} | Aprobados: {item.approved_requests}
                      </Typography>
                      
                      {/* Listado de Top ONGs Contribuyentes */}
                      <Box component="ol" sx={{ pl: 2, m: 0 }}>
                        {item.top_3_ongs.map((ong, idx) => (
                          <Typography component="li" key={ong.ong_name} variant="body2" sx={{ ml: 1, color: 'text.primary' }}>
                            {ong.ong_name} - {ong.commitments}
                          </Typography>
                        ))}
                      </Box>
                    </Box>
                  ))}
                </Box>
              </Paper>
            ) : (
              // Mensaje si no hay datos de demanda/oferta
              <Paper elevation={4} sx={{ p: 3, textAlign: 'center', height: '100%' }}>
                <Typography color="text.secondary">Sin datos de demanda/oferta</Typography>
              </Paper>
            )}
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

const SUPPORT_TYPE_LABELS: Record<string, string> = {
  financial: 'Financiamiento',
  materials: 'Materiales',
  labor: 'Mano de obra',
  logistics: 'Logística',
  other: 'Otro',
};

const getSupportTypeLabel = (key: string): string => {
  return SUPPORT_TYPE_LABELS[key] || key;
};

export default MetricsDashboard;