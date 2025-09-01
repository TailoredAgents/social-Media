// Accessibility utility functions for WCAG 2.1 AA compliance

/**
 * Check if color contrast meets WCAG AA standards
 * @param {string} foreground - Hex color code for foreground
 * @param {string} background - Hex color code for background
 * @returns {boolean} - True if contrast ratio meets AA standards (4.5:1)
 */
export const checkColorContrast = (foreground, background) => {
  const getLuminance = (color) => {
    const hex = color.replace('#', '')
    const r = parseInt(hex.substr(0, 2), 16) / 255
    const g = parseInt(hex.substr(2, 2), 16) / 255
    const b = parseInt(hex.substr(4, 2), 16) / 255
    
    const sRGB = [r, g, b].map(c => {
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
    })
    
    return 0.2126 * sRGB[0] + 0.7152 * sRGB[1] + 0.0722 * sRGB[2]
  }
  
  const l1 = getLuminance(foreground)
  const l2 = getLuminance(background)
  const lighter = Math.max(l1, l2)
  const darker = Math.min(l1, l2)
  
  const contrastRatio = (lighter + 0.05) / (darker + 0.05)
  return contrastRatio >= 4.5 // WCAG AA standard
}

/**
 * Generate accessible IDs for form elements
 * @param {string} base - Base name for the ID
 * @returns {string} - Unique accessible ID
 */
export const generateAccessibleId = (base) => {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substr(2, 5)
  return `${base}-${timestamp}-${random}`
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
}

/**
 * Check if element has minimum touch target size (44x44px)
 * @param {HTMLElement} element - DOM element to check
 * @returns {boolean} - True if meets minimum size requirements
 */
export const checkTouchTargetSize = (element) => {
  if (!element || typeof element.getBoundingClientRect !== 'function') {
    return false
  }
  
  const rect = element.getBoundingClientRect()
  return rect.width >= 44 && rect.height >= 44
}

/**
 * Announce content to screen readers using live regions
 * @param {string} message - Message to announce
 * @param {string} priority - 'polite' or 'assertive'
 */
export const announceToScreenReader = (message, priority = 'polite') => {
  const liveRegion = document.createElement('div')
  liveRegion.setAttribute('aria-live', priority)
  liveRegion.setAttribute('aria-atomic', 'true')
  liveRegion.setAttribute('class', 'sr-only')
  liveRegion.textContent = message
  
  document.body.appendChild(liveRegion)
  
  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(liveRegion)
  }, 1000)
}

/**
 * Check if text has appropriate heading hierarchy
 * @param {HTMLElement} container - Container element to check
 * @returns {Object} - Analysis of heading structure
 */
export const checkHeadingHierarchy = (container) => {
  const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6')
  const hierarchy = []
  let hasH1 = false
  let violations = []
  
  headings.forEach((heading, index) => {
    const level = parseInt(heading.tagName.charAt(1))
    hierarchy.push({ element: heading, level, index })
    
    if (level === 1) hasH1 = true
    
    if (index > 0) {
      const prevLevel = hierarchy[index - 1].level
      if (level > prevLevel + 1) {
        violations.push({
          element: heading,
          issue: `Heading level jumps from h${prevLevel} to h${level}`
        })
      }
    }
  })
  
  return {
    hasH1,
    violations,
    hierarchy: hierarchy.map(h => ({ level: h.level, text: h.element.textContent }))
  }
}

/**
 * Check for keyboard accessibility issues
 * @param {HTMLElement} container - Container to check
 * @returns {Array} - List of potential keyboard navigation issues
 */
