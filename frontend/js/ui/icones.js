// Ícones SVG usados pelos componentes e pelas telas.

const paths = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  users:
    '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m20 0v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/><circle cx="9" cy="7" r="4"/>',
  car: '<path d="m5 7 2-4h10l2 4m-16 3 2-3h14l2 3v8H3Zm2 8v3m14-3v3M3 12h18"/><path d="M6 15h2m8 0h2"/>',
  parking: '<rect x="3" y="3" width="18" height="18" rx="4"/><path d="M9 17V7h4a3 3 0 0 1 0 6H9"/>',
  calendar:
    '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18m-13 4h2m4 0h2"/>',
  receipt: '<path d="M5 3h14v19l-3-2-4 2-4-2-3 2ZM9 7h6m-6 4h6m-6 4h3"/>',
  sliders:
    '<path d="M4 6h6m4 0h6M4 12h12m4 0h0M4 18h2m4 0h10"/><circle cx="12" cy="6" r="2"/><circle cx="18" cy="12" r="2"/><circle cx="8" cy="18" r="2"/>',
  shield: '<path d="m12 3 8 4v6c0 5-8 9-8 9s-8-4-8-9V7Zm-4 9 3 3 5-6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  arrow: '<path d="M5 12h14m-6-6 6 6-6 6"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  check: '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
  search: '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>',
  refresh: '<path d="M20 7v5h-5M4 17v-5h5m-4-3a7 7 0 0 1 12-5l3 3M4 17l3 3a7 7 0 0 0 12-5"/>',
  lock: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 4v3"/>',
};
const icon = (name) =>
  /* HTML */ `<svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    ${paths[name] || paths.grid}
  </svg>`;

export { icon };
