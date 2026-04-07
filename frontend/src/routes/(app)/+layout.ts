// Disable SSR for authenticated app routes.
// Auth state is purely client-side (checked via onMount → checkSession),
// so SSR always renders a loading spinner. Skipping SSR avoids hydration
// failures on mobile that leave users stuck on an infinite spinner.
export const ssr = false;
