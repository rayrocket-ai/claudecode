/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sidebar: '#1E293B',
        facebook: '#1877F2',
        instagram: '#E4405F',
        twitter: '#000000',
        youtube: '#FF0000',
        tiktok: '#69C9D0',
      },
    },
  },
  plugins: [],
}
