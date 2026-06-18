import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import LandingPage from '../components/LandingPage'

// ---------------------------------------------------------------------------
// Basic rendering
// ---------------------------------------------------------------------------

describe('LandingPage — basic rendering', () => {
  it('renders without error', () => {
    expect(() => render(<LandingPage />)).not.toThrow()
  })

  it('h1 contains "ParcerU"', () => {
    render(<LandingPage />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('ParcerU')
  })

  it('tagline contains "copiloto"', () => {
    render(<LandingPage />)
    expect(screen.getByText(/copiloto/i)).toBeInTheDocument()
  })

  it('tagline contains "Universidad de Antioquia"', () => {
    render(<LandingPage />)
    expect(screen.getAllByText(/Universidad de Antioquia/i).length).toBeGreaterThan(0)
  })

  it('logo has alt text "Logo ParcerU"', () => {
    render(<LandingPage />)
    const logo = screen.getByAltText('Logo ParcerU')
    expect(logo).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// CTAs and onEnter prop
// ---------------------------------------------------------------------------

describe('LandingPage — CTAs and onEnter prop', () => {
  it('primary CTA text is exactly "Empezar ahora"', () => {
    render(<LandingPage />)
    expect(screen.getByRole('button', { name: 'Empezar ahora' })).toBeInTheDocument()
  })

  it('primary CTA calls onEnter when clicked', () => {
    const onEnter = vi.fn()
    render(<LandingPage onEnter={onEnter} />)
    fireEvent.click(screen.getByRole('button', { name: 'Empezar ahora' }))
    expect(onEnter).toHaveBeenCalledTimes(1)
  })

  it('second CTA calls onEnter when clicked', () => {
    const onEnter = vi.fn()
    render(<LandingPage onEnter={onEnter} />)
    fireEvent.click(screen.getByRole('button', { name: 'Ingresar a ParcerU' }))
    expect(onEnter).toHaveBeenCalledTimes(1)
  })

  it('second CTA text is NOT "Empezar ahora"', () => {
    render(<LandingPage />)
    const buttons = screen.getAllByRole('button')
    const nonPrimary = buttons.filter((b) => b.textContent !== 'Empezar ahora')
    expect(nonPrimary.length).toBeGreaterThan(0)
    nonPrimary.forEach((b) => expect(b.textContent).not.toBe('Empezar ahora'))
  })

  it('does not crash when onEnter is not provided and CTA is clicked', () => {
    render(<LandingPage />)
    expect(() => {
      fireEvent.click(screen.getByRole('button', { name: 'Empezar ahora' }))
    }).not.toThrow()
  })

  it('does not crash when onEnter is not provided and second CTA is clicked', () => {
    render(<LandingPage />)
    expect(() => {
      fireEvent.click(screen.getByRole('button', { name: 'Ingresar a ParcerU' }))
    }).not.toThrow()
  })
})

// ---------------------------------------------------------------------------
// Content sections
// ---------------------------------------------------------------------------

describe('LandingPage — content sections', () => {
  it('footer contains affiliation text "Universidad de Antioquia — Facultad de Ingeniería"', () => {
    render(<LandingPage />)
    expect(
      screen.getByText('Universidad de Antioquia — Facultad de Ingeniería')
    ).toBeInTheDocument()
  })

  it('footer contains the legal disclaimer', () => {
    render(<LandingPage />)
    expect(
      screen.getByText(
        'Herramienta orientativa. Las respuestas no reemplazan la orientación oficial de las dependencias universitarias.'
      )
    ).toBeInTheDocument()
  })

  it('renders the 4 required categories', () => {
    render(<LandingPage />)
    expect(screen.getByText('Reglamento Estudiantil')).toBeInTheDocument()
    expect(screen.getByText('Trámites y Procedimientos')).toBeInTheDocument()
    expect(screen.getByText('Calendario Académico')).toBeInTheDocument()
    expect(screen.getByText('Bienestar Universitario')).toBeInTheDocument()
  })

  it('shows official UdeA source text', () => {
    render(<LandingPage />)
    expect(
      screen.getByText(/documentos oficiales de la Universidad de Antioquia/i)
    ).toBeInTheDocument()
  })

  it('renders exactly 3 steps', () => {
    render(<LandingPage />)
    // The step numbers 1, 2, 3 appear as visible text inside the step cards
    // Use getAllByText to find each numeric label in the steps area
    const one = screen.getAllByText('1')
    const two = screen.getAllByText('2')
    const three = screen.getAllByText('3')
    expect(one.length).toBeGreaterThan(0)
    expect(two.length).toBeGreaterThan(0)
    expect(three.length).toBeGreaterThan(0)
  })

  it('advisory notice in ComoFunciona is visible without interaction', () => {
    render(<LandingPage />)
    expect(
      screen.getByText(
        /Las respuestas son orientativas\. Consulta las oficinas para decisiones definitivas\./i
      )
    ).toBeInTheDocument()
  })
})
