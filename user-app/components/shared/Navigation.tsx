'use client'

import { Home, Search, Calendar, Users } from 'lucide-react'
import { usePathname, useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'

export function Navigation() {
  const pathname = usePathname()
  const router = useRouter()

  const navItems = [
    { icon: Home, label: 'Home', path: '/' },
    { icon: Search, label: 'Discover', path: '/discover' },
    { icon: Calendar, label: 'Bookings', path: '/bookings' },
    { icon: Users, label: 'Social', path: '/social' },
  ]

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-around py-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.path
            return (
              <button
                key={item.path}
                onClick={() => router.push(item.path)}
                className={cn(
                  'flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors',
                  isActive
                    ? 'text-purple-600 bg-purple-50'
                    : 'text-gray-600 hover:text-purple-600 hover:bg-gray-50'
                )}
              >
                <Icon className="w-5 h-5" />
                <span className="text-xs font-medium">{item.label}</span>
              </button>
            )
          })}
        </div>
      </div>
    </nav>
  )
}

