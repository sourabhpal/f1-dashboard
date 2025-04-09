/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        // Add Goldman font, ensuring sans-serif is a fallback
        goldman: ['Goldman', 'sans-serif'],
      },
    },
  },
  plugins: [],
} 