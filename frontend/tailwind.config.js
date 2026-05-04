/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        'emi-blue': '#002366',    // Deep Royal Blue
        'emi-accent': '#2563eb',  // Vibrant modern Blue
        'emi-gray': '#f3f4f6',    // Light gray for background
        'emi-dark': '#1f2937',    // Dark gray for text
        'emi-glass': 'rgba(255, 255, 255, 0.7)',
      }
    },
  },
  plugins: [],
}

