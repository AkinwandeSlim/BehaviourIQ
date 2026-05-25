import random


CATEGORY_PRODUCTS = {
    1051: {
        "category": "Consumer Electronics",
        "brands": [
            "Apple",
            "Samsung",
            "Sony",
            "JBL",
            "Anker"
        ],
        "products": [
            "AirPods Pro",
            "Galaxy Buds",
            "Bluetooth Speaker",
            "Wireless Charger",
            "Smart Watch"
        ]
    },

    686: {
        "category": "Laptops",
        "brands": [
            "Apple",
            "Dell",
            "HP",
            "Lenovo",
            "ASUS"
        ],
        "products": [
            "MacBook Air",
            "XPS 13",
            "Pavilion 15",
            "ThinkPad X1",
            "ROG Zephyrus"
        ]
    },

    730: {
        "category": "Footwear",
        "brands": [
            "Nike",
            "Adidas",
            "Puma",
            "New Balance"
        ],
        "products": [
            "Air Force 1",
            "Ultraboost",
            "RS-X",
            "550 Sneakers"
        ]
    }
}















def generate_product(category_id):
    data = CATEGORY_PRODUCTS.get(category_id)

    if not data:
        return {
            "category": "General Products",
            "product": "Generic Item"
        }

    brand = random.choice(data["brands"])
    product = random.choice(data["products"])

    return {
        "category": data["category"],
        "product": f"{brand} {product}"
    }