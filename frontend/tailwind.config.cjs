/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
  	extend: {
  		colors: {
  			gargash: {
  				'100': '#FDE8EB',
  				'200': '#F9C5CD',
  				'300': '#F5A2AF',
  				'400': '#E26C7E',
  				'500': '#B22036',
  				'600': '#8E192C',
  				'700': '#6B1321',
  				'800': '#470D16',
  				'900': '#24060B',
  				DEFAULT: '#B22036',
  				light: '#D93A53',
  				dark: '#8E192C'
  			},
  			ai: {
  				light: '#B22036',
  				DEFAULT: '#8E192C',
  				dark: '#6B1321'
  			},
  			enterprise: {
  				DEFAULT: '#1F2937',
  				light: '#374151',
  				dark: '#111827',
  				card: '#1F2937',
  				border: '#374151'
  			},
  			success: {
  				DEFAULT: '#10B981',
  				light: '#34D399',
  				dark: '#059669'
  			},
  			warning: {
  				DEFAULT: '#F59E0B',
  				light: '#FBBF24',
  				dark: '#D97706'
  			},
  			danger: {
  				DEFAULT: '#EF4444',
  				light: '#F87171',
  				dark: '#DC2626'
  			},
  			cyber: {
  				'50': '#FDE8EB',
  				'100': '#F9C5CD',
  				'200': '#F5A2AF',
  				'300': '#E26C7E',
  				'400': '#D93A53',
  				'500': '#B22036',
  				'600': '#8E192C',
  				'700': '#6B1321',
  				'800': '#470D16',
  				'900': '#24060B'
  			},
  			neon: {
  				pink: '#ff00ff',
  				blue: '#00ffff',
  				green: '#00ff8c',
  				yellow: '#ffff00',
  				purple: '#9d00ff'
  			},
  			dark: {
  				DEFAULT: '#121212',
  				light: '#1e1e1e',
  				lighter: '#2a2a2a',
  				card: '#1a1a1a'
  			},
  			platinum: {
  				'100': '#2c2f2d',
  				'200': '#575e5b',
  				'300': '#838d88',
  				'400': '#b3b8b6',
  				'500': '#e2e4e3',
  				'600': '#e8e9e9',
  				'700': '#edefee',
  				'800': '#f3f4f4',
  				'900': '#f9faf9',
  				DEFAULT: '#E2E4E3'
  			},
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			},
  			sidebar: {
  				DEFAULT: 'hsl(var(--sidebar-background))',
  				foreground: 'hsl(var(--sidebar-foreground))',
  				primary: 'hsl(var(--sidebar-primary))',
  				'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
  				accent: 'hsl(var(--sidebar-accent))',
  				'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
  				border: 'hsl(var(--sidebar-border))',
  				ring: 'hsl(var(--sidebar-ring))'
  			}
  		},
  		fontFamily: {
  			sans: [
  				'Inter',
  				'ui-sans-serif',
  				'system-ui',
  				'-apple-system',
  				'BlinkMacSystemFont',
  				'Segoe UI',
  				'Roboto',
  				'Helvetica Neue',
  				'Arial',
  				'sans-serif'
  			],
  			mono: [
  				'JetBrains Mono',
  				'ui-monospace',
  				'SFMono-Regular',
  				'Menlo',
  				'Monaco',
  				'Consolas',
  				'Liberation Mono',
  				'Courier New',
  				'monospace'
  			]
  		},
  		boxShadow: {
  			gargash: '0 0 5px rgba(178, 32, 54, 0.5), 0 0 20px rgba(178, 32, 54, 0.2)',
  			'gargash-pulse': '0 0 10px rgba(178, 32, 54, 0.7), 0 0 30px rgba(178, 32, 54, 0.5), 0 0 50px rgba(178, 32, 54, 0.3)',
  			ai: '0 0 5px rgba(178, 32, 54, 0.5), 0 0 20px rgba(178, 32, 54, 0.2)',
  			'ai-pulse': '0 0 10px rgba(178, 32, 54, 0.7), 0 0 30px rgba(178, 32, 54, 0.5), 0 0 50px rgba(178, 32, 54, 0.3)',
  			neon: '0 0 5px rgba(0, 255, 255, 0.5), 0 0 20px rgba(0, 255, 255, 0.2)',
  			'neon-pink': '0 0 5px rgba(255, 0, 255, 0.5), 0 0 20px rgba(255, 0, 255, 0.2)',
  			'neon-green': '0 0 5px rgba(0, 255, 140, 0.5), 0 0 20px rgba(0, 255, 140, 0.2)'
  		},
  		animation: {
  			'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
  			glow: 'glow 2s ease-in-out infinite alternate',
  			'gargash-pulse': 'gargashPulse 2s ease-in-out infinite alternate',
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out'
  		},
  		keyframes: {
  			glow: {
  				'0%': {
  					boxShadow: '0 0 5px rgba(0, 255, 255, 0.5), 0 0 20px rgba(0, 255, 255, 0.2)'
  				},
  				'100%': {
  					boxShadow: '0 0 10px rgba(0, 255, 255, 0.8), 0 0 30px rgba(0, 255, 255, 0.5)'
  				}
  			},
  			gargashPulse: {
  				'0%': {
  					boxShadow: '0 0 5px rgba(178, 32, 54, 0.5), 0 0 20px rgba(178, 32, 54, 0.3)'
  				},
  				'100%': {
  					boxShadow: '0 0 10px rgba(178, 32, 54, 0.7), 0 0 30px rgba(178, 32, 54, 0.5), 0 0 50px rgba(178, 32, 54, 0.3)'
  				}
  			},
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: '0'
  				}
  			}
  		},
  		backdropBlur: {
  			xs: '2px'
  		},
  		borderRadius: {
  			xl: '1rem',
  			'2xl': '1.5rem',
  			'3xl': '2rem',
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
} 