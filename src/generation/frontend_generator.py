"""
Frontend Generator - React + TypeScript
Generates complete React frontend with routing, state management, and API integration
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class UIPage:
    """Represents a UI page/route"""
    name: str
    route: str
    description: str
    components: List[str]
    requires_auth: bool = True
    layout: str = 'default'


@dataclass
class Component:
    """Represents a React component"""
    name: str
    type: str  # 'page', 'component', 'layout'
    props: List[Dict[str, str]]
    state_vars: List[Dict[str, str]]
    api_calls: List[str]
    children: List[str]


class FrontendGenerator:
    """
    Generates complete React frontend application
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ui_framework = config.get('ui_framework', 'tailwindcss')
        self.state_management = config.get('state_management', 'zustand')

    async def generate(
        self,
        ui_pages: List[Dict[str, Any]],
        features: List[Dict[str, Any]],
        backend_code: Dict[str, str],
        template: Any
    ) -> Dict[str, str]:
        """
        Generates complete frontend code
        """
        frontend_files = {}

        # 1. Generate package.json
        frontend_files['frontend/package.json'] = self._generate_package_json()

        # 2. Generate Next.js/React configuration
        frontend_files['frontend/next.config.js'] = self._generate_next_config()
        frontend_files['frontend/tsconfig.json'] = self._generate_tsconfig()
        frontend_files['frontend/tailwind.config.js'] = self._generate_tailwind_config()

        # 3. Generate main app structure
        frontend_files['frontend/src/app/layout.tsx'] = self._generate_root_layout()
        frontend_files['frontend/src/app/page.tsx'] = self._generate_home_page()

        # 4. Generate pages for each route
        for page in ui_pages:
            page_files = self._generate_page(page)
            frontend_files.update(page_files)

        # 5. Generate components
        frontend_files.update(self._generate_common_components())

        # 6. Generate API integration layer
        frontend_files.update(self._generate_api_layer(backend_code))

        # 7. Generate state management
        frontend_files.update(self._generate_state_management())

        # 8. Generate authentication
        frontend_files.update(self._generate_auth_components())

        # 9. Generate utilities and hooks
        frontend_files.update(self._generate_utils_and_hooks())

        # 10. Generate styles
        frontend_files['frontend/src/app/globals.css'] = self._generate_global_styles()

        # 11. Generate environment config
        frontend_files['frontend/.env.local.example'] = self._generate_env_example()

        return frontend_files

    def _generate_package_json(self) -> str:
        """Generates package.json for Next.js + TypeScript + Tailwind"""
        return """{
  "name": "verifimind-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.2.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@types/node": "^20.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.31",
    "zustand": "^4.4.0",
    "axios": "^1.5.0",
    "react-hook-form": "^7.47.0",
    "zod": "^3.22.0",
    "@hookform/resolvers": "^3.3.0",
    "date-fns": "^2.30.0",
    "clsx": "^2.0.0",
    "lucide-react": "^0.290.0"
  },
  "devDependencies": {
    "eslint": "^8.0.0",
    "eslint-config-next": "^14.0.0",
    "@tailwindcss/forms": "^0.5.7",
    "@tailwindcss/typography": "^0.5.10"
  }
}
"""

    def _generate_next_config(self) -> str:
        """Generates Next.js configuration"""
        return """/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['localhost'],
  },
  env: {
    API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
}

module.exports = nextConfig
"""

    def _generate_tsconfig(self) -> str:
        """Generates TypeScript configuration"""
        return """{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/lib/*": ["./src/lib/*"],
      "@/hooks/*": ["./src/hooks/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
"""

    def _generate_tailwind_config(self) -> str:
        """Generates Tailwind CSS configuration"""
        return """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
"""

    def _generate_root_layout(self) -> str:
        """Generates root layout component"""
        return """import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Providers } from '@/components/Providers'
import { Navbar } from '@/components/Navbar'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'VerifiMind App',
  description: 'Generated by VerifiMind',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen bg-gray-50">
            <Navbar />
            <main className="container mx-auto px-4 py-8">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  )
}
"""

    def _generate_home_page(self) -> str:
        """Generates home page"""
        return """'use client'

import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/Button'

export default function HomePage() {
  const router = useRouter()
  const { user, isAuthenticated } = useAuth()

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to Your App
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Generated by VerifiMind - Start building amazing experiences
        </p>

        {!isAuthenticated ? (
          <div className="space-x-4">
            <Button onClick={() => router.push('/login')}>
              Sign In
            </Button>
            <Button variant="outline" onClick={() => router.push('/register')}>
              Sign Up
            </Button>
          </div>
        ) : (
          <div>
            <p className="text-lg mb-4">Welcome back, {user?.name}!</p>
            <Button onClick={() => router.push('/dashboard')}>
              Go to Dashboard
            </Button>
          </div>
        )}
      </div>

      <div className="grid md:grid-cols-3 gap-6 mt-12">
        <FeatureCard
          title="Feature 1"
          description="Description of your first feature"
          icon="🚀"
        />
        <FeatureCard
          title="Feature 2"
          description="Description of your second feature"
          icon="⚡"
        />
        <FeatureCard
          title="Feature 3"
          description="Description of your third feature"
          icon="🎯"
        />
      </div>
    </div>
  )
}

function FeatureCard({ title, description, icon }: {
  title: string
  description: string
  icon: string
}) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="text-3xl mb-3">{icon}</div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}
"""

    def _generate_page(self, page: Dict[str, Any]) -> Dict[str, str]:
        """Generates a page component"""
        page_name = page['name']
        route = page['route']
        components = page.get('components', [])

        # Convert route to Next.js app directory structure
        # e.g., /dashboard -> frontend/src/app/dashboard/page.tsx
        route_path = route.strip('/') or 'home'
        page_path = f"frontend/src/app/{route_path}/page.tsx"

        page_code = f"""'use client'

import {{ useState, useEffect }} from 'react'
import {{ useRouter }} from 'next/navigation'
import {{ useAuth }} from '@/hooks/useAuth'

export default function {page_name}Page() {{
  const router = useRouter()
  const {{ user, isAuthenticated }} = useAuth()
  const [loading, setLoading] = useState(false)

  useEffect(() => {{
    // Check authentication
    if (!isAuthenticated) {{
      router.push('/login')
    }}
  }}, [isAuthenticated, router])

  if (!isAuthenticated) {{
    return <div>Loading...</div>
  }}

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{page_name}</h1>
        <p className="text-gray-600 mt-2">{page.get('description', 'Page description')}</p>
      </div>

      <div className="space-y-6">
        {self._generate_page_components(components)}
      </div>
    </div>
  )
}}
"""

        return {page_path: page_code}

    def _generate_page_components(self, components: List[str]) -> str:
        """Generates component placeholders for a page"""
        if not components:
            return """
        {/* Add your components here */}
        <div className="bg-white p-6 rounded-lg shadow">
          <p>Content goes here</p>
        </div>
"""

        component_code = ""
        for component in components:
            component_code += f"""
        <{component} />
"""
        return component_code

    def _generate_common_components(self) -> Dict[str, str]:
        """Generates common UI components"""
        return {
            # Providers wrapper
            'frontend/src/components/Providers.tsx': self._generate_providers(),

            # Navbar
            'frontend/src/components/Navbar.tsx': self._generate_navbar(),

            # Button component
            'frontend/src/components/ui/Button.tsx': self._generate_button(),

            # Input component
            'frontend/src/components/ui/Input.tsx': self._generate_input(),

            # Card component
            'frontend/src/components/ui/Card.tsx': self._generate_card(),

            # Loading spinner
            'frontend/src/components/ui/Spinner.tsx': self._generate_spinner(),
        }

    def _generate_providers(self) -> str:
        """Generates Providers wrapper component"""
        return """'use client'

import { ReactNode } from 'react'
import { AuthProvider } from '@/hooks/useAuth'

export function Providers({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      {children}
    </AuthProvider>
  )
}
"""

    def _generate_navbar(self) -> str:
        """Generates Navbar component"""
        return """'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/Button'

export function Navbar() {
  const router = useRouter()
  const { user, isAuthenticated, logout } = useAuth()

  const handleLogout = async () => {
    await logout()
    router.push('/login')
  }

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="text-xl font-bold text-gray-900">
            VerifiMind App
          </Link>

          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <Link href="/dashboard" className="text-gray-700 hover:text-gray-900">
                  Dashboard
                </Link>
                <Link href="/profile" className="text-gray-700 hover:text-gray-900">
                  Profile
                </Link>
                <span className="text-gray-600">{user?.name}</span>
                <Button variant="outline" size="sm" onClick={handleLogout}>
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="outline" size="sm">Sign In</Button>
                </Link>
                <Link href="/register">
                  <Button size="sm">Sign Up</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
"""

    def _generate_button(self) -> str:
        """Generates reusable Button component"""
        return """import { ButtonHTMLAttributes, ReactNode } from 'react'
import { clsx } from 'clsx'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: 'primary' | 'secondary' | 'outline' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  className,
  disabled,
  ...props
}: ButtonProps) {
  const baseClasses = 'font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2'

  const variantClasses = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
    secondary: 'bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500',
    outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-primary-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  }

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  }

  return (
    <button
      className={clsx(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        (disabled || isLoading) && 'opacity-50 cursor-not-allowed',
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? 'Loading...' : children}
    </button>
  )
}
"""

    def _generate_input(self) -> str:
        """Generates reusable Input component"""
        return """import { InputHTMLAttributes, forwardRef } from 'react'
import { clsx } from 'clsx'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, className, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={clsx(
            'w-full px-3 py-2 border rounded-lg shadow-sm',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            error
              ? 'border-red-300 text-red-900 placeholder-red-300'
              : 'border-gray-300',
            className
          )}
          {...props}
        />
        {error && (
          <p className="mt-1 text-sm text-red-600">{error}</p>
        )}
        {helperText && !error && (
          <p className="mt-1 text-sm text-gray-500">{helperText}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'
"""

    def _generate_card(self) -> str:
        """Generates Card component"""
        return """import { ReactNode } from 'react'
import { clsx } from 'clsx'

interface CardProps {
  children: ReactNode
  className?: string
  title?: string
  footer?: ReactNode
}

export function Card({ children, className, title, footer }: CardProps) {
  return (
    <div className={clsx('bg-white rounded-lg shadow border border-gray-200', className)}>
      {title && (
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
      )}
      <div className="px-6 py-4">
        {children}
      </div>
      {footer && (
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          {footer}
        </div>
      )}
    </div>
  )
}
"""

    def _generate_spinner(self) -> str:
        """Generates Loading Spinner component"""
        return """export function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }

  return (
    <div className="flex justify-center items-center">
      <div className={`${sizes[size]} border-4 border-gray-200 border-t-primary-600 rounded-full animate-spin`}></div>
    </div>
  )
}
"""

    def _generate_api_layer(self, backend_code: Dict[str, str]) -> Dict[str, str]:
        """Generates API integration layer"""
        return {
            'frontend/src/lib/api.ts': """import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api'

// Create axios instance
export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API methods
export const apiClient = {
  // Auth
  auth: {
    login: (email: string, password: string) =>
      api.post('/auth/login', { email, password }),
    register: (data: any) =>
      api.post('/auth/register', data),
    logout: () =>
      api.post('/auth/logout'),
    me: () =>
      api.get('/auth/me'),
  },

  // Generic CRUD
  get: (endpoint: string) => api.get(endpoint),
  post: (endpoint: string, data: any) => api.post(endpoint, data),
  put: (endpoint: string, data: any) => api.put(endpoint, data),
  delete: (endpoint: string) => api.delete(endpoint),
}
""",
        }

    def _generate_state_management(self) -> Dict[str, str]:
        """Generates Zustand store for state management"""
        return {
            'frontend/src/store/index.ts': """import { create } from 'zustand'

interface AppState {
  // Add your global state here
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void

  // Example: notifications
  notifications: Array<{id: string, message: string, type: string}>
  addNotification: (notification: Omit<AppState['notifications'][0], 'id'>) => void
  removeNotification: (id: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: false,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  notifications: [],
  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        { ...notification, id: Math.random().toString() },
      ],
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}))
""",
        }

    def _generate_auth_components(self) -> Dict[str, str]:
        """Generates authentication components"""
        return {
            # Auth hook
            'frontend/src/hooks/useAuth.tsx': """'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { apiClient } from '@/lib/api'

interface User {
  id: string
  email: string
  name: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: any) => Promise<void>
  logout: () => Promise<void>
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('token')
      if (token) {
        const response = await apiClient.auth.me()
        setUser(response.data)
      }
    } catch (error) {
      localStorage.removeItem('token')
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    const response = await apiClient.auth.login(email, password)
    const { token, user } = response.data
    localStorage.setItem('token', token)
    setUser(user)
  }

  const register = async (data: any) => {
    const response = await apiClient.auth.register(data)
    const { token, user } = response.data
    localStorage.setItem('token', token)
    setUser(user)
  }

  const logout = async () => {
    try {
      await apiClient.auth.logout()
    } finally {
      localStorage.removeItem('token')
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
""",

            # Login page
            'frontend/src/app/login/page.tsx': """'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import Link from 'next/link'

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(email, password)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.error || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
      <Card className="w-full max-w-md">
        <div className="mb-6 text-center">
          <h2 className="text-3xl font-bold text-gray-900">Sign In</h2>
          <p className="text-gray-600 mt-2">Welcome back!</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="email"
            label="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />

          <Input
            type="password"
            label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />

          {error && (
            <div className="text-red-600 text-sm">{error}</div>
          )}

          <Button
            type="submit"
            className="w-full"
            isLoading={loading}
          >
            Sign In
          </Button>
        </form>

        <div className="mt-6 text-center text-sm">
          <span className="text-gray-600">Don't have an account? </span>
          <Link href="/register" className="text-primary-600 hover:text-primary-700 font-medium">
            Sign up
          </Link>
        </div>
      </Card>
    </div>
  )
}
""",

            # Register page
            'frontend/src/app/register/page.tsx': """'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import Link from 'next/link'

export default function RegisterPage() {
  const router = useRouter()
  const { register } = useAuth()
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return
    }

    setLoading(true)

    try {
      await register({
        name: formData.name,
        email: formData.email,
        password: formData.password,
      })
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.error || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
      <Card className="w-full max-w-md">
        <div className="mb-6 text-center">
          <h2 className="text-3xl font-bold text-gray-900">Sign Up</h2>
          <p className="text-gray-600 mt-2">Create your account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="text"
            name="name"
            label="Full Name"
            value={formData.name}
            onChange={handleChange}
            placeholder="John Doe"
            required
          />

          <Input
            type="email"
            name="email"
            label="Email"
            value={formData.email}
            onChange={handleChange}
            placeholder="you@example.com"
            required
          />

          <Input
            type="password"
            name="password"
            label="Password"
            value={formData.password}
            onChange={handleChange}
            placeholder="••••••••"
            required
          />

          <Input
            type="password"
            name="confirmPassword"
            label="Confirm Password"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="••••••••"
            required
          />

          {error && (
            <div className="text-red-600 text-sm">{error}</div>
          )}

          <Button
            type="submit"
            className="w-full"
            isLoading={loading}
          >
            Sign Up
          </Button>
        </form>

        <div className="mt-6 text-center text-sm">
          <span className="text-gray-600">Already have an account? </span>
          <Link href="/login" className="text-primary-600 hover:text-primary-700 font-medium">
            Sign in
          </Link>
        </div>
      </Card>
    </div>
  )
}
""",
        }

    def _generate_utils_and_hooks(self) -> Dict[str, str]:
        """Generates utility functions and custom hooks"""
        return {
            'frontend/src/lib/utils.ts': """import { type ClassValue, clsx } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatDate(date: string | Date) {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

export function formatCurrency(amount: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount)
}
""",

            'frontend/src/hooks/useApi.ts': """import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'

export function useApi<T>(endpoint: string) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    fetchData()
  }, [endpoint])

  const fetchData = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get(endpoint)
      setData(response.data)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }

  const refetch = () => fetchData()

  return { data, loading, error, refetch }
}
""",
        }

    def _generate_global_styles(self) -> str:
        """Generates global CSS with Tailwind"""
        return """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
  }

  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground;
  }
}

@layer utilities {
  .animate-spin {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
}
"""

    def _generate_env_example(self) -> str:
        """Generates .env.local.example"""
        return """# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:3000/api

# Application
NEXT_PUBLIC_APP_NAME=VerifiMind App
"""
