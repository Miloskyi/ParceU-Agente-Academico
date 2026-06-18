/**
 * Base URL para todas las llamadas al backend.
 *
 * - En desarrollo (npm run dev): Vite proxy redirige /api → localhost:8000
 * - En producción (Vercel): VITE_API_URL apunta al backend de Railway,
 *   p.ej. https://parceru-backend.up.railway.app
 */
const API_BASE = import.meta.env.VITE_API_URL ?? ''

export default API_BASE
