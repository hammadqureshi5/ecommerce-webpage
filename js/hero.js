/**
 * Hero banner slideshow — Breakout.com.pk style.
 */
(function () {
  function init() {
    const main = document.getElementById("main");
    if (!main || typeof HERO_SLIDES === "undefined" || !HERO_SLIDES.length) return;

    const section = document.createElement("section");
    section.className = "bo-hero";
    section.setAttribute("aria-label", "Featured collections");

    section.innerHTML = `
      <div class="bo-hero__slides" id="hero-slides"></div>
      <button type="button" class="bo-hero__nav bo-hero__nav--prev" aria-label="Previous slide">&lsaquo;</button>
      <button type="button" class="bo-hero__nav bo-hero__nav--next" aria-label="Next slide">&rsaquo;</button>
      <div class="bo-hero__dots" id="hero-dots"></div>
    `;

    main.insertBefore(section, main.firstChild);

    const slidesEl = section.querySelector("#hero-slides");
    const dotsEl = section.querySelector("#hero-dots");
    let index = 0;
    let timer;

    HERO_SLIDES.forEach((slide, i) => {
      const el = document.createElement("a");
      el.href = slide.link || "#";
      el.className = "bo-hero__slide" + (i === 0 ? " active" : "");

      const picture = document.createElement("picture");
      const source = document.createElement("source");
      source.media = "(max-width: 749px)";
      source.srcset = slide.mobile;
      const img = document.createElement("img");
      img.src = slide.desktop;
      img.alt = "Breakout collection banner " + (i + 1);
      img.loading = i === 0 ? "eager" : "lazy";
      img.referrerPolicy = "no-referrer";
      picture.appendChild(source);
      picture.appendChild(img);
      el.appendChild(picture);

      el.addEventListener("click", (e) => {
        if (slide.link && slide.link.startsWith("#")) {
          e.preventDefault();
          document.querySelector(slide.link)?.scrollIntoView({ behavior: "smooth" });
        }
      });
      slidesEl.appendChild(el);

      const dot = document.createElement("button");
      dot.type = "button";
      dot.className = "bo-hero__dot" + (i === 0 ? " active" : "");
      dot.setAttribute("aria-label", "Go to slide " + (i + 1));
      dot.addEventListener("click", () => goTo(i));
      dotsEl.appendChild(dot);
    });

    function goTo(i) {
      index = (i + HERO_SLIDES.length) % HERO_SLIDES.length;
      slidesEl.querySelectorAll(".bo-hero__slide").forEach((s, j) => {
        s.classList.toggle("active", j === index);
      });
      dotsEl.querySelectorAll(".bo-hero__dot").forEach((d, j) => {
        d.classList.toggle("active", j === index);
      });
    }

    function next() {
      goTo(index + 1);
    }
    function prev() {
      goTo(index - 1);
    }

    section.querySelector(".bo-hero__nav--next").addEventListener("click", next);
    section.querySelector(".bo-hero__nav--prev").addEventListener("click", prev);

    function startAutoplay() {
      stopAutoplay();
      timer = setInterval(next, 5000);
    }
    function stopAutoplay() {
      clearInterval(timer);
    }

    section.addEventListener("mouseenter", stopAutoplay);
    section.addEventListener("mouseleave", startAutoplay);
    startAutoplay();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
