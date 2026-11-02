/**
 * Veyra Hash Router
 * Manages view switching between Dashboard, Goals, Planner, and Execution.
 */

class Router {
  constructor(routes, defaultRoute = 'dashboard') {
    this.routes = routes;
    this.defaultRoute = defaultRoute;
    this.currentRoute = null;

    window.addEventListener('hashchange', () => this.handleHashChange());
  }

  init() {
    this.handleHashChange();
  }

  handleHashChange() {
    const rawHash = window.location.hash.replace(/^#\/?/, '').trim();
    const route = this.routes[rawHash] ? rawHash : this.defaultRoute;
    this.navigate(route, false);
  }

  navigate(routeKey, updateHash = true) {
    if (this.currentRoute === routeKey) return;
    this.currentRoute = routeKey;

    if (updateHash) {
      window.location.hash = `#${routeKey}`;
    }

    // Toggle navigation links
    document.querySelectorAll('.nav-link').forEach(link => {
      const target = link.getAttribute('data-view');
      link.classList.toggle('active', target === routeKey);
    });

    // Toggle view sections
    document.querySelectorAll('.view-section').forEach(section => {
      const sectionKey = section.getAttribute('data-view');
      section.classList.toggle('active', sectionKey === routeKey);
    });

    // Invoke route handler if defined
    if (this.routes[routeKey]) {
      this.routes[routeKey]();
    }
  }
}

export function initRouter(routeHandlers) {
  const router = new Router(routeHandlers, 'dashboard');
  router.init();
  return router;
}
