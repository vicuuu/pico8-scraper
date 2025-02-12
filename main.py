import sys
import io

buffer = io.StringIO()
sys.stdout = sys.stderr = buffer

import os
import requests
import threading
from bs4 import BeautifulSoup
import tkinter 
import tkinter.filedialog as filedialog
import eel

eel.init('web')

@eel.expose
def choose_folder():
	root = tkinter.Tk()
	root.withdraw()
	root.wm_attributes('-topmost', 1)
	folder = filedialog.askdirectory()
	return folder

@eel.expose
def start_scraping(save_path, max_pages, min_stars):
    if not save_path:
        eel.update_status('🚫 Select a folder to save!')
        return
    
    try:
        max_pages = int(max_pages)
        min_stars = int(min_stars)
        if max_pages <= 0:
            raise ValueError
    except ValueError:
        eel.update_status('🚫 Enter a valid number of pages!')
        return

    threading.Thread(target=scrape_data, args=(save_path, max_pages, min_stars)).start()

def scrape_data(save_path, max_pages, min_stars):
    base_url = 'https://www.lexaloffle.com/bbs/?cat=7&carts_tab=1'
    processed_ids = set()
    game_list = [] 

    with requests.Session() as session:
        for page_number in range(1, max_pages + 1):
            eel.update_status(f'📄 Processing page {page_number}...')
            url = f'{base_url}&page={page_number}&mode=carts'
            game_urls = get_game_links(url, session)

            if not game_urls:
                eel.update_status('🚫 No games found to download!')
                break

            for game_id, game_url in game_urls:
                if game_id in processed_ids:
                    continue
                
                title, image_link, stars = get_game_details(game_url, session)
                if stars >= min_stars and image_link:
                    game_list.append((game_id, title, image_link, stars))
                    processed_ids.add(game_id)

        total_valid_games = len(game_list)
        if total_valid_games == 0:
            eel.update_status('🚫 No games found to download!')
            return

        for index, (game_id, title, image_link, stars) in enumerate(game_list, start=1):
            safe_title = "".join(x for x in title if x.isalnum() or x in "._-`' ").rstrip()
            file_path = os.path.join(save_path, f'{safe_title}.png')

            if os.path.exists(file_path):
                eel.update_status(f'⏭️ Skipping {title} (already downloaded) ⭐ {stars}')
            else:
                eel.update_status(f'⬇️ Downloading: {title} ⭐ {stars}')
                download_image(image_link, title, save_path)

            eel.update_progress(index / total_valid_games)

    eel.update_status('🚀 Download complete!')


def get_game_links(url, session):
    try:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        game_containers = soup.find_all('div', id=lambda x: x and x.startswith('pdat_'))
        return [(container['id'].split('_')[1], f'https://www.lexaloffle.com/bbs/?pid={container["id"].split("_")[1]}#p') for container in game_containers]
    except requests.RequestException:
        return []

def get_game_details(game_url, session):
    try:
        response = session.get(game_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('div', style=lambda value: value and 'font-size:32px' in value)
        title = title.find('a').get_text(strip=True) if title else 'Unknown game'

        stars = 0
        star_div = soup.find('div', class_="form_button")
        if star_div:
            stars_span = star_div.find('div', style=lambda value: value and 'color:#999' in value)
            if stars_span:
                stars = int(stars_span.get_text(strip=True))

        image_link = None
        cartridge_anchor = soup.find('a', title='Open Cartridge File', href=True)
        if cartridge_anchor:
            image_link = cartridge_anchor['href']
            if not image_link.startswith('http'):
                image_link = 'https://www.lexaloffle.com' + image_link

        return title, image_link, stars
    except requests.RequestException:
        return 'Unknown game', None, 0

def download_image(url, title, save_path):
    try:
        response = requests.get(url)
        response.raise_for_status()
        os.makedirs(save_path, exist_ok=True)

        safe_title = "".join(x for x in title if x.isalnum() or x in "._-`' ").rstrip()
        file_path = os.path.join(save_path, f'{safe_title}.png')

        with open(file_path, 'wb') as file:
            file.write(response.content)

        eel.update_status(f'✅ {safe_title} downloaded!')
    except requests.RequestException:
        eel.update_status(f'❌ Failed to download {title}')

eel.start('index.html', size=(600, 800))
