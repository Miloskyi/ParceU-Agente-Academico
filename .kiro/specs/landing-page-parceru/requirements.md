# Requirements Document

## Introduction

ParcerU es un copiloto administrativo para estudiantes de la Universidad de Antioquia (UdeA). Actualmente, al abrir la aplicación el usuario entra directamente a la interfaz de pestañas (Chat IA, Trámites, Calendario Académico, Analytics) sin ninguna presentación del producto.

Esta feature agrega una **landing page** (página de bienvenida/presentación) que se muestra antes de que el usuario entre a la app principal. La landing page comunica qué es ParcerU, qué puede consultarse, cómo funciona y motiva al estudiante a empezar a usarlo.

---

## Glossary

- **Landing_Page**: Componente React de pantalla completa que sirve como página de presentación de ParcerU, visible antes de acceder a la app principal.
- **App_Principal**: La interfaz de pestañas existente (Chat, Trámites, Calendario, Analytics), accesible tras interactuar con la Landing_Page.
- **CTA** (Call To Action): Botón o elemento interactivo que invita al usuario a ingresar a la App_Principal.
- **Sección_Hero**: Sección principal visible sin hacer scroll, con el nombre del producto, tagline y el CTA primario.
- **Sección_Funcionalidades**: Sección que describe las capacidades principales de ParcerU mediante tarjetas visuales.
- **Sección_Como_Funciona**: Sección que explica el flujo de uso de ParcerU en pasos secuenciales.
- **Sección_Consultas**: Sección que enumera los temas y documentos sobre los que ParcerU puede responder preguntas.
- **Sección_Footer**: Sección inferior con información institucional, aviso de orientación y créditos.
- **Usuario**: Estudiante de la Universidad de Antioquia que accede a la aplicación.
- **Paleta_UdeA**: Colores institucionales de la UdeA usados en el proyecto: verde oscuro `#006065`, verde turquesa `#069A7E`, verde claro `#C5E1A5`, fondo gris `#F4F8F7`.

---

## Requirements

### Requirement 1: Mostrar la Landing Page al iniciar la aplicación

**User Story:** Como estudiante de la UdeA, quiero ver una página de presentación al abrir ParcerU, para entender de qué se trata la herramienta antes de empezar a usarla.

#### Acceptance Criteria

1. WHEN el Usuario carga la URL de la aplicación en el navegador, THE Landing_Page SHALL mostrarse como la vista inicial, antes que la App_Principal.
2. THE Landing_Page SHALL ocupar el 100% del ancho y el 100% de la altura del viewport (pantalla completa).
3. THE Landing_Page SHALL utilizar los colores institucionales de la Paleta_UdeA (`#006065`, `#069A7E`, `#C5E1A5`, `#F4F8F7`) de forma consistente con el resto de la aplicación.
4. WHEN el Usuario hace clic en el CTA (botón de llamada a la acción) de la Sección_Hero (sección principal de presentación), THE Landing_Page SHALL ocultarse y la App_Principal SHALL mostrarse en un máximo de 300ms, sin recargar la página.
5. WHEN el viewport tiene un ancho mínimo de 320px, THE Landing_Page SHALL mostrarse sin scroll horizontal, todos los elementos interactivos SHALL ser accesibles con un solo toque/clic, y todo el texto SHALL tener un tamaño mínimo de 14px.

---

### Requirement 2: Sección Hero con identidad de marca

**User Story:** Como estudiante, quiero ver claramente el nombre y propósito de ParcerU al llegar a la página, para saber de inmediato si es una herramienta útil para mí.

#### Acceptance Criteria

1. THE Sección_Hero SHALL mostrar el logotipo de ParcerU (`/parceru.png`) con el atributo `alt="Logo ParcerU"`.
2. THE Sección_Hero SHALL mostrar el nombre "ParcerU" como encabezado principal en un elemento `<h1>`.
3. THE Sección_Hero SHALL mostrar un tagline que contenga los términos "copiloto" y "Universidad de Antioquia" para describir el propósito de la herramienta.
4. THE Sección_Hero SHALL incluir un CTA con el texto exacto "Empezar ahora" que, al hacer clic, navegue al Usuario a la vista principal de chat de la App_Principal.
5. THE Sección_Hero SHALL ser completamente visible dentro de los primeros 100vh del viewport sin necesidad de hacer scroll.
6. IF el Usuario navega con teclado, THEN THE CTA SHALL ser alcanzable mediante la tecla Tab y activable mediante Enter o Espacio.

---

### Requirement 3: Sección de Funcionalidades principales

**User Story:** Como estudiante, quiero conocer rápidamente qué puede hacer ParcerU, para evaluar si me sirve antes de ingresar.

#### Acceptance Criteria

1. THE Sección_Funcionalidades SHALL mostrar exactamente 4 tarjetas, cada una con un ícono representativo, un título de máximo 5 palabras y una descripción de máximo 2 líneas de texto visible.
2. THE Sección_Funcionalidades SHALL cubrir las siguientes capacidades en sus tarjetas: consulta de trámites académicos, consulta del calendario académico, preguntas sobre el reglamento estudiantil, y resumen de analíticas de uso.
3. THE Sección_Funcionalidades SHALL usar íconos de la librería `lucide-react` ya instalada en el proyecto.
4. WHEN el viewport es menor a 768px de ancho, THE Sección_Funcionalidades SHALL mostrar las tarjetas en una columna única o en máximo 2 columnas.
5. WHEN el viewport es igual o mayor a 768px de ancho, THE Sección_Funcionalidades SHALL mostrar las tarjetas en una grilla de al menos 2 columnas.

