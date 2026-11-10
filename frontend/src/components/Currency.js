
export default function Currency({ amount, currency = 'USD' }) {
  if (amount === null || amount === undefined || amount === '') {
    return '-';
  }

  const formatter = new Intl.NumberFormat(
    'en-US', { style: 'currency', currency: currency || 'USD', currencyDisplay: 'narrowSymbol'}
  );
  return formatter.format(amount);
}
