export function makeLinePath(data, width, height, padX = 14, padY = 10) {
  if (!data || data.length === 0) return "";

  const safeWidth = Math.max(width - padX * 2, 1);
  const safeHeight = Math.max(height - padY * 2, 1);

  const values = data.map((d) => d.vpin).filter((v) => typeof v === "number" && !Number.isNaN(v));
  if (values.length === 0) return "";

  const min = Math.min(0.3, ...values);
  const max = Math.max(0.9, ...values);
  const range = Math.max(max - min, 0.01);

  return data
    .map((point, index) => {
      const x = padX + (index / Math.max(data.length - 1, 1)) * safeWidth;
      const y = padY + ((max - point.vpin) / range) * safeHeight;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export function yForThreshold(threshold, width, height, padX = 14, padY = 10) {
  const min = 0.3;
  const max = 0.9;
  const safeHeight = Math.max(height - padY * 2, 1);
  const range = Math.max(max - min, 0.01);

  return padY + ((max - threshold) / range) * safeHeight;
}
