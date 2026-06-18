# 🤝 Guía de Contribución - PARCERU

## Flujo de Trabajo del Equipo

### Roles y Responsabilidades

| Persona | Rol Principal | Módulos Asignados |
|---------|---------------|-------------------|
| **Desarrollador 1** | Data Engineer | `ingesta/`, `data/`, `agentes/doc_watcher.py`, `agentes/runtime_extractor.py` |
| **Desarrollador 2** | AI/ML Engineer | `agentes/` (grafo LangGraph), `backend/main.py`, `utils/` |
| **Desarrollador 3** | Frontend Developer | `frontend/`, `tests/frontend/`, UI/UX |
| **Desarrollador 4** | Tech Lead / DevOps | Arquitectura, `tests/`, CI/CD, documentación |

### Estructura de Branches

```
main
├── feature/frontend-chat-component
├── feature/agent-urgency-detector  
├── feature/sia-scraper-integration
└── hotfix/cors-configuration
```

**Convención de nombrado:**
- `feature/descripcion-breve` - Nuevas funcionalidades
- `bugfix/descripcion-problema` - Corrección de bugs
- `hotfix/problema-critico` - Fixes urgentes para producción
- `refactor/modulo-nombre` - Refactoring de código
- `docs/actualizacion-tema` - Actualizaciones de documentación

## Setup de Desarrollo

### 1. Configuración Inicial
```bash
# Clonar y configurar
git clone <repo-url>
cd Hackathon-UdeA-Softserve

# Crear rama de desarrollo personal
git checkout -b feature/mi-nueva-funcionalidad

# Setup ambiente Python
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Setup ambiente Node.js
cd frontend
npm install
cd ..

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus keys
```

### 2. Pre-commit Hooks (Recomendado)
```bash
# Instalar pre-commit
pip install pre-commit

# Configurar hooks
pre-commit install

# Test manual
pre-commit run --all-files
```

### 3. Verificar Setup
```bash
# Test backend
python -c "from backend.main import app; print('Backend OK')"
python -m pytest tests/ -v

# Test frontend  
cd frontend
npm test
npm run build
```

## Estándares de Código

### Python (Backend/Agentes)

#### Formateo y Linting
```bash
# Black para formateo automático
pip install black isort flake8
black agentes/ backend/ tests/
isort agentes/ backend/ tests/

# Linting con flake8
flake8 agentes/ backend/ --max-line-length=88
```

#### Convenciones de Naming
```python
# Variables y funciones: snake_case
def procesar_documento_pdf(archivo_path):
    nombre_documento = extraer_titulo(archivo_path)
    
# Classes: PascalCase
class EstadoCopiloto:
    pass

# Constantes: UPPER_SNAKE_CASE
TIMEOUT_DESCARGA = 30
MAX_REINTENTOS = 3

# Archivos: snake_case.py
# agentes/runtime_extractor.py ✅
# agentes/RuntimeExtractor.py ❌
```

#### Docstrings
```python
def buscar_documentos(query: str, filtros: dict = None) -> List[dict]:
    """
    Busca documentos en ChromaDB usando búsqueda semántica.
    
    Args:
        query: Término de búsqueda en lenguaje natural
        filtros: Diccionario opcional con filtros de metadatos
        
    Returns:
        Lista de documentos con scores de similitud
        
    Raises:
        ChromaDBError: Si la base de datos no está disponible
        
    Example:
        >>> docs = buscar_documentos("matrícula 2026")
        >>> len(docs)
        5
    """
```

#### Type Hints
```python
from typing import List, Dict, Optional, Union
from agentes.estado import EstadoCopiloto

def procesar_consulta(
    estado: EstadoCopiloto,
    timeout: Optional[int] = None
) -> Dict[str, Union[str, List[str]]]:
    pass
```

### JavaScript/React (Frontend)

#### Formateo
```bash
# Prettier para formateo
cd frontend
npm install -D prettier eslint
npx prettier --write src/
npx eslint src/ --fix
```

#### Convenciones de Naming
```javascript
// Variables y funciones: camelCase
const mensajeUsuario = "Hola";
function enviarConsulta(mensaje) { }

// Componentes: PascalCase
function ChatComponent() { }
const TramiteCard = () => { };

// Archivos componentes: PascalCase.jsx
// src/components/ChatComponent.jsx ✅
// src/components/chat-component.jsx ❌

// Constantes: UPPER_SNAKE_CASE
const API_BASE_URL = "http://localhost:8000";
const MAX_MESSAGE_LENGTH = 1000;
```

