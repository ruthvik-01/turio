export type Theme = "light" | "dark";

export function resolveTheme(saved: unknown, prefersDark: boolean): Theme {
  return saved === "light" || saved === "dark" ? saved : prefersDark ? "dark" : "light";
}

export const THEME_BOOTSTRAP = `(()=>{let t;try{t=localStorage.getItem('turio-theme')}catch{}
if(t==='light'||t==='dark')document.documentElement.dataset.theme=t;})();`;

export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem("turio-theme", theme); } catch {}
}
