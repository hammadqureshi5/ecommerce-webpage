"""Generate js/breakout-catalog.js from scraped Breakout homepage."""
import re
import json
from html import unescape

img_data = json.load(open("js/breakout-images.json", encoding="utf-8"))

# Optional: re-scrape for prices if breakout-scrape.html exists
price_map = {}
try:
    scrape = open("breakout-scrape.html", encoding="utf-8", errors="ignore").read()
    for m in re.finditer(
        r'title="([^"]+)"[\s\S]{0,4000}?Sale price:\s*PKR\s*([\d,]+)\s*Regular price:\s*PKR\s*([\d,]+)',
        scrape,
    ):
        price_map[m.group(1)] = {
            "price": int(m.group(2).replace(",", "")),
            "compareAt": int(m.group(3).replace(",", "")),
            "onSale": True,
            "bestSeller": True,
        }
    for m in re.finditer(
        r'title="([^"]+)"[\s\S]{0,4000}?Price:\s*PKR\s*([\d,]+)(?!.*Sale price)',
        scrape,
    ):
        name = m.group(1)
        if name not in price_map:
            price_map[name] = {"price": int(m.group(2).replace(",", "")), "onSale": False}
except FileNotFoundError:
    pass

heroes = [
    {
        "desktop": "https://www.breakout.com.pk/cdn/shop/files/Men_Main_jpg_68c3ab17-7192-4bf0-a758-e73897e8869a.jpg?v=1786734994&width=2560",
        "mobile": "https://www.breakout.com.pk/cdn/shop/files/Men_Mobile_jpg_7b3d3cb0-6622-4180-9ec7-3ab0803d54a1.jpg?v=1786734989&width=1000",
        "link": "#section-men",
    },
    {
        "desktop": "https://www.breakout.com.pk/cdn/shop/files/Women_Main_jpg_c97ae766-5dc7-4ade-84fc-df59a3bf5c97.jpg?v=1786734994&width=2560",
        "mobile": "https://www.breakout.com.pk/cdn/shop/files/Women_Mobile_jpg_97c99a29-9979-491a-9168-8cb618335c8e.jpg?v=1786734988&width=1000",
        "link": "#section-women",
    },
]

MEGA_MENU = {
    "male": {
        "highlights": ["NEW ARRIVALS", "SPECIAL PRICE"],
        "clothing": ["Tees", "Polos", "Summer Knits", "Shirts", "Sweaters", "Sweatshirts / Hoodies", "Jeans", "Cargo Pants", "Trousers / Chinos", "Joggers", "Shorts", "Co-ords"],
        "accessories": ["Shoes", "Jewellery", "Caps / Hats", "Sunglasses", "Perfumes", "Bags", "Belts", "Wallets", "Socks", "Underwears / Vests"],
        "collections": ["MIND THE GAP", "REMIX"],
    },
    "female": {
        "highlights": ["NEW ARRIVALS", "SPECIAL PRICE"],
        "clothing": ["Knit Tops / Tees", "Shirts / Dresses", "Sweatshirts / Hoodies", "Denims & Trousers", "Co-ords"],
        "accessories": ["Shoes", "Jewellery", "Bags", "Perfumes", "Scarves", "Glasses", "Caps / Hats", "Socks", "Nail Polish"],
        "collections": ["MIND THE GAP", "REMIX"],
    },
}

BEST_SELLERS = {
    "RELAXED FIT LINEN SHIRT", "BOXY FIT ZIP EMBROIDERED POLO", "CONTRAST RIB SUPER SOFT TEE",
    "STRETCH CROPPED FIT DENIM", "CARDIO TANK",
    "PRINTED BUTTON DOWN SHIRT", "STRAIGHT FIT DENIM", "BARREL FIT DENIM", "KIMONO TEXTURED TOP",
    "STRAIGHT FIT PLEATED DENIM", "PINSTRIPE BLAZER",
}


def infer_gender(name):
    u = name.upper()
    if u.startswith("BOYS ") or u.startswith("GIRLS "):
        return None  # kids catalog excluded
    women_kw = ("BLOUSE", "KIMONO", "BLAZER", "DRESS", "TOP", "JEGGINGS", "SKIRT", "FROCK", "PLAYSUIT")
    if any(k in u for k in women_kw):
        return "female"
    men_kw = ("POLO", "LINEN SHIRT", "DENIM", "TROUSER", "CARGO", "CARROT", "CARPENTER")
    if any(k in u for k in men_kw):
        return "male"
    return "female" if "WIDE LEG TROUSERS" in u or "MEGA WIDE" in u else "male"


