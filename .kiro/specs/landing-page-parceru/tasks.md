# Implementation Plan: Landing Page ParcerU

## Overview

Implementar la Landing Page de ParcerU como un componente React auto-contenido (`LandingPage.jsx`), integrado en `App.jsx` mediante un estado local `view`, sin dependencias externas adicionales de producción. Las pruebas se escriben con Vitest + React Testing Library y fast-check para las propiedades.

---

## Tasks

- [x] 1. Crear el componente `LandingPage.jsx` con datos estáticos y secciones
  - [x] 1.1 Declarar las constantes de datos estáticos en `frontend/src/components/LandingPage.jsx`
    - Declarar `DATA_FUNCIONALIDADES` (4 elementos) con campos `icon`, `titulo` y `descripcion` usando íconos de `lucide-react` (`MessageCircle`, `Calendar`, `BookOpen`, `BarChart3`)
    - Declarar `DATA_PASOS` (3 elementos) con campos `numero`, `titulo` (≤ 60 caracteres) y `descripcion` (≤ 120 caracteres)
    - Declarar `DATA_CATEGORIAS` (≥ 4 elementos) con campos `nombre`, `icon` y `ejemplos` (3–6 por categoría), cubriendo: Reglamento Estudiantil, Trámites y Procedimientos, Calendario Académico, Bienestar Universitario y Admisiones
    - _Requisitos: 3.1, 3.2, 4.1, 4.2, 5.1, 5.2, 5.3_

  - [x] 1.2 Implementar `HeroSection` dentro de `LandingPage.jsx`
    - Renderizar `<img src="/parceru.png" alt="Logo ParcerU" />` con tamaño responsive (`w-32 sm:w-48`)
    - Renderizar `<h1>` con el texto "ParcerU"
    - Renderizar tagline que contenga los términos "copiloto" y "Universidad de Antioquia"
    - Renderizar `<button type="button">` con texto exacto "Empezar ahora" que invoque `onEnter?.()`
    - Aplicar fondo con gradiente `linear-gradient(180deg, #006065 0%, #004548 100%)`, texto blanco y `min-h-screen`
    - Asegurar que el botón CTA es focusable mediante teclado (`Tab`, `Enter`, `Espacio`)
    - _Requisitos: 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 1.3 Implementar `FuncionalidadesSection` dentro de `LandingPage.jsx`
    - Iterar sobre `DATA_FUNCIONALIDADES` para renderizar 4 tarjetas con ícono, título y descripción
    - Aplicar grilla responsive: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`
    - Usar `bg-udea-gris` como fondo de sección, tarjetas `bg-white border-udea-gris2`, íconos `text-udea-turquesa`
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 1.4 Implementar `ComoFuncionaSection` dentro de `LandingPage.jsx`
    - Iterar sobre `DATA_PASOS` para renderizar 3 pasos, mostrando número de orden, título y descripción en el mismo bloque visual
    - Incluir aviso visible sin interacción con el texto "Las respuestas son orientativas. Consulta las oficinas para decisiones definitivas."
    - Aplicar números de paso con `text-udea-turquesa font-bold` y fondo `bg-white`
    - _Requisitos: 4.1, 4.2, 4.3, 4.4_

  - [x] 1.5 Implementar `ConsultasSection` dentro de `LandingPage.jsx`
    - Iterar sobre `DATA_CATEGORIAS` para renderizar tarjetas con `nombre`, ícono y lista de `ejemplos`
    - Incluir texto visible que indique "documentos oficiales de la Universidad de Antioquia"
    - Agregar verificación defensiva: si `DATA_CATEGORIAS` está vacío, renderizar mensaje de error legible
    - Aplicar grilla responsive: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 1.6 Implementar `CTAFinalSection` dentro de `LandingPage.jsx`
    - Renderizar `<button type="button">` con texto "Ingresar a ParcerU" que invoque `onEnter?.()`
    - Posicionar la sección después de `ConsultasSection` y antes de `FooterSection`
    - Aplicar fondo `bg-udea-petroleo`, botón `bg-udea-verde text-udea-oscuro`
    - _Requisitos: 6.1, 6.2, 6.3_

  - [x] 1.7 Implementar `FooterSection` dentro de `LandingPage.jsx`
    - Mostrar "ParcerU" y "Universidad de Antioquia — Facultad de Ingeniería"
    - Mostrar aviso: "Herramienta orientativa. Las respuestas no reemplazan la orientación oficial de las dependencias universitarias."
    - Calcular el año dinámicamente con `new Date().getFullYear()` y mostrarlo en el texto del footer
    - Aplicar fondo `bg-udea-oscuro` (`#004548`), texto `text-white/70`, borde `border-t-2 border-udea-turquesa`
    - _Requisitos: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 1.8 Ensamblar el componente principal `LandingPage` y exportarlo por defecto
    - Recibir la prop `onEnter` (opcional) e inyectarla en `HeroSection` y `CTAFinalSection`
    - Calcular `new Date().getFullYear()` una sola vez en el cuerpo del componente y pasarlo al footer
    - Aplicar `w-full min-h-screen overflow-x-hidden` en el contenedor raíz para cumplir Req. 1.2 y 1.5
    - Todos los imports deben ser únicamente de `react` y `lucide-react` (ya en `package.json`)
    - _Requisitos: 1.2, 1.3, 1.5, 8.1, 8.3, 8.5, 8.6_

