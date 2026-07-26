export function createSessionId() {
  return `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

export function debounce(fn, delay = 250) {
  let timer
  return (...args) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}