def infer_category(name, gender):
    u = name.upper()
    if "TEE" in u or "TANK" in u or "POLO" in u:
        return {"male": "tees", "female": "knit"}.get(gender, "tees")
    if "SHIRT" in u or "BLOUSE" in u or "TOP" in u or "BLAZER" in u or "KIMONO" in u:
        return {"male": "shirts", "female": "shirts"}.get(gender, "shirts")
    if "DENIM" in u or "JEAN" in u:
        return {"male": "denims", "female": "denims"}.get(gender, "denims")
    if "TROUSER" in u or "SHORT" in u or "CHINO" in u or "TIGHT" in u or "SKIRT" in u or "CAPRI" in u:
        return {"male": "trousers", "female": "denims"}.get(gender, "trousers")
    if "SET" in u or "COORD" in u or "OUTFIT" in u or "PLAYSUIT" in u:
        return {"male": "tees", "female": "coords"}.get(gender, "coords")
    return {"male": "tees", "female": "knit"}.get(gender, "tees")


def vton_meta(name, gender):
    u = name.upper()
    if "DENIM" in u or "JEAN" in u or "TROUSER" in u or "SHORT" in u or "TIGHT" in u or "SKIRT" in u:
        return "lower_body", "pant" if "DENIM" in u or "JEAN" in u else "trouser"
    if "DRESS" in u or "PLAYSUIT" in u or "COORD" in u:
        return "full_body", "dress"
    return "upper_body", "shirt"


products = []
for i, (name, image) in enumerate(img_data["products"].items()):
    name = unescape(name)
    gender = infer_gender(name)
    if gender is None:
        continue
    pm = price_map.get(name, price_map.get(name.upper(), {"price": 3899, "onSale": False}))
    cat, garment = vton_meta(name, gender)
    fc = infer_category(name, gender)
    pid = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60]
    products.append({
        "id": pid or f"p-{i}",
        "name": name,
        "gender": gender,
        "featuredCategory": fc,
        "bestSeller": name in BEST_SELLERS or pm.get("onSale"),
        "onSale": pm.get("onSale", False),
        "price": pm["price"],
        "compareAt": pm.get("compareAt"),
        "image": image,
        "category": cat,
        "garment_type": garment,
    })

out = f"""// Auto-generated from breakout.com.pk scrape — real CDN images (Men + Women only)
const HERO_SLIDES = {json.dumps(heroes, indent=2)};

const MEGA_MENU = {json.dumps(MEGA_MENU, indent=2)};

const GENDERS = [
  {{ id: "male", slug: "men", label: "MEN", nav: "Men" }},
  {{ id: "female", slug: "women", label: "WOMEN", nav: "Women" }},
];

const FEATURED_CATEGORIES = {{
  male: [
    {{ id: "tees", label: "MEN TEES" }},
    {{ id: "shirts", label: "MEN SHIRTS" }},
    {{ id: "denims", label: "MEN DENIMS" }},
    {{ id: "trousers", label: "MEN TROUSERS/CHINOS" }},
  ],
  female: [
    {{ id: "knit", label: "WOMEN KNIT TOPS / TEES" }},
    {{ id: "shirts", label: "WOMEN SHIRTS / DRESSES" }},
    {{ id: "denims", label: "WOMEN DENIMS / TROUSERS" }},
    {{ id: "coords", label: "WOMEN CO-ORDS" }},
  ],
}};

const PRODUCTS = {json.dumps(products, indent=2)};

function getProduct(id) {{
  return PRODUCTS.find((p) => p.id === id) || null;
}}

function getProducts(gender, featuredCategoryId) {{
  return PRODUCTS.filter(
    (p) =>
      p.gender === gender &&
      (!featuredCategoryId || p.featuredCategory === featuredCategoryId)
  );
}}

function getBestSellers(gender, limit = 6) {{
  const sellers = PRODUCTS.filter((p) => p.gender === gender && p.bestSeller);
  return sellers.length ? sellers.slice(0, limit) : PRODUCTS.filter((p) => p.gender === gender).slice(0, limit);
}}

function formatPrice(amount) {{
  return "PKR " + amount.toLocaleString("en-PK");
}}

function formatPriceHtml(product) {{
  if (product.onSale && product.compareAt) {{
    return (
      `<span class="price-sale">Sale price:${{formatPrice(product.price)}}</span>` +
      `<span class="price-compare">Regular price: <s>${{formatPrice(product.compareAt)}}</s></span>`
    );
  }}
  return `<span class="price-regular">Price:${{formatPrice(product.price)}}</span>`;
}}
"""

open("js/products.js", "w", encoding="utf-8").write(out)
print(f"Generated {len(products)} products (Men + Women only)")
