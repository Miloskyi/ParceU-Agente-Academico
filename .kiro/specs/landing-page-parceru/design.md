# Documento de Diseño Técnico — Landing Page ParcerU

## Overview

La _Landing Page_ de ParcerU es una pantalla de bienvenida que se muestra al estudiante de la UdeA **antes** de que acceda a la interfaz principal del copiloto administrativo. Su propósito es comunicar qué es ParcerU, qué puede consultarse, cómo funciona y motivar al usuario a empezar. Se implementa como un único componente React (`LandingPage.jsx`) sin dependencias adicionales, controlado por un `useState` en `App.jsx`.

---

## Architecture

### Modelo de estado en `App.jsx`

El control de visibilidad se centra en un único estado local de React:

```
view: "landing" | "app"
```

- Valor inicial: `"landing"` → se muestra `<LandingPage />`  
- Tras invocar `onEnter`: `"app"` → se muestra la interfaz de pestañas existente

No se utiliza `react-router-dom` ni ninguna otra librería de enrutamiento.

```jsx
// App.jsx (después de la integración)
const [view, setView] = useState('landing')

if (view === 'landing') {
  return <LandingPage onEnter={() => setView('app')} />
}

// … resto del layout con Sidebar + pestañas
```

### Árbol de componentes

```
App
├── LandingPage (view === "landing")
│   ├── HeroSection
│   ├── FuncionalidadesSection
│   ├── ComoFuncionaSection
│   ├── ConsultasSection
│   ├── CTAFinalSection
│   └── FooterSection
└── [Layout principal] (view === "app")
    ├── Sidebar
    └── main > {ChatTab | TramitesTab | CalendarioTab | AnalyticsTab}
```

Cada sección se implementa como **sub-componente interno** (función declarada dentro del mismo archivo `LandingPage.jsx`) o como JSX inline en la función principal, según su complejidad. No se crean archivos separados.

### Flujo de navegación

```
Carga inicial
     │
     ▼
 view = "landing"
 → <LandingPage onEnter={fn} />
     │
     │  usuario hace clic en CTA (Hero o CTAFinal)
     │  → onEnter?.()
     ▼
 view = "app"
 → <Layout principal>
```

La transición ocurre en < 300 ms (cambio de estado de React, sin animación de salida costosa).

---

## Components and Interfaces

### `LandingPage`

| Prop | Tipo | Descripción |
|------|------|-------------|
| `onEnter` | `() => void` (opcional) | Callback que notifica a `App` que el usuario quiere ingresar. Si no se provee, los CTAs la invocan con `onEnter?.()` para evitar errores en tiempo de ejecución. |

**Responsabilidades:**
- Renderizar las 6 secciones en orden vertical.
- Exponer el callback `onEnter` a los dos CTAs (Hero y CTAFinal).
- Calcular el año actual una sola vez y pasarlo al Footer.

### Sub-componentes internos

| Componente | Propósito |
|------------|-----------|
| `HeroSection` | Logotipo, `<h1>`, tagline y CTA primario "Empezar ahora" |
| `FuncionalidadesSection` | Grilla de 4 tarjetas con ícono, título y descripción |
| `ComoFuncionaSection` | 3 pasos numerados + aviso orientativo |
| `ConsultasSection` | Grilla de categorías temáticas con ejemplos de preguntas |
| `CTAFinalSection` | Segundo CTA "Ingresar a ParcerU" |
| `FooterSection` | Afiliación institucional, aviso legal y año dinámico |

### Paleta de colores y tokens Tailwind por sección

| Sección | Fondo | Texto principal | Acento | Detalle |
|---------|-------|-----------------|--------|---------|
| **Hero** | `bg-udea-petroleo` + gradiente a `udea-oscuro` | `text-white` | `text-udea-verde` | Botón CTA: `bg-udea-turquesa hover:bg-udea-oscuro` |
| **Funcionalidades** | `bg-udea-gris` | `text-udea-oscuro` | Tarjetas: `bg-white border-udea-gris2` | Íconos: `text-udea-turquesa` |
| **Cómo Funciona** | `bg-white` | `text-udea-oscuro` | Números de paso: `text-udea-turquesa font-bold` | Aviso: `bg-udea-gris text-udea-petroleo` |
| **Consultas** | `bg-udea-gris` | `text-udea-oscuro` | Cabeceras de categoría: `text-udea-petroleo` | Íconos: `text-udea-turquesa` |
| **CTAFinal** | `bg-udea-petroleo` | `text-white` | Botón: `bg-udea-verde text-udea-oscuro` | — |
| **Footer** | `bg-udea-oscuro` (`#004548`) | `text-white/70` | `text-udea-verde` | Borde superior: `border-t-2 border-udea-turquesa` |