---

### Requirement 4: Sección "¿Cómo funciona?"

**User Story:** Como estudiante, quiero entender el flujo de uso de ParcerU en pasos simples, para saber qué debo hacer al ingresar.

#### Acceptance Criteria

1. THE Sección_Como_Funciona SHALL mostrar el proceso de uso en exactamente 3 pasos numerados del 1 al 3 en orden ascendente.
2. THE Sección_Como_Funciona SHALL mostrar para cada paso un número de orden visible, un título de máximo 60 caracteres y una explicación de máximo 120 caracteres, todos ubicados en el mismo bloque visual del paso.
3. THE Sección_Como_Funciona SHALL describir el flujo: (1) el Usuario escribe una pregunta en lenguaje natural, (2) ParcerU consulta los documentos institucionales de la UdeA, (3) el Usuario recibe una respuesta orientativa que incluye el nombre del documento institucional como fuente.
4. THE Sección_Como_Funciona SHALL incluir un aviso legible sin interacción del usuario (sin hover, clic ni expansión) que indique que las respuestas son orientativas y que se debe consultar las oficinas para decisiones definitivas.

---

### Requirement 5: Sección de temas consultables

**User Story:** Como estudiante, quiero saber exactamente sobre qué temas puedo preguntarle a ParcerU, para saber si cubre mis necesidades académicas.

#### Acceptance Criteria

1. WHEN el Usuario carga la Landing_Page, THE Sección_Consultas SHALL listar los temas disponibles para consulta agrupados en al menos 4 categorías temáticas visibles.
2. THE Sección_Consultas SHALL incluir como mínimo las siguientes categorías: Reglamento Estudiantil, Trámites y Procedimientos, Calendario Académico y Bienestar Universitario.
3. THE Sección_Consultas SHALL mostrar entre 3 y 6 ejemplos de preguntas o temas consultables por categoría.
4. THE Sección_Consultas SHALL incluir un texto o etiqueta visible que indique que las fuentes provienen de documentos oficiales de la Universidad de Antioquia.
5. IF la sección no puede cargar su contenido, THEN THE Sección_Consultas SHALL mostrar un mensaje de error legible en lugar de un área vacía.

---

### Requirement 6: Segundo CTA al final de la página

**User Story:** Como estudiante que ha leído toda la landing page, quiero tener un botón para ingresar a la app sin tener que volver al inicio, para ahorrar tiempo.

#### Acceptance Criteria

1. THE Landing_Page SHALL incluir un segundo CTA ubicado después de la Sección_Consultas y antes de la Sección_Footer.
2. WHEN el Usuario hace clic en el segundo CTA, THE Landing_Page SHALL ocultarse y la App_Principal SHALL mostrarse en un máximo de 300ms, sin recargar la página, de la misma forma que el CTA primario de la Sección_Hero.
3. THE segundo CTA SHALL tener uno de los siguientes textos: "Ingresar a ParcerU", "Ir a la app" o "Acceder ahora", siendo diferente al texto "Empezar ahora" del CTA primario.

---

### Requirement 7: Sección Footer con información institucional

**User Story:** Como estudiante, quiero ver quién está detrás de ParcerU, para confiar en la herramienta.

#### Acceptance Criteria

1. THE Sección_Footer SHALL mostrar el texto "ParcerU" y la afiliación "Universidad de Antioquia — Facultad de Ingeniería".
2. THE Sección_Footer SHALL mostrar el aviso: "Herramienta orientativa. Las respuestas no reemplazan la orientación oficial de las dependencias universitarias."
3. THE Sección_Footer SHALL usar un color de fondo visualmente equivalente al color oscuro del Sidebar de la App_Principal.
4. THE Sección_Footer SHALL mostrar el año actual calendario en el momento de carga de la página, obtenido dinámicamente mediante código (no codificado como texto estático).
5. THE Sección_Footer SHALL ser visible en todas las vistas de la Landing_Page que el Usuario pueda alcanzar sin interacción adicional.

---

### Requirement 8: Integración con la App existente sin React Router

**User Story:** Como desarrollador, quiero integrar la landing page en el proyecto sin añadir dependencias externas, para mantener la arquitectura simple del proyecto.

#### Acceptance Criteria

1. THE Landing_Page SHALL implementarse como un componente React en el archivo `frontend/src/components/LandingPage.jsx`.
2. THE App_Principal SHALL controlar la visibilidad de la Landing_Page mediante un estado local de React (`useState`) inicializado en el valor `"landing"`, sin requerir `react-router-dom` u otra librería de enrutamiento.
3. THE Landing_Page SHALL aceptar una prop `onEnter` de tipo función que, al invocarse, notifique a la App_Principal que el Usuario desea ingresar.
4. WHEN la prop `onEnter` es invocada desde cualquier CTA de la Landing_Page, THE App_Principal SHALL cambiar el estado de `"landing"` a `"app"`, ocultando la Landing_Page y mostrando la App_Principal.
5. IF la prop `onEnter` no es provista al componente Landing_Page, THEN THE Landing_Page SHALL omitir la invocación silenciosamente sin lanzar un error en tiempo de ejecución.
6. THE Landing_Page SHALL usar únicamente las dependencias ya declaradas en el archivo `package.json` del proyecto, sin agregar nuevas entradas a `dependencies` ni `devDependencies`.
