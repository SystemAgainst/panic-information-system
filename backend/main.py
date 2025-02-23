import json
import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin


BASE_URL = "https://www.avito.ru/artem/zemelnye_uchastki/prodam"

def apply_filters(driver):
    """Применяем фильтр цены до 1 200 000"""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-marker='price-to/input']"))
        )

        max_price_input = driver.find_element(By.CSS_SELECTOR, "input[data-marker='price-to/input']")
        
        # Очищаем поле полностью
        max_price_input.click()
        max_price_input.send_keys(Keys.CONTROL + "a")  # Выделяем весь текст
        max_price_input.send_keys(Keys.BACKSPACE)  # Удаляем
        
        time.sleep(1)  # Ждем, чтобы поле очистилось

        # Вводим цену по одной цифре
        max_price = "1200000"
        for digit in max_price:
            max_price_input.send_keys(digit)
            time.sleep(0.2)  # Небольшая задержка после каждой цифры

        time.sleep(2)  # Даем время полю обновиться

        # Нажимаем кнопку "Показать" для подтверждения фильтрации
        apply_button = driver.find_element(By.CSS_SELECTOR, "button[data-marker='search-filters/submit-button']")
        apply_button.click()

        # Ждем обновления страницы
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-marker='catalog-serp']"))
        )

        print("✅ Фильтр цены применен: до 1 200 000 ₽")
        time.sleep(2)

    except Exception as e:
        print(f"❌ Ошибка при вводе фильтра цены: {e}")

def get_all_listings():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = uc.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(BASE_URL)
    print("🌍 Открыта страница:", driver.current_url)

    apply_filters(driver)  # Применяем фильтр
    current_url = driver.current_url  # Сохраняем актуальный URL

    print("🔄 Текущий URL после применения фильтра:", current_url)

    page = 1
    all_results = []
    global_index = 1  # Глобальный счетчик объявлений

    while True:
        paginated_url = f"{current_url}&p={page}"  # Теперь фильтр сохраняется при пагинации
        print(f"📄 Сканирую страницу {page}: {paginated_url}")
        driver.get(paginated_url)

        # Ожидание загрузки объявлений
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-marker='item']"))
            )
        except Exception as e:
            print(f"⚠️ Ошибка при загрузке страницы {page}: {e}")
            break

        soup = BeautifulSoup(driver.page_source, "html.parser")
        listings = soup.find_all("div", {"data-marker": "item"})
        print(f"✅ Найдено объявлений на странице {page}: {len(listings)}")

        for item in listings:
            title_tag = item.find("a", {"data-marker": "item-title"})
            price_tag = item.find("p", {"data-marker": "item-price"})
            link_tag = item.find("a", {"data-marker": "item-title"})
            id_tag = item.get("data-item-id")  # Получаем ID объявления

            title_text = title_tag.text.strip() if title_tag else "Нет заголовка"
            price_value = price_tag.find("meta", {"itemprop": "price"})["content"] if price_tag else "Нет цены"
            price_text = price_tag.find("span").text.strip() if price_tag and price_tag.find("span") else "Нет цены"
            link_href = urljoin("https://www.avito.ru", link_tag["href"]) if link_tag else "Нет ссылки"
            item_id = id_tag if id_tag else "Нет ID"

            all_results.append({
                "order": global_index,
                "id": item_id,
                "title": title_text,
                "price": price_value,
                "formatted_price": price_text,
                "link": link_href
            })

            global_index += 1  # Увеличиваем счетчик объявлений

        # Проверяем кнопку "Следующая страница"
        next_button = soup.find("a", {"data-marker": "pagination-button/nextPage"})
        if next_button:
            page += 1
            time.sleep(3)  # Уменьшили задержку
        else:
            print("🏁 Достигнута последняя страница.")
            break

    driver.quit()

    # Сохраняем в JSON
    with open("all_results.json", "w", encoding="utf-8") as file:
        json.dump(all_results, file, indent=4, ensure_ascii=False)

    print(f"📂 Данные успешно сохранены в all_results.json ({len(all_results)} объявлений)")


def main():
    get_all_listings()


if __name__ == "__main__":
    main()