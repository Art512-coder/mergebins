declare global {
  interface Window {
    addToast?: (toast: {
      type: 'success' | 'error' | 'info'
      title: string
      message?: string
      duration?: number
    }) => void
    openLogin?: () => void
    openCryptoChecker?: () => void
    currentUser?: any
  }
}

export {}
