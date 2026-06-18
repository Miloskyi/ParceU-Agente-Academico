import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../App'

describe('App — integration', () => {
  it('initial render shows landing page with h1 "ParcerU"', () => {
    render(<App />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('ParcerU')
  })

  it('clicking "Empezar ahora" transitions away from landing page', () => {
    render(<App />)
    // Confirm we are on the landing page
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('ParcerU')

    // Click the primary CTA
    fireEvent.click(screen.getByRole('button', { name: 'Empezar ahora' }))

    // Landing page h1 should no longer be in the document
    expect(screen.queryByRole('heading', { level: 1, name: /ParcerU/i })).toBeNull()
  })
})