export const checkKeyboardAccessibility = (container) => {
  const issues = []
  
  // Check for elements that should be focusable but aren't
  const clickableElements = container.querySelectorAll('[onclick], .cursor-pointer')
  clickableElements.forEach(element => {
    const isButton = element.tagName === 'BUTTON'
    const isLink = element.tagName === 'A' && element.hasAttribute('href')
    const hasTabIndex = element.hasAttribute('tabindex')
    const hasRole = element.getAttribute('role') === 'button'
    
    if (!isButton && !isLink && !hasTabIndex && !hasRole) {
      issues.push({
        element,
        issue: 'Clickable element is not keyboard accessible'
      })
    }
  })
  
  // Check for focus traps in modals
  const modals = container.querySelectorAll('[role="dialog"], .modal')
  modals.forEach(modal => {
    const focusableElements = modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    
    if (focusableElements.length === 0) {
      issues.push({
        element: modal,
        issue: 'Modal has no focusable elements'
      })
    }
  })
  
  return issues
}

/**
 * Validate form accessibility
 * @param {HTMLFormElement} form - Form element to validate
 * @returns {Object} - Validation results
 */
export const validateFormAccessibility = (form) => {
  const issues = []
  const inputs = form.querySelectorAll('input, select, textarea')
  
  inputs.forEach(input => {
    const id = input.id
    const label = form.querySelector(`label[for="${id}"]`)
    const ariaLabel = input.getAttribute('aria-label')
    const ariaLabelledBy = input.getAttribute('aria-labelledby')
    
    if (!label && !ariaLabel && !ariaLabelledBy) {
      issues.push({
        element: input,
        issue: 'Form control lacks accessible label'
      })
    }
    
    // Check required field indicators
    if (input.hasAttribute('required')) {
      const hasAriaRequired = input.getAttribute('aria-required') === 'true'
      const hasVisualIndicator = input.classList.contains('required') || 
        form.querySelector(`[aria-describedby="${id}-required"]`)
      
      if (!hasAriaRequired || !hasVisualIndicator) {
        issues.push({
          element: input,
          issue: 'Required field lacks proper indicators'
        })
      }
    }
  })
  
  return {
    valid: issues.length === 0,
    issues
  }
}

/**
 * WCAG 2.1 AA Compliance Checker
 * @param {HTMLElement} container - Container element to audit
 * @returns {Object} - Comprehensive accessibility audit results
 */
export const auditAccessibility = (container = document.body) => {
  const results = {
    timestamp: new Date().toISOString(),
    overall: { compliant: true, score: 100 },
    sections: {
      headings: checkHeadingHierarchy(container),
      keyboard: checkKeyboardAccessibility(container),
      forms: [],
      images: [],
      colors: { tested: false, message: 'Color contrast requires manual testing' }
    },
    recommendations: []
  }
  
  // Check forms
  const forms = container.querySelectorAll('form')
  forms.forEach(form => {
    results.sections.forms.push(validateFormAccessibility(form))
  })
  
  // Check images
  const images = container.querySelectorAll('img')
  images.forEach(img => {
    const alt = img.getAttribute('alt')
    const ariaLabel = img.getAttribute('aria-label')
    const ariaHidden = img.getAttribute('aria-hidden') === 'true'
    
    if (!alt && !ariaLabel && !ariaHidden) {
      results.sections.images.push({
        element: img,
        issue: 'Image lacks alternative text'
      })
    }
  })
  
  // Generate score and recommendations
  const totalIssues = 
    results.sections.headings.violations.length +
    results.sections.keyboard.length +
    results.sections.forms.reduce((sum, form) => sum + form.issues.length, 0) +
    results.sections.images.length
  
  results.overall.score = Math.max(0, 100 - (totalIssues * 10))
  results.overall.compliant = totalIssues === 0
  
  if (!results.sections.headings.hasH1) {
    results.recommendations.push('Add a main h1 heading to the page')
  }
  
  if (totalIssues > 0) {
    results.recommendations.push('Review and fix accessibility issues before production')
  }
  
  return results
}

export default {
  checkColorContrast,
  generateAccessibleId,
  checkTouchTargetSize,
  announceToScreenReader,
  checkHeadingHierarchy,
  checkKeyboardAccessibility,
  validateFormAccessibility,
  auditAccessibility
}