- [x] 2. Integrar `LandingPage` en `App.jsx`
  - [x] 2.1 Agregar estado `view` y renderizado condicional en `frontend/src/App.jsx`
    - Importar `LandingPage` desde `./components/LandingPage`
    - Añadir `const [view, setView] = useState('landing')` como primer estado del componente
    - Agregar bloque condicional: si `view === 'landing'` retornar `<LandingPage onEnter={() => setView('app')} />`
    - El resto del layout existente (Sidebar + main) permanece sin cambios y sólo se renderiza cuando `view === 'app'`
    - No agregar `react-router-dom` ni ninguna otra librería de enrutamiento
    - _Requisitos: 1.1, 1.4, 8.2, 8.3, 8.4_

- [x] 3. Checkpoint — verificar renderizado manual
  - Asegurarse de que `npm run dev` muestra la landing page al cargar, que el CTA "Empezar ahora" hace la transición a la app y que no hay errores en consola. Preguntar al usuario si tiene observaciones antes de continuar.

- [x] 4. Configurar entorno de pruebas
  - [x] 4.1 Instalar Vitest, React Testing Library y jsdom como devDependencies
    - Ejecutar: `npm install --save-dev vitest@1.6.0 @vitest/ui@1.6.0 jsdom@24.1.0 @testing-library/react@16.0.0 @testing-library/jest-dom@6.4.6 @testing-library/user-event@14.5.2`
    - _Requisitos: (infraestructura de pruebas)_

  - [x] 4.2 Instalar fast-check como devDependency
    - Ejecutar: `npm install --save-dev fast-check@3.20.0`
    - _Requisitos: (infraestructura de pruebas PBT)_

  - [x] 4.3 Crear el archivo de configuración `frontend/vite.config.js` (o actualizar el existente) con bloque `test`
    - Agregar al objeto de configuración de Vite:
      ```js
      test: {
        environment: 'jsdom',
        globals: true,
        setupFiles: './src/test/setup.js',
      }
      ```
    - Crear `frontend/src/test/setup.js` con el contenido `import '@testing-library/jest-dom'`
    - Agregar script `"test": "vitest --run"` en `package.json`
    - _Requisitos: (infraestructura de pruebas)_

- [x] 5. Escribir las 18 pruebas de ejemplo (unit tests)
  - [x] 5.1 Crear `frontend/src/test/LandingPage.test.jsx` con las pruebas de renderizado básico
    - Test: `LandingPage` renderiza sin errores con prop `onEnter`
    - Test: `<h1>` contiene el texto "ParcerU"
    - Test: tagline contiene "copiloto" y "Universidad de Antioquia"
    - Test: imagen del logo tiene `alt="Logo ParcerU"`
    - _Requisitos: 2.1, 2.2, 2.3, 8.3_

  - [x] 5.2 Agregar pruebas de CTAs y prop `onEnter` en `LandingPage.test.jsx`
    - Test: CTA primario ("Empezar ahora") tiene texto exacto "Empezar ahora"
    - Test: CTA primario llama `onEnter` al hacer clic
    - Test: segundo CTA llama `onEnter` al hacer clic
    - Test: segundo CTA no tiene el texto "Empezar ahora"
    - Test: `LandingPage` sin prop `onEnter` no lanza error al hacer clic en cualquier CTA
    - _Requisitos: 1.4, 2.4, 6.2, 6.3, 8.5_

  - [x] 5.3 Agregar pruebas de secciones de contenido en `LandingPage.test.jsx`
    - Test: footer contiene "Universidad de Antioquia — Facultad de Ingeniería"
    - Test: footer contiene aviso orientativo completo
    - Test: `ConsultasSection` renderiza las 4 categorías mínimas requeridas (Reglamento Estudiantil, Trámites y Procedimientos, Calendario Académico, Bienestar Universitario)
    - Test: `ConsultasSection` muestra texto de fuentes oficiales de la UdeA
    - Test: `ConsultasSection` con datos vacíos muestra mensaje de error legible
    - Test: los 3 pasos del flujo están presentes y describen el proceso correcto
    - Test: aviso orientativo de `ComoFuncionaSection` está visible sin interacción
    - _Requisitos: 4.3, 4.4, 5.2, 5.4, 5.5, 7.1, 7.2_

  - [x] 5.4 Crear `frontend/src/test/App.test.jsx` con pruebas de integración de estado
    - Test: estado inicial de `App` es `"landing"` (la landing page se renderiza)
    - Test: `App` cambia a `"app"` cuando `onEnter` se invoca (el CTA "Empezar ahora" oculta la landing)
    - _Requisitos: 8.2, 8.4_

- [x] 6. Checkpoint — ejecutar suite de pruebas de ejemplo
  - Ejecutar `npm test` y verificar que los 18 tests pasan. Corregir cualquier fallo antes de continuar.

