import { ref, watch } from 'vue'

export function useDebounce<T>(value: T, delay: number) {
  const debouncedValue = ref(value)
  
  watch(
    () => value,
    (newValue) => {
      const timeout = setTimeout(() => {
        debouncedValue.value = newValue
      }, delay)
      
      return () => clearTimeout(timeout)
    },
    { immediate: true }
  )
  
  return debouncedValue
}

export function useDebounceFunction<T extends (...args: any[]) => any>(
  func: T,
  delay: number
) {
  let timeoutId: ReturnType<typeof setTimeout>
  
  const debouncedFunction = (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func(...args), delay)
  }
  
  const cancel = () => {
    clearTimeout(timeoutId)
  }
  
  return { debouncedFunction, cancel }
}
