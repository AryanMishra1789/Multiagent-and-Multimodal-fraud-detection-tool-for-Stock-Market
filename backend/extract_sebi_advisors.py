import os
import csv
from bs4 import BeautifulSoup


# Use the multi-page HTML file
HTML_FILE = "sebi_advisors_full.html"  # Output from Selenium script
OUTPUT_CSV = "sebi_advisors_clean.csv"

fields = ["Name", "Registration No.", "E-mail", "Contact Person", "Address", "Correspondence Address", "Validity"]


def extract_advisors(html_file, output_csv):
    with open(html_file, encoding="utf-8") as f:
        html = f.read()
    pages = html.split("<!-- PAGE BREAK -->")
    advisors = []
    for page_html in pages:
        soup = BeautifulSoup(page_html, "html.parser")
        advisor_blocks = soup.find_all("div", class_="fixed-table-body")
        for block in advisor_blocks:
            record = {field: "" for field in fields}
            for card in block.find_all("div", class_="card-view"):
                title = card.find("div", class_="title")
                value = card.find("div", class_="value")
                if not title or not value:
                    continue
                key = title.get_text(strip=True).replace(':', '')
                val = value.get_text(strip=True).replace('\u2022', '').replace('\xa0', ' ')
                if key in record:
                    record[key] = val
            # Only add if Name and Registration No. are present
            if record["Name"] and record["Registration No."]:
                advisors.append(record)
    # Write to CSV
    with open(output_csv, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(advisors)
    print(f"Extracted {len(advisors)} advisors to {output_csv}")

if __name__ == "__main__":
    extract_advisors(HTML_FILE, OUTPUT_CSV)
