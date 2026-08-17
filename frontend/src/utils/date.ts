export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return '--'
  }

  return value.replace('T', ' ').slice(0, 19)
}
