type ClassDictionary = Record<string, boolean | string | number | undefined | null>
type ClassValue = string | number | boolean | undefined | null | ClassDictionary | ClassValue[]

const toValue = (value: ClassValue): string[] => {
  if (!value) return []
  if (typeof value === 'string' || typeof value === 'number') return [String(value)]
  if (Array.isArray(value)) {
    return value.map(toValue).flat()
  }
  return Object.entries(value)
    .filter(([, truthy]) => Boolean(truthy))
    .map(([key]) => key)
}

export function cn(...values: ClassValue[]) {
  return values.map(toValue).flat().filter(Boolean).join(' ')
}