El gradiente del Hero replica el patrón del Sidebar para coherencia visual:

```css
background: linear-gradient(180deg, #006065 0%, #004548 100%);
```

### Responsive breakpoints

Se usa el sistema de breakpoints de Tailwind (mobile-first):

| Breakpoint | Ancho mínimo | Comportamiento |
|------------|-------------|----------------|
| default | 0px | Columna única, padding `px-4` |
| `sm` | 640px | Ajustes de tipografía (logo más grande, h1 más grande) |
| `md` | 768px | Grilla de 2+ columnas en Funcionalidades y Consultas |
| `lg` | 1024px | Grilla de 4 columnas en Funcionalidades, 3 en Consultas |

#### Grilla `FuncionalidadesSection`

```
< 640px  → grid-cols-1
≥ 640px  → grid-cols-2
≥ 1024px → grid-cols-4
```

#### Grilla `ConsultasSection`

```
< 768px  → grid-cols-1
≥ 768px  → grid-cols-2
≥ 1024px → grid-cols-3
```

#### `HeroSection`

- Siempre ocupa `min-h-screen` para asegurar visibilidad completa sin scroll.
- Mobile: logo `w-32`, `<h1>` con `text-4xl`, tagline `text-base`.
- Desktop (`md+`): logo `w-48`, `<h1>` con `text-6xl`, tagline `text-xl`.

---

## Data Models

Los datos estáticos se declaran como **constantes de módulo** al inicio de `LandingPage.jsx`, antes de la función principal. Esto los hace legibles y editables sin tocar el JSX.

### `DATA_FUNCIONALIDADES`

```js
// 4 tarjetas exactas, en este orden
const DATA_FUNCIONALIDADES = [
  {
    icon: MessageCircle,   // lucide-react
    titulo: 'Consulta de trámites',
    descripcion: 'Conoce los pasos y requisitos de los trámites académicos más frecuentes.',
  },
  {
    icon: Calendar,
    titulo: 'Calendario académico',
    descripcion: 'Consulta fechas clave de matrículas, exámenes y eventos del semestre.',
  },
  {
    icon: BookOpen,
    titulo: 'Reglamento estudiantil',
    descripcion: 'Resuelve dudas sobre derechos, deberes y normativas de la UdeA.',
  },
  {
    icon: BarChart3,
    titulo: 'Analíticas de uso',
    descripcion: 'Visualiza las preguntas más frecuentes y tendencias de consulta.',
  },
]
```

### `DATA_PASOS`

```js
// Exactamente 3 pasos, numerados del 1 al 3
const DATA_PASOS = [
  {
    numero: 1,
    titulo: 'Escribe tu pregunta',                             // <= 60 chars
    descripcion: 'Redácta en lenguaje natural lo que necesitas saber sobre tu vida académica.',  // <= 120 chars
  },
  {
    numero: 2,
    titulo: 'ParcerU consulta los documentos',
    descripcion: 'El sistema busca en los documentos oficiales de la UdeA la información más relevante.',
  },
  {
    numero: 3,
    titulo: 'Recibe una respuesta orientativa',
    descripcion: 'Obtienes la respuesta con la fuente del documento institucional como referencia.',
  },
]
```

**Invariantes de `DATA_PASOS`:**
- Longitud exacta: 3
- Para todo paso: `titulo.length <= 60` y `descripcion.length <= 120`
- Números de orden: `[1, 2, 3]` en orden ascendente

### `DATA_CATEGORIAS`

```js
// >= 4 categorías; cada una con 3–6 ejemplos
const DATA_CATEGORIAS = [
  {
    nombre: 'Reglamento Estudiantil',
    icon: BookOpen,
    ejemplos: [
      'Mínimo de créditos para conservar el cupo',
      'Causales de cancelación de matrícula',
      'Proceso de apelación de notas',
      'Normas sobre monitorías académicas',
    ],
  },
  {
    nombre: 'Trámites y Procedimientos',
    icon: ClipboardList,
    ejemplos: [
      'Liquidación y pago de matrícula',
      'Matrícula de estudiantes en intercambio',
      'Solicitud de certificados y constancias',
      'Trámites para estudiantes indígenas y NARP',
    ],
  },
  {
    nombre: 'Calendario Académico',
    icon: Calendar,
    ejemplos: [
      'Fechas de inicio y cierre del semestre',
      'Periodos de adición y cancelación de materias',
      'Semana de exámenes finales',
      'Días festivos y vacaciones institucionales',
    ],
  },
  {
    nombre: 'Bienestar Universitario',
    icon: Heart,
    ejemplos: [
      'Servicios del Sistema de Bienestar UdeA',
      'Beneficios de alimentación y transporte',
      'Apoyos económicos y becas disponibles',
      'Actividades culturales y deportivas',
    ],
  },
  {
    nombre: 'Admisiones',
    icon: Users,
    ejemplos: [
      'Proceso de admisión para aspirantes nuevos',
      'Exentos de pago de derechos de matrícula',
      'Guía para aspirantes con pruebas especiales',
      'Requisitos para programas de arte y música',
    ],
  },
]
```

