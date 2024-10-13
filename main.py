import os
import requests
from bs4 import BeautifulSoup
import customtkinter as ctk
from tkinter import messagebox
import threading

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("PICO-8 Scraper")
        self.geometry("600x450")  

        # Grid configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1) 
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=0)

        # Save Path
        self.label_save_path = ctk.CTkLabel(self, text="Path")
        self.label_save_path.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.entry_save_path = ctk.CTkEntry(self, placeholder_text="Select folder", width=200)
        self.entry_save_path.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.button_browse = ctk.CTkButton(self, text="Browse", command=self.browse_folder)
        self.button_browse.grid(row=0, column=2, padx=10, pady=10, sticky="ew")

        # Number of Pages
        self.label_pages = ctk.CTkLabel(self, text="Pages")
        self.label_pages.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.entry_pages = ctk.CTkEntry(self, placeholder_text="Select number", width=200)
        self.entry_pages.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        # Minimum Star Rating
        self.label_min_stars = ctk.CTkLabel(self, text="Min Stars")
        self.label_min_stars.grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.entry_min_stars = ctk.CTkEntry(self, placeholder_text="Enter minimum stars", width=200)
        self.entry_min_stars.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # Status Display
        self.label_status = ctk.CTkLabel(self, text="Status")
        self.label_status.grid(row=3, column=0, padx=10, pady=10, sticky="ne")
        self.textbox_status = ctk.CTkTextbox(self, height=150)
        self.textbox_status.grid(row=3, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Progress Bar
        self.label_progress = ctk.CTkLabel(self, text="Progress")
        self.label_progress.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.grid(row=4, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        self.progress_bar.set(0)

        # Start Button
        self.button_start = ctk.CTkButton(self, text="Start", command=self.start_scraping, height=40)
        self.button_start.grid(row=5, column=1, columnspan=2, padx=10, pady=10, sticky="ew")


    def browse_folder(self):
        folder = ctk.filedialog.askdirectory()
        if folder:
            self.entry_save_path.delete(0, ctk.END)
            self.entry_save_path.insert(0, folder)

    def update_status(self, text):
        self.textbox_status.configure(state="normal")
        self.textbox_status.insert(ctk.END, text + '\n')
        self.textbox_status.configure(state="disabled")
        self.textbox_status.yview(ctk.END)

    def update_progress(self, value):
        self.progress_bar.set(value)

    def get_game_links(self, url, session):
        try:
            response = session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            game_containers = soup.find_all('div', id=lambda x: x and x.startswith('pdat_'))
            if not game_containers:
                self.update_status(f'No game containers found on {url}')
            
            game_urls = [
                (container['id'].split('_')[1], f'https://www.lexaloffle.com/bbs/?pid={container["id"].split("_")[1]}#p')
                for container in game_containers
            ]
            return game_urls
        except requests.RequestException as e:
            self.update_status(f'Error fetching game links: {e}')
            return []

    def get_game_details(self, game_url, session):
        try:
            response = session.get(game_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract title
            title_div = soup.find('div', style=lambda value: value and 'font-size:32px' in value)
            title = title_div.find('a').get_text(strip=True) if title_div else 'Unknown Title'

            # Extract number of stars
            star_div = soup.find('div', class_="form_button")
            if star_div:
                stars_span = star_div.find('div', style=lambda value: value and 'color:#999' in value)
                if stars_span:
                    stars = int(stars_span.get_text(strip=True))
                else:
                    stars = 0 
            else:
                stars = 0  

            # Extract cartridge link
            cartridge_link = None
            cartridge_anchor = soup.find('a', title='Open Cartridge File', href=True)
            if cartridge_anchor:
                cartridge_link = cartridge_anchor['href']
                if not cartridge_link.startswith('http'):
                    cartridge_link = 'https://www.lexaloffle.com' + cartridge_link

            return title, cartridge_link, stars
        except requests.RequestException as e:
            self.update_status(f'Error fetching game details: {e}')
            return 'Unknown Title', None, 0

    def download_image(self, url, title, save_path):
        if url:
            try:
                response = requests.get(url)
                response.raise_for_status()
                
                os.makedirs(save_path, exist_ok=True)
                
                safe_title = "".join(x for x in title if x.isalnum() or x in "._-`' ").rstrip()
                file_path = os.path.join(save_path, f'{safe_title}.png')
                
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                
                self.update_status(f'- {safe_title}')
            except requests.RequestException as e:
                self.update_status(f'Failed to download image from {url}: {e}')
        else:
            self.update_status('No image URL provided')

    def scrape_data(self, save_path, max_pages, min_stars):
        base_url = 'https://www.lexaloffle.com/bbs/?cat=7&carts_tab=1'
        games = []
        processed_ids = set()
        page_number = 1
        valid_games_count = 0  
        total_valid_games = 0  

        with requests.Session() as session:
            while page_number <= max_pages:
                self.update_status(f'\nCalculating. Please be patient for a moment ( ͡° ͜ʖ ͡°)\n')
                url = f'{base_url}&page={page_number}&mode=carts'
                self.update_status(f'• PAGE {page_number}')
                
                game_urls = self.get_game_links(url, session)
                
                if not game_urls:
                    self.update_status('No more game URLs found. Exiting...')
                    break

                page_valid_games = []

                for game_id, game_url in game_urls:
                    if game_id in processed_ids:
                        continue
                    
                    title, image_link, stars = self.get_game_details(game_url, session)
                    
                    if stars >= min_stars:  
                        total_valid_games += 1  
                        page_valid_games.append((title, game_url, image_link, stars)) 

                for title, game_url, image_link, stars in page_valid_games:
                    valid_games_count += 1  
                    
                    if image_link:
                        self.update_status(f'Downloading: {title} - Stars: {stars}')
                        self.download_image(image_link, title, save_path)
                        processed_ids.add(game_id)

                    if total_valid_games > 0:  
                        self.update_progress(valid_games_count / total_valid_games)

                page_number += 1

        messagebox.showinfo("Info", "All done :)")
        self.update_progress(1)  

    def start_scraping(self):
        save_path = self.entry_save_path.get()
        max_pages = int(self.entry_pages.get())
        min_stars = int(self.entry_min_stars.get() or 0)  
        
        if not save_path:
            messagebox.showerror("Error", "Please select a folder to save images")
            return
        
        if max_pages <= 0:
            messagebox.showerror("Error", "Number of pages must be greater than 0")
            return
        
        self.update_status('Starting scraping')
        self.update_progress(0)  
        
        scraping_thread = threading.Thread(target=self.scrape_data, args=(save_path, max_pages, min_stars))
        scraping_thread.start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
