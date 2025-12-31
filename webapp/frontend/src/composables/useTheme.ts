import { ref, computed } from 'vue'

export function useTheme() {
  const theme = ref<'light' | 'dark'>('dark')
  
  const isDark = computed(() => theme.value === 'dark')
  const isLight = computed(() => theme.value === 'light')
  
  const toggleTheme = () => {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    updateTheme()
  }
  
  const setTheme = (newTheme: 'light' | 'dark') => {
    theme.value = newTheme
    updateTheme()
  }
  
  const updateTheme = () => {
    const root = document.documentElement
    
    if (theme.value === 'dark') {
      root.classList.add('dark')
      root.classList.remove('light')
    } else {
      root.classList.add('light')
      root.classList.remove('dark')
    }
    
    // Save to localStorage
    localStorage.setItem('theme', theme.value)
  }
  
  const initTheme = () => {
    // Check localStorage first
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    
    if (savedTheme) {
      theme.value = savedTheme
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      theme.value = prefersDark ? 'dark' : 'light'
    }
    
    updateTheme()
  }
  
  // Listen for system theme changes
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  mediaQuery.addEventListener('change', (e) => {
    // Only update if user hasn't manually set a theme
    if (!localStorage.getItem('theme')) {
      theme.value = e.matches ? 'dark' : 'light'
      updateTheme()
    }
  })
  
  return {
    theme,
    isDark,
    isLight,
    toggleTheme,
    setTheme,
    initTheme,
  }
}
