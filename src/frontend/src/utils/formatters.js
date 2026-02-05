export const formatCurrency = (amount, currency = 'USD') => {
  if (amount === null || amount === undefined || isNaN(amount)) return '$0.00'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(amount)
}

export const formatPercent = (value) => {
  if (value === null || value === undefined || isNaN(value)) return '0.00%'
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

export const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export const getChangeColor = (value) => {
  if (value > 0) return 'text-success'
  if (value < 0) return 'text-danger'
  return 'text-gray-600'
}