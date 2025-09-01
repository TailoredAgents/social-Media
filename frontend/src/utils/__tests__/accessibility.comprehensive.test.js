import { describe, it, expect, beforeEach, afterEach, vi } from '@jest/globals'
import {
  checkColorContrast,
  generateAccessibleId,
  checkTouchTargetSize,
  announceToScreenReader,
  checkHeadingHierarchy,
  checkKeyboardAccessibility,
  validateFormAccessibility,
  auditAccessibility
} from '../accessibility.js'

// Mock DOM environment
Object.defineProperty(window, 'getBoundingClientRect', {
  value: vi.fn()
})

describe('Accessibility Utils', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
    vi.clearAllTimers()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.runOnlyPendingTimers()
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  describe('checkColorContrast', () => {
    it('should return true for high contrast colors', () => {
      // Black text on white background
      expect(checkColorContrast('#000000', '#ffffff')).toBe(true)
      // White text on black background
      expect(checkColorContrast('#ffffff', '#000000')).toBe(true)
    })

    it('should return false for low contrast colors', () => {
      // Light gray on white
      expect(checkColorContrast('#cccccc', '#ffffff')).toBe(false)
      // Light blue on white
      expect(checkColorContrast('#8eb4f0', '#ffffff')).toBe(false)
    })

    it('should handle hex colors without hash prefix', () => {
      expect(checkColorContrast('000000', 'ffffff')).toBe(true)
    })

    it('should meet WCAG AA standard (4.5:1 ratio)', () => {
      // Dark blue on white (should pass)
      expect(checkColorContrast('#1f2937', '#ffffff')).toBe(true)
      // Medium gray on white (should fail)
      expect(checkColorContrast('#9ca3af', '#ffffff')).toBe(false)
    })
  })

  describe('generateAccessibleId', () => {
    it('should generate unique IDs', () => {
      const id1 = generateAccessibleId('test')
      const id2 = generateAccessibleId('test')
      
      expect(id1).not.toBe(id2)
      expect(id1).toMatch(/^test-\d+-[a-z0-9]+$/)
      expect(id2).toMatch(/^test-\d+-[a-z0-9]+$/)
    })

    it('should normalize base strings', () => {
      const id = generateAccessibleId('Test Base Name!')
      expect(id).toMatch(/^test-base-name-\d+-[a-z0-9]+$/)
    })

    it('should handle special characters', () => {
      const id = generateAccessibleId('form@@field##input**')
      expect(id).toMatch(/^form-field-input-\d+-[a-z0-9]+$/)
    })

    it('should not start or end with hyphens', () => {
      const id = generateAccessibleId('--test--')
      expect(id).not.toMatch(/^-/)
      expect(id).not.toMatch(/-$/)
    })
  })

  describe('checkTouchTargetSize', () => {
    it('should return true for elements meeting minimum size', () => {
      const element = {
        getBoundingClientRect: vi.fn().mockReturnValue({
          width: 44,
          height: 44
        })
      }
      
      expect(checkTouchTargetSize(element)).toBe(true)
    })

    it('should return false for elements too small', () => {
      const element = {
        getBoundingClientRect: vi.fn().mockReturnValue({
          width: 30,
          height: 30
        })
      }
      
      expect(checkTouchTargetSize(element)).toBe(false)
    })

    it('should return false for null element', () => {
      expect(checkTouchTargetSize(null)).toBe(false)
    })

    it('should return false for element without getBoundingClientRect', () => {
      const element = {}
      expect(checkTouchTargetSize(element)).toBe(false)
    })

    it('should handle large touch targets', () => {
      const element = {
        getBoundingClientRect: vi.fn().mockReturnValue({
          width: 100,
          height: 60
        })
      }
      
      expect(checkTouchTargetSize(element)).toBe(true)
    })
  })

  describe('announceToScreenReader', () => {
    it('should create and remove live region', () => {
      announceToScreenReader('Test announcement')
      
      const liveRegion = document.querySelector('[aria-live="polite"]')
      expect(liveRegion).toBeTruthy()
      expect(liveRegion.textContent).toBe('Test announcement')
      expect(liveRegion.getAttribute('aria-atomic')).toBe('true')
      
      // Fast-forward time to check removal
      vi.advanceTimersByTime(1000)
      expect(document.querySelector('[aria-live="polite"]')).toBeFalsy()
    })

    it('should support assertive priority', () => {
      announceToScreenReader('Urgent message', 'assertive')
      
      const liveRegion = document.querySelector('[aria-live="assertive"]')
      expect(liveRegion).toBeTruthy()
      expect(liveRegion.textContent).toBe('Urgent message')
    })

    it('should default to polite priority', () => {
      announceToScreenReader('Default message')
      
      const liveRegion = document.querySelector('[aria-live="polite"]')
      expect(liveRegion).toBeTruthy()
    })
  })

  describe('checkHeadingHierarchy', () => {
    it('should identify proper heading hierarchy', () => {
      document.body.innerHTML = `
        <div id="container">
          <h1>Main Title</h1>
          <h2>Section</h2>
          <h3>Subsection</h3>
        </div>
      `
      
      const container = document.getElementById('container')
      const result = checkHeadingHierarchy(container)
      
      expect(result.hasH1).toBe(true)
      expect(result.violations).toHaveLength(0)
      expect(result.hierarchy).toEqual([
        { level: 1, text: 'Main Title' },
        { level: 2, text: 'Section' },
        { level: 3, text: 'Subsection' }
      ])
    })

    it('should detect heading level jumps', () => {
      document.body.innerHTML = `
        <div id="container">
          <h1>Main Title</h1>
          <h4>Jumped to h4</h4>
        </div>
      `
      
      const container = document.getElementById('container')
      const result = checkHeadingHierarchy(container)
      
      expect(result.violations).toHaveLength(1)
      expect(result.violations[0].issue).toContain('Heading level jumps from h1 to h4')
    })

    it('should detect missing h1', () => {
      document.body.innerHTML = `
        <div id="container">
          <h2>Section</h2>
          <h3>Subsection</h3>
        </div>
      `
      
      const container = document.getElementById('container')
      const result = checkHeadingHierarchy(container)
      
      expect(result.hasH1).toBe(false)
    })
  })

  describe('checkKeyboardAccessibility', () => {
    it('should identify clickable elements without keyboard access', () => {
      document.body.innerHTML = `
        <div id="container">
          <div onclick="doSomething()" class="cursor-pointer">Clickable div</div>
          <button>Accessible button</button>
          <a href="#test">Accessible link</a>
        </div>
      `
      
      const container = document.getElementById('container')
      const issues = checkKeyboardAccessibility(container)
      
      expect(issues).toHaveLength(1)
      expect(issues[0].issue).toContain('not keyboard accessible')
    })

    it('should validate modal focus management', () => {
      document.body.innerHTML = `
        <div id="container">
          <div role="dialog">
            <span>Modal without focusable elements</span>
          </div>
        </div>
      `
      
      const container = document.getElementById('container')
      const issues = checkKeyboardAccessibility(container)
      
      expect(issues).toHaveLength(1)
      expect(issues[0].issue).toContain('no focusable elements')
    })

    it('should handle properly accessible elements', () => {
      document.body.innerHTML = `
        <div id="container">
          <button onclick="doSomething()">Proper button</button>
          <div role="button" tabindex="0" onclick="doSomething()">Proper div button</div>
          <div role="dialog">
            <button>Close</button>
            <input type="text">
          </div>
        </div>
      `
      
      const container = document.getElementById('container')
      const issues = checkKeyboardAccessibility(container)
      
      expect(issues).toHaveLength(0)
    })
  })

  describe('validateFormAccessibility', () => {
    it('should validate form with proper labels', () => {
      document.body.innerHTML = `
        <form id="test-form">
          <label for="name">Name</label>
          <input type="text" id="name">
          
          <input type="email" aria-label="Email address">
          
          <input type="password" aria-labelledby="pwd-label">
          <div id="pwd-label">Password</div>
        </form>
      `
      
      const form = document.getElementById('test-form')
      const result = validateFormAccessibility(form)
      
      expect(result.valid).toBe(true)
      expect(result.issues).toHaveLength(0)
    })

    it('should detect unlabeled form controls', () => {
      document.body.innerHTML = `
        <form id="test-form">
          <input type="text" id="unlabeled">
          <select id="unlabeled-select">
            <option>Option 1</option>
          </select>
        </form>
      `
      
      const form = document.getElementById('test-form')
      const result = validateFormAccessibility(form)
      
      expect(result.valid).toBe(false)
      expect(result.issues).toHaveLength(2)
      expect(result.issues[0].issue).toContain('lacks accessible label')
    })

    it('should validate required field indicators', () => {
      document.body.innerHTML = `
        <form id="test-form">
          <label for="req1">Required Field 1</label>
          <input type="text" id="req1" required aria-required="true" class="required">
          
          <label for="req2">Required Field 2</label>
          <input type="text" id="req2" required>
        </form>
      `
      
      const form = document.getElementById('test-form')
      const result = validateFormAccessibility(form)
      
      expect(result.issues).toHaveLength(1)
      expect(result.issues[0].issue).toContain('Required field lacks proper indicators')
    })
  })

  describe('auditAccessibility', () => {
    it('should perform comprehensive accessibility audit', () => {
      document.body.innerHTML = `
        <div id="container">
          <h1>Main Title</h1>
          <form>
            <label for="test">Test Input</label>
            <input type="text" id="test">
          </form>
          <img src="test.jpg" alt="Test image">
          <button>Accessible button</button>
        </div>
      `
      
      const container = document.getElementById('container')
      const audit = auditAccessibility(container)
      
      expect(audit.overall.compliant).toBe(true)
      expect(audit.overall.score).toBe(100)
      expect(audit.sections.headings.hasH1).toBe(true)
      expect(audit.sections.keyboard).toHaveLength(0)
      expect(audit.sections.forms[0].valid).toBe(true)
      expect(audit.sections.images).toHaveLength(0)
    })

    it('should detect and score accessibility issues', () => {
      document.body.innerHTML = `
        <div id="container">
          <h2>No H1</h2>
          <h4>Skipped heading level</h4>
          <form>
            <input type="text" id="unlabeled">
          </form>
          <img src="test.jpg">
          <div onclick="clickable" class="cursor-pointer">Not accessible</div>
        </div>
      `
      
      const container = document.getElementById('container')
      const audit = auditAccessibility(container)
      
      expect(audit.overall.compliant).toBe(false)
      expect(audit.overall.score).toBeLessThan(100)
      expect(audit.sections.headings.hasH1).toBe(false)
      expect(audit.recommendations).toContain('Add a main h1 heading to the page')
    })

    it('should include timestamp and be structured correctly', () => {
      const audit = auditAccessibility()
      
      expect(audit.timestamp).toBeTruthy()
      expect(new Date(audit.timestamp)).toBeInstanceOf(Date)
      expect(audit.sections).toHaveProperty('headings')
      expect(audit.sections).toHaveProperty('keyboard')
      expect(audit.sections).toHaveProperty('forms')
      expect(audit.sections).toHaveProperty('images')
      expect(audit.sections).toHaveProperty('colors')
    })
  })
})