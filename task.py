# import time
# import pandas as pd
# from pymongo import MongoClient
# import undetected_chromedriver as uc
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
#
# # ---- MongoDB Setup ----
# client = MongoClient("mongodb://localhost:27017/")
# db = client["Walmart_data"]
# collection = db["consoles"]
#
# # ---- Scraping Function ----
# def scrape_and_store(product_url, category, client_name, task_id):
#     options = uc.ChromeOptions()
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.add_argument("--lang=en-US,en")
#     options.add_argument("--window-size=1920,1080")
#     options.add_argument(
#         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
#     )
#
#     driver = uc.Chrome(options=options, headless=True)
#     driver.get(product_url)
#     time.sleep(3)
#
#     if "captcha" in driver.page_source.lower():
#         print("CAPTCHA detected! Solve it manually.")
#         input("Press ENTER after solving CAPTCHA...")
#
#     def scroll_to_element(selector, timeout=10):
#         try:
#             elem = WebDriverWait(driver, timeout).until(
#                 EC.presence_of_element_located((By.CSS_SELECTOR, selector))
#             )
#             driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", elem)
#             time.sleep(2)
#             return elem
#         except Exception:
#             return None
#
#     def safe_find_text_by_css(selectors, timeout=5):
#         if isinstance(selectors, str):
#             selectors = [selectors]
#         for selector in selectors:
#             try:
#                 elem = WebDriverWait(driver, timeout).until(
#                     EC.presence_of_element_located((By.CSS_SELECTOR, selector))
#                 )
#                 text = elem.text.strip()
#                 if text:
#                     return text
#             except:
#                 continue
#         return "N/A"
#
#     def extract_colors(driver):
#         color_names = set()
#         selectors = [
#             'ul[data-tl-id*="color"] button span',
#             'ul[data-tl-id*="color"] label span',
#             'div[data-automation-id="color-picker"] label span',
#             '[data-tl-id*="color"] button span',
#             '[data-tl-id*="color"] label span',
#             '[aria-label*="Color"]',
#             'button[aria-checked="true"] span',
#             '[itemprop="color"]',
#         ]
#         for sel in selectors:
#             elems = driver.find_elements(By.CSS_SELECTOR, sel)
#             for elem in elems:
#                 name = elem.text.strip()
#                 if name:
#                     color_names.add(name)
#             if color_names:
#                 break
#         if not color_names:
#             imgs = driver.find_elements(By.CSS_SELECTOR, 'img[alt*="color"], img[alt*="Color"]')
#             for img in imgs:
#                 alt = img.get_attribute('alt')
#                 if alt:
#                     color_names.add(alt.strip())
#         return list(color_names) or ["N/A"]
#
#     def extract_sizes(driver):
#         size_names = set()
#         size_selectors = [
#             'ul[data-tl-id*="size"] button span',
#             'ul[data-tl-id*="size"] label span',
#             'div[data-automation-id="size-picker"] label',
#             '[aria-label*="Size"]',
#             'button[aria-checked="true"] span',
#         ]
#         for sel in size_selectors:
#             elems = driver.find_elements(By.CSS_SELECTOR, sel)
#             for elem in elems:
#                 txt = elem.text.strip()
#                 if txt and txt.lower() != "select":
#                     size_names.add(txt)
#             if size_names:
#                 break
#         return list(size_names) or ["N/A"]
#
#     def extract_price(driver):
#         selectors = [
#             'span[itemprop="price"]',
#             'span[data-automation-id="product-price"]',
#             'span.price-characteristic',
#             'div[data-testid="price"] span'
#         ]
#         for sel in selectors:
#             try:
#                 elem = WebDriverWait(driver, 10).until(
#                     EC.presence_of_element_located((By.CSS_SELECTOR, sel))
#                 )
#                 text = elem.text.strip()
#                 if text:
#                     return float(text.replace('$', '').replace(',', '').strip())
#             except:
#                 continue
#         return 0.0
#
#     product = {
#         "client_name": client_name,
#         "category": category,
#         "task_id": task_id,
#         "title": safe_find_text_by_css(['h1.prod-ProductTitle', 'h1[itemprop="name"]'], timeout=15),
#         "price": extract_price(driver),
#         "images": [],
#         "about_this_item": [],
#         "colors": extract_colors(driver),
#         "sizes": extract_sizes(driver),
#         "product_url": product_url,
#         "related_links": [],
#         "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
#     }
#
#     try:
#         scroll_to_element('div[data-testid="media-gallery"]')
#         image_urls = []
#         thumbs = driver.find_elements(By.CSS_SELECTOR, 'img[data-testid="media-gallery-thumbnail-image"]')
#         for thumb in thumbs[:5]:
#             try:
#                 thumb.click()
#                 time.sleep(1)
#                 main_img = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="media-gallery"] img')
#                 src = main_img.get_attribute("src")
#                 if src and src not in image_urls:
#                     image_urls.append(src)
#             except:
#                 continue
#         product["images"] = image_urls
#     except:
#         product["images"] = []
#
#     try:
#         scroll_to_element('div.dangerous-html.mb3', timeout=15)
#         about_elem = WebDriverWait(driver, 12).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, 'div.dangerous-html.mb3'))
#         )
#         paragraphs = about_elem.find_elements(By.TAG_NAME, 'p')
#         product["about_this_item"] = [p.text.strip() for p in paragraphs if p.text.strip()]
#     except:
#         product["about_this_item"] = []
#
#     try:
#         links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/ip/"]')
#         product["related_links"] = list({a.get_attribute("href").split("?")[0] for a in links if a.get_attribute("href")})
#     except:
#         product["related_links"] = []
#
#     # ---- Save to MongoDB ----
#     try:
#         collection.insert_one(product)
#         print("🍃 Saved to MongoDB")
#     except Exception as e:
#         print("❌ MongoDB Error:", e)
#
#     # ---- Save to CSV ----
#     try:
#         df = pd.DataFrame([product])
#         df.to_csv("walmart_data.csv", index=False)
#         print("📁 Saved to CSV")
#     except Exception as e:
#         print("❌ CSV Error:", e)
#
#     driver.quit()
#     return product


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

