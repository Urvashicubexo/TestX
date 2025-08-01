

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from worker_setup import celery_app

# ---- FastAPI App ----
app = FastAPI()

# ---- MongoDB Connection ----
client = MongoClient("mongodb://localhost:27017/")
db = client["Walmart_data"]
task_col = db["tasks"]
product_col = db["product"]
client_col = db["clients"]

# ---- Request Models ----
class TaskRequest(BaseModel):
    client_name: str
    category: str
    url: str

class ClientRequest(BaseModel):
    client_name: str
    client_email: str

# ---- Client Registration API ----
@app.post("/register-client/")
def register_client(client_data: ClientRequest):
    existing = client_col.find_one({"client_email": client_data.client_email})
    if existing:
        return JSONResponse(status_code=400, content={"message": "Client already registered."})

    client_doc = {
        "client_name": client_data.client_name,
        "client_email": client_data.client_email,
        "registered_at": datetime.now()
    }
    result = client_col.insert_one(client_doc)
    return {
        "message": "✅ Client registered successfully",
        "client_id": str(result.inserted_id)
    }


    product["colors"] = extract_colors(driver)
    product["sizes"] = extract_sizes(driver)

    # ---- Extract Images ----
    try:
        gallery_elem = scroll_to_element('div[data-testid="media-gallery"]')
        image_urls = []
        image_set = set()

        if gallery_elem:
            thumbs = driver.find_elements(By.CSS_SELECTOR, 'img[data-testid="media-gallery-thumbnail-image"]')
            for thumb in thumbs:
                if len(image_urls) >= 5:
                    break
                try:
                    driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", thumb)
                    time.sleep(1)
                    thumb.click()
                    time.sleep(1.5)
                    main_img = driver.find_element(By.CSS_SELECTOR,
                                                   'div[data-testid="media-gallery"] img[data-testid="media-gallery-image"]')
                    src = main_img.get_attribute("src") or main_img.get_attribute("data-src")
                    if src and src not in image_set:
                        image_set.add(src)
                        image_urls.append(src)
                except Exception:
                    continue
            if len(image_urls) < 5:
                imgs = gallery_elem.find_elements(By.TAG_NAME, 'img')
                for img in imgs:
                    src = img.get_attribute('src') or img.get_attribute('data-src')
                    if src and src not in image_set:
                        image_set.add(src)
                        image_urls.append(src)
                    if len(image_urls) >= 5:
                        break
        if not image_urls:
            imgs = driver.find_elements(By.CSS_SELECTOR, 'img')
            for img in imgs:
                src = img.get_attribute('src') or img.get_attribute('data-src')
                if src and src not in image_set and any(
                        ext in src.lower() for ext in ['.jpg', '.png', '.gif', '.webp']):
                    image_set.add(src)
                    image_urls.append(src)
                if len(image_urls) >= 5:
                    break
        product["images"] = image_urls
        print(f"🖼 Product gallery images: {len(product['images'])} extracted (max 5).")
    except Exception as e:
        print(f"❌ Error extracting images: {e}")

    # ---- Extract About This Item ----
    try:
        scroll_to_element_by_id("product-description-section")
        desc_container = WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="product-description-section"]'))
        )
        details = []

        for ul in desc_container.find_elements(By.XPATH, ".//ul | .//ol"):
            for li in ul.find_elements(By.TAG_NAME, 'li'):
                line = li.text.strip()
                if line:
                    details.append(line)

        for p in desc_container.find_elements(By.TAG_NAME, 'p'):
            line = p.text.strip()
            if line and line not in details:
                details.append(line)

        if not details:
            raw_text = desc_container.text.strip()
            details = [line.strip() for line in raw_text.split("\n") if
                       line.strip() and "about this item" not in line.lower()]

        about_text = "\n".join(details).strip()
        product["about_this_item"] = about_text if about_text else "N/A"
        print("📝 About This Item content extracted.")
    except Exception as e:
        product["about_this_item"] = "N/A"
        print(f"⚠ Failed to extract About This Item: {e}")

    # ---- Related Links ----
    try:
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/ip/"]')
        unique_links = set()
        for a in links:
            href = a.get_attribute("href")
            if href and "/ip/" in href:
                unique_links.add(href.split("?")[0])
        product["related_links"] = list(unique_links)
    except Exception as e:
        print("⚠ Related links not found:", e)

    # ---- Print Scraped Data ----
    print("\n✅ Product Details:")
    for k, v in product.items():
        if isinstance(v, list):
            print(f"{k.capitalize()}: {len(v)} items -> {v}")
        else:
            print(f"{k.capitalize()}: {v}")

    # ---- Save to MongoDB ----
    try:
        collection.insert_one(product)
        print("🍃 Saved to MongoDB")
    except Exception as e:
        print("❌ Error saving to MongoDB:", e)

    # ---- Save to CSV ----
    csv_file = "walmart_data.csv"
    try:
        df = pd.DataFrame([product])
        df.to_csv(csv_file, index=False)
        print(f"📁 Saved to CSV: {csv_file}")
    except Exception as e:
        print("❌ Error saving to CSV:", e)

    driver.quit()
