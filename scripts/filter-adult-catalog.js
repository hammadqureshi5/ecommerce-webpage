/**
 * Strip boys/girls from products.js catalog (Men + Women only).
 */
const fs = require("fs");
const path = require("path");
const file = path.join(__dirname, "..", "js", "products.js");
let src = fs.readFileSync(file, "utf8");

// Evaluate catalog globals in a sandbox
const sandbox = {};
const vm = require("vm");
vm.runInNewContext(src + "\n;this.HERO_SLIDES=HERO_SLIDES;this.MEGA_MENU=MEGA_MENU;this.GENDERS=GENDERS;this.FEATURED_CATEGORIES=FEATURED_CATEGORIES;this.PRODUCTS=PRODUCTS;", sandbox);

const HERO_SLIDES = sandbox.HERO_SLIDES.filter((s) =>
  ["#section-men", "#section-women"].includes(s.link)
);
const MEGA_MENU = {
  male: sandbox.MEGA_MENU.male,
  female: sandbox.MEGA_MENU.female,
};
const GENDERS = sandbox.GENDERS.filter((g) => g.id === "male" || g.id === "female");
const FEATURED_CATEGORIES = {
  male: sandbox.FEATURED_CATEGORIES.male,
  female: sandbox.FEATURED_CATEGORIES.female,
};
const PRODUCTS = sandbox.PRODUCTS.filter(
  (p) => p.gender === "male" || p.gender === "female"
);

function dump(v) {
  return JSON.stringify(v, null, 2);
}

const helpers = src.slice(src.indexOf("function getProduct"));
const out = `// Auto-generated from breakout.com.pk scrape — real CDN images (Men + Women only)
const HERO_SLIDES = ${dump(HERO_SLIDES)};

const MEGA_MENU = ${dump(MEGA_MENU)};

const GENDERS = ${dump(GENDERS)};

const FEATURED_CATEGORIES = ${dump(FEATURED_CATEGORIES)};

const PRODUCTS = ${dump(PRODUCTS)};

${helpers}`;

fs.writeFileSync(file, out);
console.log("Kept products:", PRODUCTS.length, "genders:", GENDERS.map((g) => g.id).join(","));
