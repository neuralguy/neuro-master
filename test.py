"""One-time script to check Lava.top products and their offer IDs."""
import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()


async def main():
    api_key = "VgHqmd78r2AKMUMVoY6q1FCfjNlR7VaJ4X5t4oIaMaYtjOlKMgfm9JNBXyoOesyV"
    api_url = os.getenv("LAVA_API_URL", "https://gate.lava.top")

    if not api_key:
        print("ERROR: LAVA_API_KEY not set in .env")
        return

    headers = {
        "X-Api-Key": api_key,
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get products
        print(f"Fetching products from {api_url}/api/v2/products ...")
        resp = await client.get(f"{api_url}/api/v2/products", headers=headers)
        print(f"Status: {resp.status_code}\n")

        if resp.status_code != 200:
            print(f"Error: {resp.text}")
            return

        data = resp.json()

        # Print all products with their offers
        products = data.get("products", data) if isinstance(data, dict) else data

        if isinstance(products, list):
            for product in products:
                print(f"Product: {product.get('title', product.get('name', 'N/A'))}")
                print(f"  ID: {product.get('id', 'N/A')}")

                offers = product.get("offers", [])
                for offer in offers:
                    print(f"  Offer ID: {offer.get('id')}")
                    print(f"    Price: {offer.get('price', {})}")
                    print(f"    Title: {offer.get('title', 'N/A')}")
                print()
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False))


asyncio.run(main())

