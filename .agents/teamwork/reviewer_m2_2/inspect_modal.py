import sys
from bs4 import BeautifulSoup

soup = BeautifulSoup(open('index.html', encoding='utf-8'), 'html.parser')
modal = soup.find(id='legal-modal')
card = modal.find(class_='obs-modal-card')
selectors = 'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
found = card.select(selectors)
print(f'Total focusable elements in #legal-modal: {len(found)}')
for idx, el in enumerate(found):
    desc = el.text.strip()[:30].encode('ascii', 'replace').decode('ascii')
    print(f'  {idx}: <{el.name} class="{el.get("class")}" id="{el.get("id")}"> text="{desc}"')
