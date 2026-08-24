import re
import json

html = open("breakout-scrape.html", encoding="utf-8", errors="ignore").read()

# Hero slides: pair desktop + mobile within each slide block
slide_blocks = re.findall(
    r'ai-hero-slide-amwdyb2vywhbqrgfxyaigenblock9b066e84igcax.*?(?=ai-hero-slide-amwdyb2vywhbqrgfxyaigenblock9b066e84igcax|$)',
    html,
    re.S,
)
heroes = []
for block in slide_blocks[:8]:
    d = re.search(r'ai-hero-slide-image-desktop[^>]+src="(//[^"]+)"', block)
    m = re.search(r'ai-hero-slide-image-mobile[^>]+src="(//[^"]+)"', block)
    link = re.search(r'href="(/collections/[^"]+)"', block)
    if d:
        heroes.append({
            "desktop": "https:" + d.group(1),
            "mobile": "https:" + m.group(1) if m else "https:" + d.group(1),
            "link": link.group(1) if link else "#",
        })

# Products: src before alt
products = {}
for m in re.finditer(
    r'src="(//www\.breakout\.com\.pk/cdn/shop/files/[^"]+)" alt="([^"]+)"',
    html,
):
    url = "https:" + m.group(1).replace("&width=480", "&width=840")
    name = m.group(2).strip()
    if len(name) > 3 and name not in products:
        products[name] = url

# Prices from visible text near product titles
print(json.dumps({"heroes": heroes, "productCount": len(products)}, indent=2))
for k in list(products.keys())[:5]:
    print(k)

with open("js/breakout-images.json", "w", encoding="utf-8") as f:
    json.dump({"heroes": heroes, "products": products}, f, indent=2)

print("Wrote js/breakout-images.json")
