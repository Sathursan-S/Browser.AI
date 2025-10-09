module.exports = {
  content: [
    './index.html',
    './src/**/*.{ts,tsx,js,jsx}',
  ],
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      keyframes: {
        slideIn: {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        fadeInUp: {
          '0%': { 
            opacity: '0', 
            transform: 'translateY(20px) scale(0.95)' 
          },
          '100%': { 
            opacity: '1', 
            transform: 'translateY(0) scale(1)' 
          },
        },
        fadeOutUp: {
          '0%': { 
            opacity: '1', 
            transform: 'translateY(0) scale(1)' 
          },
          '100%': { 
            opacity: '0', 
            transform: 'translateY(-20px) scale(0.95)' 
          },
        },
      },
      animation: {
        slideIn: 'slideIn 0.3s ease forwards',
        shimmer: 'shimmer 2s linear infinite',
        fadeInUp: 'fadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards',
        fadeOutUp: 'fadeOutUp 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards',
      },
      backgroundSize: {
        '200': '200% 100%',
      },
    },
  },
  plugins: [
    function({ addUtilities }) {
      addUtilities({
        '.scrollbar-thin': {
          'scrollbar-width': 'thin',
        },
        '.scrollbar-none': {
          'scrollbar-width': 'none',
          '-ms-overflow-style': 'none',
        },
        '.scrollbar-none::-webkit-scrollbar': {
          'display': 'none',
        },
        '.scrollbar-track-white\\/5::-webkit-scrollbar-track': {
          'background-color': 'rgba(255, 255, 255, 0.05)',
        },
        '.scrollbar-thumb-white\\/20::-webkit-scrollbar-thumb': {
          'background-color': 'rgba(255, 255, 255, 0.2)',
          'border-radius': '6px',
        },
        '.scrollbar-thumb-white\\/30::-webkit-scrollbar-thumb:hover': {
          'background-color': 'rgba(255, 255, 255, 0.3)',
        },
        '.scrollbar-w-2::-webkit-scrollbar': {
          'width': '8px',
        },
        '.scrollbar-h-2::-webkit-scrollbar': {
          'height': '8px',
        },
      })
    }
  ],
}