**Invariantes de `DATA_CATEGORIAS`:**
- Longitud: `>= 4`
- Para toda categoría: `3 <= ejemplos.length <= 6`

---

## Correctness Properties

*Una propiedad es una característica o comportamiento que debe mantenerse verdadero en todas las ejecuciones válidas del sistema — esencialmente, un enunciado formal sobre lo que el software debe hacer. Las propiedades sirven de puente entre las especificaciones legibles por humanos y las garantías de corrección verificables automáticamente.*

### Property 1: Las tarjetas de funcionalidades renderizan todos sus datos

*Para cualquier* array de objetos funcionalidad de longitud n (con campos `icon`, `titulo` y `descripcion`), el componente `FuncionalidadesSection` debe renderizar exactamente n tarjetas, cada una con un título y una descripción no vacíos.

**Validates: Requirements 3.1**

---

### Property 2: El orden de los pasos se preserva en el renderizado

*Para cualquier* array de pasos con numeración secuencial ascendente, el componente `ComoFuncionaSection` debe renderizarlos en el mismo orden de entrada, sin inversión ni reordenamiento.

**Validates: Requirements 4.1**

---

### Property 3: Invariante de longitud en los datos de pasos

*Para cualquier* paso en `DATA_PASOS`, su campo `titulo` debe tener como máximo 60 caracteres y su campo `descripcion` como máximo 120 caracteres.

**Validates: Requirements 4.2**

---

### Property 4: Las categorías de consultas siempre tienen entre 3 y 6 ejemplos

*Para cualquier* categoría en `DATA_CATEGORIAS`, el número de ejemplos de preguntas debe satisfacer `3 ≤ ejemplos.length ≤ 6`.

**Validates: Requirements 5.3**

---

### Property 5: Todos los CTAs invocan `onEnter` exactamente una vez por clic

*Para cualquier* CTA presente en `LandingPage` (CTA primario del Hero y CTA final), al hacer clic una sola vez sobre él, la función `onEnter` debe ser invocada exactamente una vez.

**Validates: Requirements 1.4, 6.2, 8.4**

---

### Property 6: El año del Footer refleja siempre el año en curso

*Para cualquier* instante de renderizado del componente, el texto visible del año en `FooterSection` debe ser igual al valor devuelto por `new Date().getFullYear()` en ese mismo instante.

**Validates: Requirements 7.4**

---

## Error Handling

### `onEnter` no provista

Se usa optional chaining (`onEnter?.()`) en todos los manejadores de clic de CTAs. Si la prop no se pasa, la invocación se omite silenciosamente y no se lanza ningún error en tiempo de ejecución. Cubre el uso de la vista previa aislada del componente (Requisito 8.5).

### Datos estáticos vacíos o no disponibles

Los datos (`DATA_FUNCIONALIDADES`, `DATA_PASOS`, `DATA_CATEGORIAS`) son constantes del módulo — no hay llamada asíncrona. Sin embargo, para cumplir el Requisito 5.5, `ConsultasSection` incluye una verificación defensiva:

```jsx
if (!DATA_CATEGORIAS || DATA_CATEGORIAS.length === 0) {
  return (
    <p className="text-red-600 text-center py-8">
      No se pudieron cargar los temas de consulta. Por favor recarga la página.
    </p>
  )
}
```

### Imagen del logotipo no disponible

Si `/parceru.png` no existe, el navegador muestra el texto del atributo `alt="Logo ParcerU"` de forma nativa. No se requiere lógica adicional de fallback dado que el asset forma parte del build del proyecto (`frontend/public/parceru.png`).

### Accesibilidad

- Todos los `<button>` son focusables por teclado de forma nativa; incluyen `type="button"` explícito.
- El CTA primario y secundario son alcanzables mediante `Tab` y activables con `Enter` / `Espacio` (Requisito 2.6).
- El logotipo incluye `alt="Logo ParcerU"` (Requisito 2.1).
- Contraste texto blanco (`#ffffff`) sobre fondo `#006065`: ratio ≈ 4.8:1 — cumple WCAG AA.
- Contraste texto `#004548` sobre `#F4F8F7`: ratio ≈ 9.1:1 — cumple WCAG AAA.

---

## Testing Strategy

### Enfoque dual

