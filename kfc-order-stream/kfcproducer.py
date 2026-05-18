import random
import uuid
import json

from faker import Faker

fake = Faker()

BRANCHES = [
    "KFC Dubai Mall",
    "KFC Mall of the Emirates",
    "KFC Marina Walk",
    "KFC Abu Dhabi Corniche",
    "KFC Sharjah City Centre",
    "KFC Yas Mall",
]

# Prices are realistic AED defaults — uae.kfc.me is a JS-rendered SPA and
# could not be scraped live. Tweak these to match the current menu as needed.
ITEMS = [
    {"name": "🍔 Zinger Burger", "price_aed": 19},
    {"name": "🍔 Mighty Zinger", "price_aed": 29},
    {"name": "🌯 Twister Wrap", "price_aed": 23},
    {"name": "🍗 Original Recipe Chicken (1 pc)", "price_aed": 11},
    {"name": "🌶️ Hot & Crispy Chicken (1 pc)", "price_aed": 11},
    {"name": "🔥 Hot Wings (5 pcs)", "price_aed": 23},
    {"name": "🍿 Popcorn Chicken", "price_aed": 17},
    {"name": "🍚 Rice Bowlz", "price_aed": 26},
    {"name": "🍗 Crispy Strips (3 pcs)", "price_aed": 25},
    {"name": "🍕 Chizza", "price_aed": 29},
    {"name": "🍔 Boxmaster", "price_aed": 31},
    {"name": "🥪 Crunch Burger", "price_aed": 19},
]

ADDONS = [
    {"name": "🍟 Regular Fries", "price_aed": 9},
    {"name": "🍟 Large Fries", "price_aed": 13},
    {"name": "🥗 Coleslaw", "price_aed": 8},
    {"name": "🥔 Mashed Potato & Gravy", "price_aed": 9},
    {"name": "🌽 Corn on the Cob", "price_aed": 7},
    {"name": "🥤 Pepsi", "price_aed": 7},
    {"name": "🥤 7Up", "price_aed": 7},
    {"name": "🥤 Mountain Dew", "price_aed": 7},
    {"name": "🍦 Krusher", "price_aed": 17},
    {"name": "🍞 Bread Roll", "price_aed": 3},
    {"name": "🌶️ Spicy Dip", "price_aed": 2},
    {"name": "🧄 Garlic Mayo", "price_aed": 2},
]

TOP_DEALS = [
    {"name": "🔥 8 Pcs Hot & Crispy Bucket", "price_aed": 79},
    {"name": "👨‍👩‍👧 Family Feast (12 Pcs + 4 Sides + Drink)", "price_aed": 129},
    {"name": "💪 Mighty Bucket for One", "price_aed": 39},
    {"name": "🚗 Streetwise 2 (2 Pcs + Fries + Drink)", "price_aed": 21},
    {"name": "📦 Variety Bucket (Wings + Strips + Popcorn)", "price_aed": 89},
    {"name": "🍔 Zinger Box Meal", "price_aed": 31},
    {"name": "🍕 Chizza Combo", "price_aed": 41},
    {"name": "🍗 21 Pcs Mega Bucket", "price_aed": 179},
    {"name": "🍱 Rizo Box (Rice + Chicken + Drink)", "price_aed": 26},
    {"name": "👬 Sharing Bucket for Two", "price_aed": 65},
]

ITEM_COUNT_CHOICES = [1, 2, 3, 4]
ITEM_COUNT_WEIGHTS = [15, 55, 20, 10]
COUNTRY_CODES = ["+971", "+91", "+44"]
ORDER_TYPES = ["Deliveroo", "Just Eat", "Uber Eats", "Dine In", "Takeaway"]


def generate_phone():
    code = random.choice(COUNTRY_CODES)
    digits = "".join(str(random.randint(0, 9)) for _ in range(10))
    return f"{code} {digits}"


def generate_item():
    base = random.choice(ITEMS)
    addons = random.sample(ADDONS, k=random.randint(0, 3))
    return {
        "name": base["name"],
        "price_aed": base["price_aed"],
        "addons": [{"name": addon["name"], "price_aed": addon["price_aed"]} for addon in addons],
        "is_deal": False,
    }


def _deal_as_item(deal):
    return {
        "name": deal["name"],
        "price_aed": deal["price_aed"],
        "addons": [],
        "is_deal": True,
    }


def _item_total(item):
    return item["price_aed"] + sum(a["price_aed"] for a in item["addons"])


def generate_order():
    n_items = random.choices(ITEM_COUNT_CHOICES, weights=ITEM_COUNT_WEIGHTS, k=1)[0]
    items = [generate_item() for _ in range(n_items)]
    if random.random() < 0.3:
        items.append(_deal_as_item(random.choice(TOP_DEALS)))
    total_aed = sum(_item_total(i) for i in items)
    return {
        "order_id": str(uuid.uuid4()),
        "branch": random.choice(BRANCHES),
        "type": random.choice(ORDER_TYPES),
        "customer_name": fake.name(),
        "phone_number": generate_phone(),
        "items": items,
        "total_aed": total_aed,
    }


if __name__ == "__main__":
    print(json.dumps(generate_order(), indent=2, ensure_ascii=False))
