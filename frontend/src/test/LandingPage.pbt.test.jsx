import { render, screen, cleanup, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, afterEach } from 'vitest'
import * as fc from 'fast-check'
import LandingPage, {
  DATA_FUNCIONALIDADES,
  DATA_PASOS,
  DATA_CATEGORIAS,
} from '../components/LandingPage'

// Clean up the DOM after every test so renders don't bleed between runs
afterEach(() => cleanup())

// ---------------------------------------------------------------------------
// Propiedad 1 — Las tarjetas de funcionalidades renderizan todos sus datos
// Feature: landing-page-parceru, Propiedad 1: Las tarjetas de funcionalidades renderizan títulos y descripciones no vacíos
// Validates: Requirements 3.1
// ---------------------------------------------------------------------------

describe('PBT — Propiedad 1: Tarjetas de funcionalidades tienen título y descripción no vacíos', () => {
  it('todas las tarjetas de DATA_FUNCIONALIDADES renderizan titulo y descripcion en el DOM', () => {
    // Feature: landing-page-parceru, Propiedad 1: Las 4 tarjetas de funcionalidades renderizan títulos y descripciones no vacíos
    fc.assert(
      fc.property(fc.constant(DATA_FUNCIONALIDADES), (funcionalidades) => {
        const { unmount } = render(<LandingPage />)

        funcionalidades.forEach((item) => {
          // Each titulo must be present in the document
          expect(item.titulo.length).toBeGreaterThan(0)
          const tituloEl = screen.getByText(item.titulo)
          expect(tituloEl).toBeInTheDocument()

          // Each descripcion must be present in the document
          expect(item.descripcion.length).toBeGreaterThan(0)
          const descripcionEl = screen.getByText(item.descripcion)
          expect(descripcionEl).toBeInTheDocument()
        })

        unmount()
      }),
      { numRuns: 100 }
    )
  })
})

// ---------------------------------------------------------------------------
// Propiedad 2 — El orden de los pasos se preserva en el renderizado (1, 2, 3)
// Feature: landing-page-parceru, Propiedad 2: Los números de paso aparecen en orden ascendente 1 → 2 → 3
// Validates: Requirements 4.1
// ---------------------------------------------------------------------------

describe('PBT — Propiedad 2: Números de paso renderizados en orden ascendente', () => {
  it('los elementos con los números 1, 2, 3 aparecen en el DOM en ese orden', () => {
    // Feature: landing-page-parceru, Propiedad 2: Los números de paso aparecen en orden ascendente 1 → 2 → 3
    fc.assert(
      fc.property(fc.constant(DATA_PASOS), (pasos) => {
        const { unmount, container } = render(<LandingPage />)

        // Collect all elements that display exactly the step numbers
        // They are rendered as bold text inside the step cards
        const stepNumbers = pasos.map((p) => p.numero)

        // Walk the DOM in document order to collect positions of each number
        const allText = Array.from(container.querySelectorAll('span'))
          .filter((el) => /^[0-9]+$/.test(el.textContent?.trim() ?? ''))
          .map((el) => parseInt(el.textContent.trim(), 10))

        // The sequence [1, 2, 3] must appear in order within the span list
        const relevantSpans = allText.filter((n) => stepNumbers.includes(n))
        const uniqueOrdered = [...new Set(relevantSpans)]
        expect(uniqueOrdered).toEqual([1, 2, 3])

        unmount()
      }),
      { numRuns: 100 }
    )
  })
})

// ---------------------------------------------------------------------------
// Propiedad 3 — Invariante de longitud en los datos de pasos
// Feature: landing-page-parceru, Propiedad 3: titulo ≤ 60 chars y descripcion ≤ 120 chars para cada paso
// Validates: Requirements 4.2
// ---------------------------------------------------------------------------

