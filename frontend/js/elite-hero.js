/**
 * Auto-sliding hero carousel — left headline + right badge per slide.
 */
const EliteHero = (function () {
  let index = 0;
  let timer = null;
  const INTERVAL_MS = 5500;

  function field(slide, key, fallback) {
    const val = slide?.[key];
    return val != null && String(val).trim() !== "" ? val : fallback;
  }

  function slideImage(slide) {
    const mobile = window.matchMedia("(max-width: 767px)").matches;
    const url = mobile && slide.mobile ? slide.mobile : slide.desktop;
    return url || "https://www.breakout.com.pk/cdn/shop/files/Men_Main_jpg_68c3ab17-7192-4bf0-a758-e73897e8869a.jpg?v=1786734994&width=2560";
  }

  function renderSlides() {
    const track = document.getElementById("hero-track");
    const slides = typeof HERO_SLIDES !== "undefined" ? HERO_SLIDES : [];
    if (!track || !slides.length) return;

    track.innerHTML = slides
      .map(
        (slide, i) => `
      <article class="hero-slide absolute inset-0 transition-opacity duration-700 ease-in-out ${i === 0 ? "opacity-100 z-10" : "opacity-0 z-0"}" data-index="${i}" aria-hidden="${i !== 0}">
        <div class="absolute inset-0 bg-cover bg-center transition-transform duration-[1200ms] scale-100" style="background-image:url('${slideImage(slide)}')"></div>
        <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-black/15 to-black/10"></div>
        <div class="absolute inset-0 flex items-end justify-between p-8 lg:p-14 pb-12 lg:pb-16">
          <div class="max-w-xl text-left">
            <p class="font-label-md text-label-md text-white/90 uppercase tracking-[0.2em] mb-4">${field(slide, "label", "New Collection")}</p>
            <h2 class="font-display-lg text-headline-lg-mobile lg:text-display-lg text-white leading-tight mb-8 uppercase">${field(slide, "headline", "Elevate Your Everyday Wardrobe")}</h2>
            <a href="${field(slide, "link", "#trending")}" class="inline-flex items-center justify-center bg-white text-primary font-label-lg uppercase tracking-wide py-4 px-10 rounded-full hover:bg-surface-container transition-colors">${field(slide, "cta", "Shop Now")}</a>
          </div>
          <p class="hidden md:block font-display-lg text-[clamp(2rem,5vw,4.5rem)] text-white uppercase tracking-tight text-right max-w-md leading-none self-center">${field(slide, "badge", "Modern Elegance")}</p>
        </div>
      </article>`
      )
      .join("");

    const dots = document.getElementById("hero-dots");
    if (dots) {
      dots.innerHTML = slides
        .map(
          (_, i) =>
            `<button type="button" class="hero-dot w-2 h-2 rounded-full transition-all duration-300 ${i === 0 ? "bg-white w-6" : "bg-white/40"}" data-go="${i}" aria-label="Go to slide ${i + 1}"></button>`
        )
        .join("");
      dots.querySelectorAll(".hero-dot").forEach((btn) => {
        btn.addEventListener("click", () => goTo(Number(btn.dataset.go), true));
      });
    }
  }

  function goTo(next, userTriggered) {
    const slides = document.querySelectorAll(".hero-slide");
    const dots = document.querySelectorAll(".hero-dot");
    if (!slides.length) return;

    slides[index]?.classList.replace("opacity-100", "opacity-0");
    slides[index]?.classList.replace("z-10", "z-0");
    slides[index]?.setAttribute("aria-hidden", "true");
    dots[index]?.classList.remove("bg-white", "w-6");
    dots[index]?.classList.add("bg-white/40");

    index = (next + slides.length) % slides.length;

    slides[index]?.classList.replace("opacity-0", "opacity-100");
    slides[index]?.classList.replace("z-0", "z-10");
    slides[index]?.setAttribute("aria-hidden", "false");
    dots[index]?.classList.add("bg-white", "w-6");
    dots[index]?.classList.remove("bg-white/40");

    if (userTriggered) restartTimer();
  }

  function next() {
    goTo(index + 1, false);
  }

  function restartTimer() {
    clearInterval(timer);
    timer = setInterval(next, INTERVAL_MS);
  }

  function init() {
    renderSlides();
    restartTimer();

    const section = document.getElementById("hero-carousel");
    section?.addEventListener("mouseenter", () => clearInterval(timer));
    section?.addEventListener("mouseleave", restartTimer);
  }

  document.addEventListener("DOMContentLoaded", init);
  return { goTo, next };
})();
