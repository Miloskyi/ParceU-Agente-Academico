import '@testing-library/jest-dom'

// jsdom does not implement scrollIntoView — stub it so components that call
// it (e.g. ChatTab's auto-scroll useEffect) don't throw in tests.
window.HTMLElement.prototype.scrollIntoView = () => {}
