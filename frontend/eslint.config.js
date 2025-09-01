import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'

export default [
  { ignores: ['dist', 'node_modules', 'coverage'] },
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...js.configs.recommended.rules,
      'no-unused-vars': ['warn', { varsIgnorePattern: '^_' }],
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
    },
  },
  // Test files configuration
  {
    files: ['**/__tests__/**/*.{js,jsx}', '**/*.test.{js,jsx}', '**/*.spec.{js,jsx}', 'src/setupTests.js'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.jest,
        ...globals.node,
      },
    },
    rules: {
      'no-unused-vars': ['warn', { varsIgnorePattern: '^_' }],
    },
  },
  // Mock files configuration  
  {
    files: ['**/__mocks__/**/*.{js,jsx}'],
    languageOptions: {
      globals: {
        ...globals.node,
        global: 'writable',
        process: 'readonly',
      },
    },
    rules: {
      'no-unused-vars': 'off',
    },
  },
]
