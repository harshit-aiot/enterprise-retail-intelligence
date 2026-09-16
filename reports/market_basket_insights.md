# Enterprise Retail Intelligence & Decision Engine
## Market Basket Analysis — Insights Report

**Generated:** 2026-09-17 03:16:08  
**Phase:** 12 — Market Basket Analysis  

---

## Methodology

- **Approach:** Product co-occurrence analysis on prior order basket data
- **Products analyzed:** Top 500 by purchase frequency
- **Total prior orders:** Used as denominator for support calculation
- **Minimum support:** 0.005 (0.5% of all orders)
- **Minimum confidence:** 0.1 (10%)
- **Minimum lift:** 1.1
- **Total rules found:** 87

**Metrics:**
- **Support:** P(A ∩ B) — fraction of all orders containing both products
- **Confidence:** P(B|A) — fraction of orders with A that also contain B
- **Lift:** Support / (P(A) × P(B)) — how much more co-occurring than by chance (>1 = positive association)

---

## Top 50 Product Associations (by Lift)

| Antecedent | Consequent | Support | Confidence | Lift | Co-occurrences |
|-----------|-----------|---------|------------|------|----------------|
| Limes | Organic Cilantro | 0.0055 | 0.125 | 5.776 | 17,565 |
| Organic Cilantro | Limes | 0.0055 | 0.253 | 5.776 | 17,565 |
| Organic Yellow Onion | Organic Garlic | 0.0069 | 0.195 | 5.699 | 22,073 |
| Organic Garlic | Organic Yellow Onion | 0.0069 | 0.201 | 5.699 | 22,073 |
| Large Lemon | Limes | 0.0085 | 0.179 | 4.104 | 27,403 |
| Limes | Large Lemon | 0.0085 | 0.195 | 4.104 | 27,403 |
| Organic Lemon | Organic Hass Avocado | 0.0066 | 0.242 | 3.645 | 21,246 |
| Organic Cucumber | Organic Hass Avocado | 0.0054 | 0.217 | 3.268 | 17,456 |
| Organic Raspberries | Organic Strawberries | 0.0105 | 0.247 | 3.001 | 33,863 |
| Organic Strawberries | Organic Raspberries | 0.0105 | 0.128 | 3.001 | 33,863 |
| Large Lemon | Organic Avocado | 0.0076 | 0.160 | 2.908 | 24,417 |
| Organic Avocado | Large Lemon | 0.0076 | 0.138 | 2.908 | 24,417 |
| Organic Blueberries | Organic Strawberries | 0.0074 | 0.237 | 2.884 | 23,756 |
| Organic Avocado | Limes | 0.0068 | 0.124 | 2.846 | 22,010 |
| Limes | Organic Avocado | 0.0068 | 0.157 | 2.846 | 22,010 |
| Organic Hass Avocado | Organic Raspberries | 0.0080 | 0.121 | 2.833 | 25,793 |
| Organic Raspberries | Organic Hass Avocado | 0.0080 | 0.188 | 2.833 | 25,793 |
| Organic Yellow Onion | Organic Hass Avocado | 0.0062 | 0.176 | 2.644 | 19,927 |
| Organic Large Extra Fancy Fuji Apple | Bag of Organic Bananas | 0.0073 | 0.311 | 2.634 | 23,364 |
| Organic Zucchini | Organic Baby Spinach | 0.0063 | 0.195 | 2.588 | 20,415 |
| Organic Fuji Apple | Banana | 0.0106 | 0.379 | 2.576 | 33,943 |
| Organic Garlic | Organic Baby Spinach | 0.0065 | 0.191 | 2.542 | 20,996 |
| Organic Raspberries | Bag of Organic Bananas | 0.0126 | 0.295 | 2.504 | 40,503 |
| Bag of Organic Bananas | Organic Raspberries | 0.0126 | 0.107 | 2.504 | 40,503 |
| Organic Cucumber | Organic Strawberries | 0.0052 | 0.206 | 2.501 | 16,555 |
| Organic Hass Avocado | Bag of Organic Bananas | 0.0194 | 0.292 | 2.473 | 62,341 |
| Bag of Organic Bananas | Organic Hass Avocado | 0.0194 | 0.164 | 2.473 | 62,341 |
| Organic Garlic | Organic Hass Avocado | 0.0055 | 0.161 | 2.426 | 17,697 |
| Honeycrisp Apple | Banana | 0.0088 | 0.356 | 2.423 | 28,408 |
| Organic Zucchini | Organic Hass Avocado | 0.0051 | 0.157 | 2.364 | 16,464 |
| Apple Honeycrisp Organic | Bag of Organic Bananas | 0.0074 | 0.279 | 2.361 | 23,696 |
| Organic Baby Spinach | Organic Avocado | 0.0096 | 0.128 | 2.321 | 30,889 |
| Organic Avocado | Organic Baby Spinach | 0.0096 | 0.175 | 2.321 | 30,889 |
| Organic Strawberries | Organic Hass Avocado | 0.0127 | 0.154 | 2.320 | 40,794 |
| Organic Hass Avocado | Organic Strawberries | 0.0127 | 0.191 | 2.320 | 40,794 |
| Organic Yellow Onion | Organic Baby Spinach | 0.0061 | 0.174 | 2.309 | 19,707 |
| Organic Cucumber | Bag of Organic Bananas | 0.0067 | 0.268 | 2.269 | 21,534 |
| Cucumber Kirby | Banana | 0.0100 | 0.330 | 2.244 | 32,097 |
| Organic Gala Apples | Bag of Organic Bananas | 0.0059 | 0.260 | 2.205 | 18,958 |
| Organic Hass Avocado | Organic Baby Spinach | 0.0109 | 0.163 | 2.171 | 34,901 |
| Organic Baby Spinach | Organic Hass Avocado | 0.0109 | 0.144 | 2.171 | 34,901 |
| Organic Lemon | Bag of Organic Bananas | 0.0070 | 0.255 | 2.161 | 22,383 |
| Limes | Organic Hass Avocado | 0.0062 | 0.142 | 2.144 | 20,030 |
| Organic Whole Milk | Organic Strawberries | 0.0074 | 0.173 | 2.097 | 23,813 |
| Organic Avocado | Banana | 0.0166 | 0.302 | 2.054 | 53,395 |
| Banana | Organic Avocado | 0.0166 | 0.113 | 2.054 | 53,395 |
| Seedless Red Grapes | Banana | 0.0076 | 0.297 | 2.023 | 24,594 |
| Large Lemon | Organic Baby Spinach | 0.0071 | 0.149 | 1.986 | 22,808 |
| Blueberries | Banana | 0.0051 | 0.291 | 1.980 | 16,286 |
| Bag of Organic Bananas | Organic Strawberries | 0.0192 | 0.162 | 1.973 | 61,628 |

---

## Business Interpretation

**High lift pairs** indicate products that are purchased together significantly more often than chance.
These represent strong cross-selling opportunities.

**High confidence pairs** indicate that when customers buy product A, they very often also buy product B.
This is most actionable for recommendation systems.

## Limitations

- Analysis limited to top 500 products for computational tractability
- No price data available — margin impact of cross-sell cannot be assessed
- Association ≠ causation — products may co-occur due to lifestyle patterns
- Dataset from 2017 — product assortment may have changed

---
*Generated by python/market_basket.py — Phase 12*