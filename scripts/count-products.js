const fs = require("fs");
const vm = require("vm");
const code = fs.readFileSync("js/products.js", "utf8");
const ctx = { console };
vm.createContext(ctx);
vm.runInContext(code, ctx);
const { PRODUCTS, getProducts, getBestSellers, GENDERS } = ctx;
console.log("total", PRODUCTS.length);
GENDERS.forEach((g) => {
  console.log(g.id, "best", getBestSellers(g.id).length, "all", PRODUCTS.filter((p) => p.gender === g.id).length);
});