describe('PBT — Propiedad 3: DATA_PASOS cumple las restricciones de longitud', () => {
  it('cada paso tiene titulo.length ≤ 60 y descripcion.length ≤ 120', () => {
    // Feature: landing-page-parceru, Propiedad 3: titulo ≤ 60 chars y descripcion ≤ 120 chars para cada paso
    fc.assert(
      fc.property(fc.constant(DATA_PASOS), (pasos) => {
        pasos.forEach((paso) => {
          expect(paso.titulo.length).toBeLessThanOrEqual(60)
          expect(paso.descripcion.length).toBeLessThanOrEqual(120)
        })
      }),
      { numRuns: 100 }
    )
  })
})

// ---------------------------------------------------------------------------
// Propiedad 4 — Las categorías de consultas tienen entre 3 y 6 ejemplos
// Feature: landing-page-parceru, Propiedad 4: Cada categoría en DATA_CATEGORIAS tiene entre 3 y 6 ejemplos
// Validates: Requirements 5.3
// ---------------------------------------------------------------------------

describe('PBT — Propiedad 4: DATA_CATEGORIAS tiene entre 3 y 6 ejemplos por categoría', () => {
  it('cada categoría satisface 3 ≤ ejemplos.length ≤ 6', () => {
    // Feature: landing-page-parceru, Propiedad 4: Cada categoría en DATA_CATEGORIAS tiene entre 3 y 6 ejemplos
    fc.assert(
      fc.property(fc.constant(DATA_CATEGORIAS), (categorias) => {
        categorias.forEach((categoria) => {
          expect(categoria.ejemplos.length).toBeGreaterThanOrEqual(3)
          expect(categoria.ejemplos.length).toBeLessThanOrEqual(6)
        })
      }),
      { numRuns: 100 }
    )
  })
})

// ---------------------------------------------------------------------------
// Propiedad 5 — Todos los CTAs invocan onEnter exactamente una vez por clic
// Feature: landing-page-parceru, Propiedad 5: Cualquier CTA llama a onEnter exactamente una vez al hacer clic
// Validates: Requirements 1.4, 6.2, 8.4
// ---------------------------------------------------------------------------

describe('PBT — Propiedad 5: Cada CTA invoca onEnter exactamente una vez', () => {
  it('el CTA clickeado llama a onEnter exactamente una vez', () => {
    // Feature: landing-page-parceru, Propiedad 5: Cualquier CTA llama a onEnter exactamente una vez al hacer clic
    fc.assert(
      fc.property(
        fc.constantFrom('Empezar ahora', 'Ingresar a ParcerU'),
        (buttonText) => {
          const onEnter = vi.fn()
          const { unmount } = render(<LandingPage onEnter={onEnter} />)

          const button = screen.getByRole('button', { name: buttonText })
          fireEvent.click(button)

          expect(onEnter).toHaveBeenCalledTimes(1)

          unmount()
        }
      ),
      { numRuns: 100 }
    )
  })
})

// ---------------------------------------------------------------------------
// Propiedad 6 — El año del Footer refleja siempre el año en curso
// Feature: landing-page-parceru, Propiedad 6: El footer muestra el año actual obtenido dinámicamente
// Validates: Requirements 7.4
// ---------------------------------------------------------------------------

describe('PBT — Propiedad 6: El Footer muestra el año dinámico correcto', () => {
  it('el footer renderiza el año devuelto por Date.getFullYear()', () => {
    // Feature: landing-page-parceru, Propiedad 6: El footer muestra el año actual obtenido dinámicamente
    fc.assert(
      fc.property(fc.integer({ min: 2024, max: 2099 }), (year) => {
        const spy = vi.spyOn(Date.prototype, 'getFullYear').mockReturnValue(year)

        const { unmount } = render(<LandingPage />)

        // The footer renders "© <year>" — look for an element containing the year
        const yearText = screen.getByText(new RegExp(`©\\s*${year}`))
        expect(yearText).toBeInTheDocument()

        unmount()
        spy.mockRestore()
      }),
      { numRuns: 50 }
    )
  })
})
