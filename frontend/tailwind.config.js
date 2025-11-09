/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  safelist: [
    // Protect DaisyUI loading spinner classes and animations from being purged in production builds
    'loading',
    'loading-spinner',
    'loading-xs',
    'loading-sm',
    'loading-md',
    'loading-lg',
    { pattern: /loading/ },
  ],
  theme: {
    extend: {},
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: ['light', 'dark'],
  },
};
