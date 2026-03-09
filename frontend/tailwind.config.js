/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        dark: { bg: '#0F1117', card: '#1A1D29', border: '#2A2D3A', hover: '#252836' },
        accent: { primary: '#6366F1', secondary: '#8B5CF6', success: '#10B981', danger: '#EF4444', warning: '#F59E0B', info: '#3B82F6' }
      },
    },
  },
  plugins: [],
}