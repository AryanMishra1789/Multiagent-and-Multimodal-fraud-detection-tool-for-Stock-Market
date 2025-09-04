

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# URL of SEBI Research Analyst page
URL = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=14"


options = Options()
options.add_argument("--headless")  # Run in headless mode (no browser window)
driver = webdriver.Chrome(options=options)


all_html = []
try:

    driver.get(URL)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".fixed-table-body"))
    )

    # Find the total number of pages from the pagination
    pagination = driver.find_elements(By.CSS_SELECTOR, ".pagination_inner p")
    total_pages = 1
    if pagination:
        import re
        text = pagination[0].text  # e.g., '1 to 25 of 1656 records'
        match = re.search(r'of (\d+) records', text)
        if match:
            total_records = int(match.group(1))
            total_pages = (total_records // 25) + (1 if total_records % 25 else 0)
    print(f"Total pages: {total_pages}")

    page = 1
    while True:
        # Wait for table to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".fixed-table-body"))
        )
        all_html.append(driver.page_source)
        print(f"Saved page {page}")
        try:
            # Always re-locate the Next button after each page load
            pagination = driver.find_elements(By.CSS_SELECTOR, ".pagination_inner p")
            if pagination:
                print(f"Pagination text: {pagination[0].text}")
            next_btns = driver.find_elements(By.XPATH, "//li/a[contains(@title, 'Next') or contains(text(), '›') or contains(@class, 'fa-angle-double-right')]")
            next_btn = None
            for btn in next_btns:
                parent_li = btn.find_element(By.XPATH, "..")
                if 'disabled' not in parent_li.get_attribute('class'):
                    next_btn = btn
                    break
            if not next_btn:
                print(f"No enabled 'Next' button found. Stopping at page {page}.")
                break
            driver.execute_script("arguments[0].scrollIntoView();", next_btn)
            next_btn.click()
            page += 1
            # Wait for the page number to update (pagination text changes)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".fixed-table-body"))
            )
            time.sleep(1)  # Give time for DOM to update
        except Exception as e:
            print(f"No more 'Next' button found or error: {e}. Stopping at page {page}.")
            break
    # Save all HTMLs concatenated
    with open("sebi_advisors_full.html", "w", encoding="utf-8") as f:
        for html in all_html:
            f.write(html)
            f.write("\n<!-- PAGE BREAK -->\n")
    print(f"Saved {len(all_html)} pages of advisor records to sebi_advisors_full.html")
finally:
    driver.quit()