# ---- Task Submission API ----
@app.post("/submit-task/")
def submit_task(task: TaskRequest):
    task_data = {
        "client_name": task.client_name,
        "category": task.category,
        "url": task.url,
        "status": "pending",
        "created_at": datetime.now()
    }
    result = task_col.insert_one(task_data)
    task_id = str(result.inserted_id)

    try:
        scrape_and_store(task.url, task.category, task.client_name, task_id)
        task_col.update_one({"_id": result.inserted_id}, {"$set": {"status": "completed"}})
    except Exception as e:
        task_col.update_one({"_id": result.inserted_id}, {"$set": {"status": "failed", "error": str(e)}})
        return JSONResponse(status_code=500, content={"message": "Scraping failed", "error": str(e)})

    return {"message": "✅ Task created and scraping completed", "task_id": task_id}

@celery_app.task(name="task.scrape_task")
def scrape_and_store(product_url, category, client_name, task_id):
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=en-US,en")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )

    driver = uc.Chrome(options=options, headless=True)
    driver.get(product_url)
    time.sleep(3)

    if "captcha" in driver.page_source.lower():
        print("CAPTCHA detected! Solve it manually.")
        input("Press ENTER after solving CAPTCHA...")

    def scroll_to_element(selector, timeout=10):
        try:
            elem = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", elem)
            time.sleep(2)
            return elem
        except Exception:
            return None

    def scroll_to_element_by_id(element_id):
        try:
            driver.execute_script(f"document.getElementById('{element_id}').scrollIntoView();")
            time.sleep(2)
            return True
        except Exception:
            return False

    def safe_find_text_by_css(selectors, timeout=5):
        if isinstance(selectors, str):
            selectors = [selectors]
        for selector in selectors:
            try:
                elem = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                text = elem.text.strip()
                if text:
                    return text
            except:
                continue
        return "N/A"

    def extract_colors(driver):
        color_names = set()
        try:
            selectors = [
                'ul[data-tl-id*="color"] button span',
                'ul[data-tl-id*="color"] label span',
                'div[data-automation-id="color-picker"] label span',
                '[data-tl-id*="color"] button span',
                '[data-tl-id*="color"] label span',
                '[aria-label*="Color"]',
                'button[aria-checked="true"] span',
                '[itemprop="color"]',
            ]

            for sel in selectors:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                for elem in elems:
                    name = elem.text.strip()
                    if name:
                        color_names.add(name)
                if color_names:
                    break

            if not color_names:
                imgs = driver.find_elements(By.CSS_SELECTOR,
                                            'img[data-testid*="swatch"], img[alt*="color"], img[alt*="Color"], img[alt*="colour"]')
                for img in imgs:
                    alt = img.get_attribute('alt') or img.get_attribute('title')
                    if alt:
                        alt_clean = alt.replace('Color', '').replace('Swatch', '').strip()
                        if alt_clean:
                            color_names.add(alt_clean)

            if not color_names:
                color_names.add("N/A")
        except Exception:
            return ["N/A"]

        return list(color_names)

    def extract_sizes(driver):
        size_names = set()
        try:
            size_selectors = [
                'ul[data-tl-id*="size"] button span',
                'ul[data-tl-id*="size"] label span',
                'div[data-automation-id="size-picker"] label',
                'ul[data-tl-id*="variant"] button span',
                'ul[data-tl-id*="variant"] label span',
                '[aria-label*="Size"]',
                'button[aria-checked="true"] span',
            ]

            for sel in size_selectors:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                for elem in elems:
                    txt = elem.text.strip()
                    if txt and txt.lower() != "select":
                        size_names.add(txt)
                if size_names:
                    break

            if not size_names:
                selected = driver.find_elements(By.CSS_SELECTOR, '[aria-checked="true"] span')
                for s in selected:
                    txt = s.text.strip()
                    if txt:
                        size_names.add(txt)

            if not size_names:
                return ["N/A"]

            cleaned_sizes = []
            for size in size_names:
                try:
                    size_int = int(size)
                    cleaned_sizes.append(size_int)
                except:
                    cleaned_sizes.append(size)
            return cleaned_sizes
        except Exception:
            return ["N/A"]

    def extract_price(driver):
        possible_selectors = [
            'span[itemprop="price"]',
            'span[data-automation-id="product-price"]',
            'span.price-characteristic',
            'span[class*="Price"]',
            'div[class*="price"] span',
            'div[data-testid="price"] span'
        ]

        for sel in possible_selectors:
            try:
                elem = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                )
                text = elem.text.strip()
                if text:
                    price = text.replace('$', '').replace(',', '').strip()
                    return float(price)
            except Exception:
                continue
        return 0.0

    # ---- Data Dictionary ----
    product = {
        "title": safe_find_text_by_css(['h1.prod-ProductTitle', 'h1[itemprop="name"]'], timeout=15),
        "price": extract_price(driver),
        "images": [],
        "about_this_item": "N/A",
        "colors": [],  # will be filled below
        "sizes": [],  # will be filled below
        "product_url": product_url,
        "related_links": [],
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
