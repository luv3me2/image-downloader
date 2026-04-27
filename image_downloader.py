Web Image Downloader - утилита для массового скачивания изображений с веб-страниц
Author: Васильев Александр Александрович
GitHub: https://github.com/luv3me2/image-downloader.git

import requests
import os
import sys
import time
from urllib.parse import urlparse, urljoin
import json
from datetime import datetime

class ImgDownloader:
    """Класс для скачивания изображений"""
    
    def __init__(self, output_dir="images"):
        self.output_dir = output_dir
        self.session = requests.Session()
        # без этого некоторые сайты кидают 403
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        self.stats = {'ok': 0, 'fail': 0}
        
        # создаю папку если её нет
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Создал папку {output_dir}")
    
    def get_html(self, url):
        """качает html страницу"""
        try:
            r = self.session.get(url, timeout=15)
            if r.status_code == 200:
                return r.text
            else:
                print(f"Плохой статус: {r.status_code}")
                return None
        except Exception as e:
            print(f"Ошибка соединения: {e}")
            return None
    
    def extract_img_urls(self, html, base_url):
        """вытаскивает ссылки на картинки из html"""
        urls = []
        
        # ищем img src
        parts = html.split('<img')
        for part in parts[1:]:  # пропускаем первый пустой
            if 'src=' in part:
                # пытаемся найти src="..."
                start = part.find('src="')
                if start == -1:
                    start = part.find("src='")
                    if start == -1:
                        continue
                    quote = "'"
                else:
                    quote = '"'
                
                start += 5  # длина 'src='
                end = part.find(quote, start)
                
                if end != -1:
                    img_url = part[start:end].strip()
                    
                    # нормализуем ссылку
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = urljoin(base_url, img_url)
                    elif not img_url.startswith('http'):
                        img_url = urljoin(base_url, img_url)
                    
                    urls.append(img_url)
        
        # убираем дубликаты сохраняя порядок (для этого используется костыль с dict)
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls
    
    def download_one(self, url, index):
        """скачивает одну картинку"""
        try:
            # жду немного чтобы не заддосить сайт
            time.sleep(0.15)
            
            r = self.session.get(url, timeout=10)
            if r.status_code != 200:
                self.stats['fail'] += 1
                return False
            
            # определяю расширение
            content_type = r.headers.get('content-type', '')
            if 'png' in content_type:
                ext = '.png'
            elif 'gif' in content_type:
                ext = '.gif'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            else:
                # пытаюсь взять из url
                if '.' in url.split('/')[-1]:
                    maybe_ext = url.split('.')[-1].split('?')[0]
                    if len(maybe_ext) <= 4:
                        ext = '.' + maybe_ext
                    else:
                        ext = '.jpg'
                else:
                    ext = '.jpg'
            
            filename = f"{self.output_dir}/img_{index:04d}{ext}"
            
            with open(filename, 'wb') as f:
                f.write(r.content)
            
            self.stats['ok'] += 1
            print(f"OK [{self.stats['ok']}]: {filename}")
            return True
            
        except Exception as ex:
            self.stats['fail'] += 1
            print(f"FAIL: {url[:60]}... ({ex})")
            return False
    
    def run(self, url, limit=None):
        """запускает весь процесс"""
        print(f"\n>>> Скачиваю с {url}")
        
        # получаем html
        html = self.get_html(url)
        if not html:
            print("Не удалось загрузить страницу")
            return
        
        # находим картинки
        img_urls = self.extract_img_urls(html, url)
        print(f"Найдено {len(img_urls)} картинок")
        
        if limit and limit < len(img_urls):
            img_urls = img_urls[:limit]
            print(f"Ограничился {limit} штуками")
        
        # качаем
        print("\nНачинаю загрузку...")
        for i, img_url in enumerate(img_urls):
            self.download_one(img_url, i)
        
        # статистика
        print(f"\nГотово! Скачано: {self.stats['ok']}, Ошибок: {self.stats['fail']}")
        
        # сохраняю лог
        log_data = {
            'url': url,
            'date': str(datetime.now()),
            'downloaded': self.stats['ok'],
            'failed': self.stats['fail']
        }
        with open(f"{self.output_dir}/log.json", 'w') as f:
            json.dump(log_data, f, indent=2)
        print(f"Лог сохранён в {self.output_dir}/log.json")


def main():
    print("=" * 50)
    print("Скачиватель картинок v1.0")
    print("=" * 50)
    
    # спрашиваю сайт
    site = input("Введите URL сайта: ").strip()
    if not site:
        print("Надо ввести сайт!")
        sys.exit(1)
    
    if not site.startswith('http'):
        site = 'https://' + site
    
    # спрашиваю лимит
    limit_input = input("Максимум картинок (Enter = без лимита): ").strip()
    limit = int(limit_input) if limit_input else None
    
    # скачиваю
    downloader = ImgDownloader("my_images")
    downloader.run(site, limit)


if __name__ == "__main__":
    main()
