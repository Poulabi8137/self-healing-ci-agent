import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export function useKeyboardShortcuts(onOpenPalette: () => void) {
  const navigate = useNavigate()

  useEffect(() => {
    let seq = ''
    let timer: ReturnType<typeof setTimeout>

    function handleKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable

      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        onOpenPalette()
        return
      }

      if (isInput) return

      const key = e.key.toLowerCase()

      if (key === 'g') {
        seq = 'g'
        clearTimeout(timer)
        timer = setTimeout(() => { seq = '' }, 500)
        return
      }

      if (seq === 'g') {
        seq = ''
        clearTimeout(timer)
        switch (key) {
          case 'd': navigate('/dashboard'); break
          case 'a': navigate('/analysis'); break
          case 'v': navigate('/validation'); break
          case 'r': navigate('/review'); break
          case 't': navigate('/tasks'); break
        }
      }
    }

    window.addEventListener('keydown', handleKey)
    return () => {
      window.removeEventListener('keydown', handleKey)
      clearTimeout(timer)
    }
  }, [navigate, onOpenPalette])
}
