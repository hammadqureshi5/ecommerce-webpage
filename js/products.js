/**
 * Product catalog for the dummy shop.
 *
 * Each product maps to a vton_type from vton_supported_combinations.csv:
 *   - upper_body  → shirts / tops
 *   - lower_body  → pants / bottoms
 *   - full_body   → full outfits
 *
 * image: local photo in images/ (downloaded from Unsplash)
 * garment_type: used later by the backend classifier
 */

const CATEGORIES = [
  { id: "upper_body", label: "Shirt", icon: "👔" },
  { id: "lower_body", label: "Pant", icon: "👖" },
  { id: "full_body", label: "Full body", icon: "🧥" },
];

const PRODUCTS = [
  // ── Male — Shirts (upper_body) ──────────────────────────────────────
  {
    id: "m-shirt-blue",
    name: "Blue Formal Shirt",
    gender: "male",
    category: "upper_body",
    garment_type: "shirt",
    color: "#3b6ea5",
    image: "images/m-shirt-blue.jpg",
    description: "Classic blue cotton shirt",
  },
  {
    id: "m-tshirt-white",
    name: "White T-Shirt",
    gender: "male",
    category: "upper_body",
    garment_type: "tshirt",
    color: "#f0f0f0",
    image: "images/m-tshirt-white.jpg",
    description: "Plain white crew-neck tee",
  },
  {
    id: "m-kurta-cream",
    name: "Cream Kurta",
    gender: "male",
    category: "upper_body",
    garment_type: "kurta",
    color: "#e8dcc8",
    image: "images/m-kurta-cream.jpg",
    description: "Long kurta with side slits",
  },

  // ── Male — Pants (lower_body) ───────────────────────────────────────
  {
    id: "m-jeans-dark",
    name: "Dark Jeans",
    gender: "male",
    category: "lower_body",
    garment_type: "jeans",
    color: "#2c3e6b",
    image: "images/m-jeans-dark.jpg",
    description: "Slim-fit dark wash denim",
  },
  {
    id: "m-trouser-grey",
    name: "Grey Trousers",
    gender: "male",
    category: "lower_body",
    garment_type: "trouser",
    color: "#6b7280",
    image: "images/m-trouser-grey.jpg",
    description: "Formal grey trousers",
  },
  {
    id: "m-shorts-khaki",
    name: "Khaki Shorts",
    gender: "male",
    category: "lower_body",
    garment_type: "shorts",
    color: "#b5a642",
    image: "images/m-shorts-khaki.jpg",
    description: "Casual summer shorts",
  },

  // ── Male — Full body ────────────────────────────────────────────────
  {
    id: "m-suit-navy",
    name: "Navy Suit",
    gender: "male",
    category: "full_body",
    garment_type: "suit",
    color: "#1e3a5f",
    image: "images/m-suit-navy.jpg",
    description: "Two-piece navy business suit",
  },
  {
    id: "m-shirt-pant-set",
    name: "Shirt + Pant Set",
    gender: "male",
    category: "full_body",
    garment_type: "shirt_pant",
    color: "#4a7c59",
    image: "images/m-shirt-pant-set.jpg",
    description: "Coordinated shirt and pant outfit",
  },
  {
    id: "m-kurta-shalwar",
    name: "Kurta Shalwar",
    gender: "male",
    category: "full_body",
    garment_type: "kurta_shalwar",
    color: "#8b7355",
    image: "images/m-kurta-shalwar.jpg",
    description: "Traditional kurta with shalwar",
  },

  // ── Female — Shirts (upper_body) ────────────────────────────────────
  {
    id: "f-blouse-white",
    name: "White Blouse",
    gender: "female",
    category: "upper_body",
    garment_type: "shirt",
    color: "#fafafa",
    image: "images/f-blouse-white.jpg",
    description: "Elegant white blouse",
  },
  {
    id: "f-tshirt-pink",
    name: "Pink T-Shirt",
    gender: "female",
    category: "upper_body",
    garment_type: "tshirt",
    color: "#f4a4b8",
    image: "images/f-tshirt-pink.jpg",
    description: "Soft pink casual tee",
  },
  {
    id: "f-kurta-embroidered",
    name: "Embroidered Kurta",
    gender: "female",
    category: "upper_body",
    garment_type: "kurta",
    color: "#c9a87c",
    image: "images/f-kurta-embroidered.jpg",
    description: "Embroidered long kurta",
  },

  // ── Female — Pants (lower_body) ─────────────────────────────────────
  {
    id: "f-jeans-light",
    name: "Light Jeans",
    gender: "female",
    category: "lower_body",
    garment_type: "jeans",
    color: "#7ba3c9",
    image: "images/f-jeans-light.jpg",
    description: "High-waist light wash jeans",
  },
  {
    id: "f-trouser-black",
    name: "Black Trousers",
    gender: "female",
    category: "lower_body",
    garment_type: "trouser",
    color: "#2d2d2d",
    image: "images/f-trouser-black.jpg",
    description: "Tailored black trousers",
  },
  {
    id: "f-shalwar-white",
    name: "White Shalwar",
    gender: "female",
    category: "lower_body",
    garment_type: "shalwar",
    color: "#f5f5f0",
    image: "images/f-shalwar-white.jpg",
    description: "Loose white shalwar",
  },

  // ── Female — Full body ──────────────────────────────────────────────
  {
    id: "f-dress-red",
    name: "Red Dress",
    gender: "female",
    category: "full_body",
    garment_type: "dress",
    color: "#c0392b",
    image: "images/f-dress-red.jpg",
    description: "Midi red dress",
  },
  {
    id: "f-kurta-shalwar-set",
    name: "Kurta Shalwar Set",
    gender: "female",
    category: "full_body",
    garment_type: "kurta_shalwar",
    color: "#9b7bb8",
    image: "images/f-kurta-shalwar-set.jpg",
    description: "Matching kurta and shalwar",
  },
  {
    id: "f-shirt-pant-outfit",
    name: "Shirt + Pant Outfit",
    gender: "female",
    category: "full_body",
    garment_type: "shirt_pant",
    color: "#5d8a66",
    image: "images/f-shirt-pant-outfit.jpg",
    description: "Casual coordinated outfit",
  },
];

/** Find one product by its id. */
function getProduct(id) {
  return PRODUCTS.find((p) => p.id === id) || null;
}

/** Filter products by gender and optional category. */
function getProducts(gender, categoryId) {
  return PRODUCTS.filter(
    (p) => p.gender === gender && (!categoryId || p.category === categoryId)
  );
}