#### Estructura de Componentes
```javascript
// src/components/ChatComponent.jsx
import React, { useState, useEffect } from 'react';
import { MessageSquare, Send } from 'lucide-react';

/**
 * Componente principal de chat para interactuar con el copiloto
 * @param {Object} props - Propiedades del componente
 * @param {string} props.perfil - Perfil del usuario (pregrado/posgrado/etc)
 */
function ChatComponent({ perfil = "pregrado" }) {
    const [mensaje, setMensaje] = useState("");
    
    // Hooks de efectos
    useEffect(() => {
        // Setup inicial
    }, []);
    
    // Handlers de eventos
    const handleEnviarMensaje = async () => {
        // Lógica de envío
    };
    
    return (
        <div className="flex flex-col h-full">
            {/* JSX aquí */}
        </div>
    );
}

export default ChatComponent;
```

## Testing

### Backend Python

#### Tests Unitarios
```python
# tests/test_router.py
import pytest
from agentes.router import router_node
from agentes.estado import estado_inicial

class TestRouter:
    def test_clasifica_consulta_tramite(self):
        """Test clasificación de consulta sobre trámites"""
        estado = estado_inicial()
        estado["mensajes"] = [{"role": "user", "content": "necesito un certificado"}]
        
        resultado = router_node(estado)
        
        assert resultado["intencion"] == "tramite"
        assert "certificado" in resultado["pregunta_reformulada"]
    
    def test_detecta_urgencia(self):
        """Test detección de palabras clave de urgencia"""
        estado = estado_inicial()
        estado["mensajes"] = [{"role": "user", "content": "me siento mal, necesito ayuda"}]
        
        resultado = router_node(estado)
        
        assert resultado["es_urgente"] == True
        assert resultado["nivel_urgencia"] in ["medio", "alto"]

# Fixtures para datos de test
@pytest.fixture
def estado_base():
    return estado_inicial()

@pytest.fixture
def documentos_mock():
    return [
        {"contenido": "Texto del reglamento...", "fuente": "reglamento.pdf"}
    ]
```

#### Property-Based Testing
```python
# tests/test_properties.py
from hypothesis import given, strategies as st
from agentes.router import clasificar_intencion

@given(st.text(min_size=5, max_size=200))
def test_clasificacion_nunca_falla(mensaje):
    """La clasificación debe funcionar con cualquier texto válido"""
    resultado = clasificar_intencion(mensaje)
    
    # Propiedades que siempre deben cumplirse
    assert resultado["intencion"] in ["normativa", "tramite", "calendario", "urgencia", "otro"]
    assert isinstance(resultado["categoria"], str)
    assert len(resultado["pregunta_reformulada"]) > 0
```

### Frontend React

#### Tests de Componentes
```javascript
// tests/ChatComponent.test.jsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import ChatComponent from '../src/components/ChatComponent';

// Mock axios
vi.mock('axios', () => ({
    default: {
        post: vi.fn(() => Promise.resolve({
            data: { respuesta: "Respuesta mock", fuentes: [] }
        }))
    }
}));

describe('ChatComponent', () => {
    test('renderiza input de mensaje', () => {
        render(<ChatComponent perfil="pregrado" />);
        
        const input = screen.getByPlaceholderText(/escribe tu consulta/i);
        expect(input).toBeInTheDocument();
    });
    
    test('envía mensaje al hacer clic en botón', async () => {
        render(<ChatComponent perfil="pregrado" />);
        
        const input = screen.getByRole('textbox');
        const button = screen.getByRole('button', { name: /enviar/i });
        
        fireEvent.change(input, { target: { value: 'mensaje de prueba' } });
        fireEvent.click(button);
        
        await waitFor(() => {
            expect(screen.getByText('Respuesta mock')).toBeInTheDocument();
        });
    });
});
```

#### Property-Based Testing React
```javascript
// tests/properties.test.js
import fc from 'fast-check';
import { validarMensaje, formatearRespuesta } from '../src/utils/validators';

describe('Propiedades del validador', () => {
    test('validarMensaje siempre retorna booleano', () => {
        fc.assert(fc.property(
            fc.string({ minLength: 0, maxLength: 1000 }),
            (mensaje) => {
                const resultado = validarMensaje(mensaje);
                return typeof resultado === 'boolean';
            }
        ));
    });
});
```

## Pull Request Process