- [x] 7. Escribir las 6 pruebas basadas en propiedades (PBT con fast-check)
  - [x]* 7.1 Escribir prueba PBT para la Propiedad 1 en `frontend/src/test/LandingPage.pbt.test.jsx`
    - **Propiedad 1: Las tarjetas de funcionalidades renderizan todos sus datos**
    - Generar array de n objetos `{ icon: fc.constant(MessageCircle), titulo: fc.string({minLength: 1}), descripcion: fc.string({minLength: 1}) }` con `fc.array(..., {minLength: 1, maxLength: 10})`
    - Renderizar `FuncionalidadesSection` con el array generado y verificar que hay exactamente n tarjetas con título y descripción no vacíos
    - Mínimo 100 iteraciones (`numRuns: 100`)
    - **Valida: Requisito 3.1**

  - [x]* 7.2 Agregar prueba PBT para la Propiedad 2 en `LandingPage.pbt.test.jsx`
    - **Propiedad 2: El orden de los pasos se preserva en el renderizado**
    - Generar permutaciones con `fc.shuffledSubarray([1, 2, 3], {minLength: 3})`, ordenar ascendentemente, renderizar `ComoFuncionaSection` y verificar que los números de paso aparecen en el mismo orden ascendente
    - Mínimo 100 iteraciones
    - **Valida: Requisito 4.1**

  - [x]* 7.3 Agregar prueba PBT para la Propiedad 3 en `LandingPage.pbt.test.jsx`
    - **Propiedad 3: Invariante de longitud en los datos de pasos**
    - Iterar sobre `DATA_PASOS` real con `fc.constant(DATA_PASOS)` y para cada paso afirmar `titulo.length <= 60` y `descripcion.length <= 120`
    - Mínimo 100 iteraciones
    - **Valida: Requisito 4.2**

  - [x]* 7.4 Agregar prueba PBT para la Propiedad 4 en `LandingPage.pbt.test.jsx`
    - **Propiedad 4: Las categorías de consultas siempre tienen entre 3 y 6 ejemplos**
    - Generar categorías con `fc.record({ nombre: fc.string(), icon: fc.constant(BookOpen), ejemplos: fc.array(fc.string({minLength: 1}), {minLength: 3, maxLength: 6}) })`
    - Renderizar `ConsultasSection` y verificar que cada categoría renderiza entre 3 y 6 ítems de ejemplo
    - Mínimo 100 iteraciones
    - **Valida: Requisito 5.3**

  - [x]* 7.5 Agregar prueba PBT para la Propiedad 5 en `LandingPage.pbt.test.jsx`
    - **Propiedad 5: Todos los CTAs invocan `onEnter` exactamente una vez por clic**
    - Para cada CTA identificado por su texto (`fc.constantFrom('Empezar ahora', 'Ingresar a ParcerU')`), crear mock de `onEnter`, simular un clic y verificar `expect(onEnter).toHaveBeenCalledTimes(1)`
    - Mínimo 100 iteraciones
    - **Valida: Requisitos 1.4, 6.2, 8.4**

  - [x]* 7.6 Agregar prueba PBT para la Propiedad 6 en `LandingPage.pbt.test.jsx`
    - **Propiedad 6: El año del Footer refleja siempre el año en curso**
    - Generar años con `fc.integer({min: 2024, max: 2099})`, mockear `Date` con el año generado y verificar que `FooterSection` muestra ese año en su texto visible
    - Mínimo 100 iteraciones
    - **Valida: Requisito 7.4**

- [x] 8. Checkpoint final — suite completa
  - Ejecutar `npm test` y verificar que los 18 tests de ejemplo y las 6 pruebas PBT pasan. Asegurarse de que no hay errores de lint ni de tipos. Preguntar al usuario si tiene comentarios finales.

---

## Notes

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido.
- Cada tarea referencia los requisitos específicos del documento `requirements.md` para trazabilidad.
- Los datos estáticos (`DATA_FUNCIONALIDADES`, `DATA_PASOS`, `DATA_CATEGORIAS`) son constantes de módulo — no hay llamadas asíncronas.
- El diseño usa únicamente `react` y `lucide-react` como dependencias de producción (ya en `package.json`).
- `fast-check` y las librerías de testing se instalan sólo como `devDependencies`.
- Las secciones son sub-componentes internos de `LandingPage.jsx`; no se crean archivos separados.
- La transición Landing → App ocurre en < 300 ms al ser un simple cambio de estado de React.

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4", "1.5", "1.6", "1.7"] },
    { "id": 2, "tasks": ["1.8"] },
    { "id": 3, "tasks": ["2.1"] },
    { "id": 4, "tasks": ["4.1", "4.2"] },
    { "id": 5, "tasks": ["4.3"] },
    { "id": 6, "tasks": ["5.1", "5.2", "5.3", "5.4"] },
    { "id": 7, "tasks": ["7.1", "7.2", "7.3", "7.4", "7.5", "7.6"] }
  ]
}
```
