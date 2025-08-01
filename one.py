task2.py
import time
import pandas as pd
from pymongo import MongoClient
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---- MongoDB Setup ----
client = MongoClient("mongodb://localhost:27017/")
db = client["Walmart_data"]
collection = db["consoles"]

# ---- Scraping Function ----
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
            imgs = driver.find_elements(By.CSS_SELECTOR, 'img[alt*="color"], img[alt*="Color"]')
            for img in imgs:
                alt = img.get_attribute('alt')
                if alt:
                    color_names.add(alt.strip())
        return list(color_names) or ["N/A"]

    def extract_sizes(driver):
        size_names = set()
        size_selectors = [
            'ul[data-tl-id*="size"] button span',
            'ul[data-tl-id*="size"] label span',
            'div[data-automation-id="size-picker"] label',
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
        return list(size_names) or ["N/A"]

    def extract_price(driver):
        selectors = [
            'span[itemprop="price"]',
            'span[data-automation-id="product-price"]',
            'span.price-characteristic',
            'div[data-testid="price"] span'
        ]
        for sel in selectors:
            try:
                elem = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                )
                text = elem.text.strip()
                if text:
                    return float(text.replace('$', '').replace(',', '').strip())
            except:
                continue
        return 0.0

    product = {
        "client_name": client_name,
        "category": category,
        "task_id": task_id,
        "title": safe_find_text_by_css(['h1.prod-ProductTitle', 'h1[itemprop="name"]'], timeout=15),
        "price": extract_price(driver),
        "images": [],
        "about_this_item": [],
        "colors": extract_colors(driver),
        "sizes": extract_sizes(driver),
        "product_url": product_url,
        "related_links": [],
        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        scroll_to_element('div[data-testid="media-gallery"]')
        image_urls = []
        thumbs = driver.find_elements(By.CSS_SELECTOR, 'img[data-testid="media-gallery-thumbnail-image"]')
        for thumb in thumbs[:5]:
            try:
                thumb.click()
                time.sleep(1)
                main_img = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="media-gallery"] img')
                src = main_img.get_attribute("src")
                if src and src not in image_urls:
                    image_urls.append(src)
            except:
                continue
        product["images"] = image_urls
    except:
        product["images"] = []

    try:
        scroll_to_element('div.dangerous-html.mb3', timeout=15)
        about_elem = WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.dangerous-html.mb3'))
        )
        paragraphs = about_elem.find_elements(By.TAG_NAME, 'p')
        product["about_this_item"] = [p.text.strip() for p in paragraphs if p.text.strip()]
    except:
        product["about_this_item"] = []

    try:
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/ip/"]')
        product["related_links"] = list({a.get_attribute("href").split("?")[0] for a in links if a.get_attribute("href")})
    except:
        product["related_links"] = []

    # ---- Save to MongoDB ----
    try:
        collection.insert_one(product)
        print("🍃 Saved to MongoDB")
    except Exception as e:
        print("❌ MongoDB Error:", e)

    # ---- Save to CSV ----
    try:
        df = pd.DataFrame([product])
        df.to_csv("walmart_data.csv", index=False)
        print("📁 Saved to CSV")
    except Exception as e:
        print("❌ CSV Error:", e)

    driver.quit()
    return product