### 1. Antes de Crear PR
```bash
# Actualizar rama local
git checkout main
git pull origin main
git checkout feature/mi-rama
git rebase main  # o git merge main

# Ejecutar todos los tests
python -m pytest tests/ -v
cd frontend && npm test

# Formatear código
black agentes/ backend/
cd frontend && npx prettier --write src/

# Verificar que no hay errores
flake8 agentes/ backend/
cd frontend && npx eslint src/
```

### 2. Template de PR

```markdown
## 📋 Descripción
Breve descripción de los cambios implementados.

## 🔗 Issue Relacionado
- Cierra #123
- Relacionado con #456

## 🧪 Tipo de Cambio
- [ ] Bug fix (cambio que corrige un problema)
- [ ] Nueva funcionalidad (cambio que agrega funcionalidad)
- [ ] Cambio breaking (fix o feature que causaría que funcionalidad existente no funcione como se espera)
- [ ] Documentación (cambios solo en documentación)

## 🔍 Tests
- [ ] Los tests existentes pasan
- [ ] Agregué tests para mi cambio
- [ ] Los tests cubren casos edge

## 📝 Checklist
- [ ] Mi código sigue las convenciones del proyecto
- [ ] Hice self-review de mi código
- [ ] Comenté código complejo cuando fue necesario
- [ ] Actualicé documentación relevante
- [ ] Mis cambios no generan nuevos warnings

## 🖼️ Screenshots (si aplica)
Adjuntar capturas de pantalla de cambios UI.
```

### 3. Review Process
- **Mínimo 1 review** de otro miembro del equipo
- **Todos los tests** deben pasar
- **No conflicts** con branch main
- **Documentación** actualizada si es necesario

## Debugging

### Backend Issues
```bash
# Logs detallados
export LOG_LEVEL=DEBUG
python -m uvicorn backend.main:app --log-level debug

# Debug específico de agentes
python -c "
from agentes.grafo import app_grafo
from agentes.estado import estado_inicial
print(app_grafo.invoke(estado_inicial()))
"

# Memory profiling (si hay problemas de rendimiento)
pip install memory-profiler
@profile  # Decorador en funciones
python -m memory_profiler script.py
```

### Frontend Issues
```bash
# Development con sourcemaps detallados
cd frontend
npm run dev -- --debug

# Bundle analysis
npm run build
npm install -g vite-bundle-analyzer
npx vite-bundle-analyzer dist

# Performance profiling
# Usar React DevTools en navegador
```

### Database Issues
```bash
# Reset ChromaDB completamente
rm -rf data/chroma_db
python run_ingesta.py

# Verificar indexación
python -c "
import chromadb
client = chromadb.PersistentClient(path='data/chroma_db')
collection = client.get_collection('documentos_udea')
print(f'Documentos: {collection.count()}')
"
```

## Release Process

### Versionado Semántico
- **MAJOR**: Cambios incompatibles de API (1.0.0 → 2.0.0)
- **MINOR**: Nueva funcionalidad compatible (1.0.0 → 1.1.0)  
- **PATCH**: Bug fixes compatibles (1.0.0 → 1.0.1)

### Preparar Release
```bash
# 1. Crear release branch
git checkout -b release/v1.1.0

# 2. Actualizar versión en archivos
# frontend/package.json: "version": "1.1.0"
# backend/__init__.py: __version__ = "1.1.0"

# 3. Actualizar CHANGELOG.md
echo "## [1.1.0] - 2026-06-18
### Added
- Nueva funcionalidad X
- Integración con sistema Y

### Fixed  
- Bug en módulo Z
" >> CHANGELOG.md

# 4. Final testing
pytest tests/ -v
cd frontend && npm test && npm run build

# 5. Crear tag
git tag -a v1.1.0 -m "Release 1.1.0: Nuevas funcionalidades X, Y"
git push origin v1.1.0
```

## Comunicación del Equipo

### Daily Standups (Virtuales)
- **Cuándo**: Inicio del día de trabajo
- **Formato**: 
  - ¿Qué hice ayer?
  - ¿Qué voy a hacer hoy?
  - ¿Tengo blockers?

### Code Reviews
- **Objetivo**: Compartir conocimiento, mejorar calidad
- **Tono**: Constructivo y educativo
- **Timing**: Máximo 24 horas para review

### Documentación
- **Inline docs**: Para código complejo
- **README**: Para setup y uso básico
- **Wiki/Docs**: Para arquitectura y decisiones

---

¡Gracias por contribuir a PARCERU! 🚀