Se combinan pruebas de ejemplo (unit tests) con pruebas basadas en propiedades (PBT) para lograr cobertura comprehensiva.

**Librería PBT:** [fast-check](https://fast-check.dev/) — compatible con Vitest sin configuración adicional.  
> Única dependencia de desarrollo a agregar: `fast-check`. No agrega dependencias de producción.

Cada propiedad se implementa con **mínimo 100 iteraciones**. Cada test PBT incluye el comentario:
```
// Feature: landing-page-parceru, Propiedad N: <texto de la propiedad>
```

### Pruebas de ejemplo (Vitest + React Testing Library)

Cubren comportamientos concretos y condiciones de borde que no requieren PBT:

| Test | Requisito validado |
|------|--------------------|
| `LandingPage` renderiza sin errores con `onEnter` | Req. 8.3 |
| CTA primario ("Empezar ahora") llama `onEnter` al hacer clic | Req. 2.4, 1.4 |
| Segundo CTA llama `onEnter` al hacer clic | Req. 6.2 |
| `LandingPage` sin `onEnter` no lanza error al hacer clic en CTAs | Req. 8.5 |
| `<h1>` contiene el texto "ParcerU" | Req. 2.2 |
| Tagline contiene "copiloto" y "Universidad de Antioquia" | Req. 2.3 |
| Imagen del logo tiene `alt="Logo ParcerU"` | Req. 2.1 |
| CTA primario tiene texto exacto "Empezar ahora" | Req. 2.4 |
| Segundo CTA no tiene el texto "Empezar ahora" | Req. 6.3 |
| Footer contiene "Universidad de Antioquia — Facultad de Ingeniería" | Req. 7.1 |
| Footer contiene aviso orientativo completo | Req. 7.2 |
| `ConsultasSection` renderiza las 4 categorías mínimas requeridas | Req. 5.2 |
| `ConsultasSection` muestra texto de fuentes oficiales de la UdeA | Req. 5.4 |
| `ConsultasSection` con datos vacíos muestra mensaje de error legible | Req. 5.5 |
| Los 3 pasos del flujo están presentes y describen el proceso correcto | Req. 4.3 |
| Aviso orientativo de `ComoFuncionaSection` está visible sin interacción | Req. 4.4 |
| Estado inicial de `App` es `"landing"` | Req. 8.2 |
| `App` cambia a `"app"` cuando `onEnter` se invoca | Req. 8.4 |

### Pruebas basadas en propiedades (fast-check, ≥ 100 iteraciones)

| Propiedad | Estrategia de generación |
|-----------|--------------------------|
| **Propiedad 1** — Tarjetas renderizan todos los datos | Generar array de n objetos `{icon: fc.constant(MessageCircle), titulo: fc.string({minLength: 1}), descripcion: fc.string({minLength: 1})}` con `fc.array(..., {minLength: 1, maxLength: 10})`. Renderizar `FuncionalidadesSection` y verificar que hay exactamente n tarjetas con título y descripción no vacíos. |
| **Propiedad 2** — Orden de pasos preservado | Generar permutaciones del array `[1,2,3]` con `fc.shuffledSubarray([1,2,3], {minLength: 3})`. Ordenar el input ascendentemente, renderizar `ComoFuncionaSection` y verificar que los números de paso siguen el mismo orden. |
| **Propiedad 3** — Invariante de longitud en pasos | Iterar sobre `DATA_PASOS` (datos estáticos reales) y para cada paso afirmar `titulo.length <= 60 && descripcion.length <= 120`. |
| **Propiedad 4** — Ejemplos por categoría entre 3 y 6 | Generar categorías con `fc.record({nombre: fc.string(), ejemplos: fc.array(fc.string(), {minLength: 3, maxLength: 6})})`. Renderizar `ConsultasSection` y verificar que se renderizan entre 3 y 6 elementos por categoría. |
| **Propiedad 5** — CTAs invocan `onEnter` exactamente una vez | Para cada CTA identificado por su texto (generado con `fc.constantFrom('Empezar ahora', 'Ingresar a ParcerU')`), simular clic y verificar que el mock de `onEnter` fue llamado `toHaveBeenCalledTimes(1)`. |
| **Propiedad 6** — Año del Footer siempre correcto | Generar años con `fc.integer({min: 2024, max: 2099})`. Mockear `Date` con el año generado y verificar que `FooterSection` muestra ese año en su texto visible. |

### Pruebas de humo

- El archivo `frontend/src/components/LandingPage.jsx` existe y exporta un componente React por defecto.
- Los imports de `LandingPage.jsx` no incluyen paquetes fuera de `package.json`.
- El estado inicial de `App` es `"landing"` (verificado con `useState` mock o inspección del estado inicial).
