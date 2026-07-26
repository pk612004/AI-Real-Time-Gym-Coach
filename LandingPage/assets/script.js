document.addEventListener("DOMContentLoaded", () => {
  initLoader();
  initStickyNavShadow();
  initHamburgerMenu();
  initScrollReveal();
  initScrollProgress();
  initStatsCounter();
});
function initLoader() {
  const loader = document.getElementById("loader");
  if (!loader) return;

  const hide = () => {
    loader.classList.add("hidden");
    document.body.classList.remove("loading");
    setTimeout(() => loader.remove(), 600);
  };
  window.addEventListener("load", () => {
    setTimeout(hide, 1000);
  });

  setTimeout(hide, 3500);
}
function initStickyNavShadow() {
  const nav = document.querySelector(".nav");
  if (!nav) return;

  const toggleScrolled = () => {
    if (window.scrollY > 20) {
      nav.classList.add("scrolled");
    } else {
      nav.classList.remove("scrolled");
    }
  };
  toggleScrolled();
  window.addEventListener("scroll", toggleScrolled, { passive: true });
}
function initHamburgerMenu() {
  const hamburger = document.querySelector(".nav-hamburger");
  const navLinks = document.querySelector(".nav-links");
  if (!hamburger || !navLinks) return;

  const closeMenu = () => {
    hamburger.classList.remove("open");
    navLinks.classList.remove("open");
  };
  hamburger.addEventListener("click", () => {
    hamburger.classList.toggle("open");
    navLinks.classList.toggle("open");
  });
  navLinks.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeMenu);
  });
  window.addEventListener("resize", () => {
    if (window.innerWidth > 768) {
      closeMenu();
    }
  });
}
function initScrollReveal() {
  const selectors = [
    ".step-card",
    ".feature-card",
    ".img-card",
    ".exercise-card",
    ".stat-card",
    ".tech-card",
    ".feature",
  ];
  const targets = document.querySelectorAll(selectors.join(","));
  if (!targets.length) return;
  targets.forEach((el) => el.classList.add("reveal"));
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.15,
      rootMargin: "0px 0px -60px 0px",
    }
  );
  targets.forEach((el, index) => {
    el.style.transitionDelay = `${(index % 6) * 0.08}s`;
    observer.observe(el);
  });
}
function initScrollProgress() {
  const bar = document.getElementById("scroll-progress");
  if (!bar) return;
  const update = () => {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const pct = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
    bar.style.width = pct + "%";
  };

  update();
  window.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
}
function initStatsCounter() {
  const statEls = document.querySelectorAll(".stat-val[data-count]");
  if (!statEls.length) return;
  const animateCount = (el) => {
    const target = parseInt(el.getAttribute("data-count"), 10);
    const prefix = el.getAttribute("data-prefix") || "";
    const suffix = el.getAttribute("data-suffix") || "";
    const duration = 1200;
    const startTime = performance.now();
    const step = (now) => {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      const value = Math.floor(eased * target);
      el.textContent = `${prefix}${value}${suffix}`;
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        el.textContent = `${prefix}${target}${suffix}`;
      }
    };
    requestAnimationFrame(step);
  };
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.4 }
  );
  statEls.forEach((el) => observer.observe(el));
}