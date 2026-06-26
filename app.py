from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ua = UserAgent()

def find_contacts(query: str):
    result = {
        'name': query,
        'website': '',
        'emails': [],
        'phones': [],
        'social': {},
        'source': 'Mega Parser'
    }
    
    # Поиск через DuckDuckGo
    try:
        url = f"https://html.duckduckgo.com/html/?q={query}+official+website"
        resp = requests.get(url, headers={'User-Agent': ua.random}, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if 'http' in href and 'duckduckgo' not in href:
                clean = re.sub(r'^.*?http', 'http', href)
                if clean.startswith('http'):
                    result['website'] = clean
                    break
    except:
        pass
    
    # Парсим сайт
    if result['website']:
        try:
            resp = requests.get(result['website'], headers={'User-Agent': ua.random}, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text()
            
            emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', text)
            result['emails'] = list(set(emails))[:10]
            
            phones = re.findall(r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}', text)
            result['phones'] = list(set(phones))[:5]
            
            patterns = {
                'linkedin': r'linkedin\.com/',
                'telegram': r'(?:t\.me/|telegram\.me/)',
                'instagram': r'instagram\.com/',
                'facebook': r'facebook\.com/',
                'twitter': r'(?:twitter\.com/|x\.com/)'
            }
            for link in soup.find_all('a', href=True):
                href = link['href']
                for key, pattern in patterns.items():
                    if re.search(pattern, href) and not result['social'].get(key):
                        result['social'][key] = href
        except:
            pass
    
    return result

@app.post("/api/parse")
async def parse(query: str = Form(...)):
    result = find_contacts(query)
    return JSONResponse(result)

@app.get("/api/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
