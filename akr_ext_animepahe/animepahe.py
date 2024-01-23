import time
import math
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from akr_extensions_sdk import AnimeExtension


class AnimePahe(AnimeExtension):

    def __init__(self, debug):
        AnimeExtension.__init__(self, debug)
        options = webdriver.ChromeOptions()
        prefs = {"download.default_directory" : os.getcwd() }
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("prefs",prefs)
        self._driver = webdriver.Chrome(options=options)

    def run (self, anime_name):
        self.search(anime_name)
        self.list_anime()
        self.get_anime_choice() # super class
        self.get_anime_details()
        self.get_episode()
        self.download_episode()
    
    def search(self, anime_name):
        self._driver.get(f"https://animepahe.ru/api?m=search&q={anime_name}")
        input("You need to solve a captcha before proceeding. "
              "You chrome would be opened for you to solve it. "
              "Once you've solved it come to the terminal where you're "
              "running the app and press the enter key to proceed."
        )
        text =  self._driver.find_element(By.TAG_NAME, "pre")
        self.jsonres = json.loads(text.get_attribute("innerHTML"))
        
        

    def list_anime(self):
        animes = [
            f"{i+1}. {self.jsonres['data'][i]['title']}"
            for i in range(len(self.jsonres['data']))
        ]

        print(
            "Animes:\n" +
            "\n".join(animes) + "\n\n"
        )

    def get_anime_details(self):
        self._driver.get(
            f"https://animepahe.ru/api?m=release&id={self.jsonres['data'][self._choice-1]['session']}&sort=episode_desc&page=1"
        )
        text =  self._driver.find_element(By.TAG_NAME, "pre")
        self.anime_details = json.loads(text.get_attribute("innerHTML"))
    
    def get_episode(self): # This will cover other things until the download
        self._driver.get(
            f"https://animepahe.ru/api?m=release&id={self.jsonres['data'][self._choice-1]['session']}&sort=episode_desc&page=1"
        )
        episode = self._ask_episode()
        episode_link = self._get_episode_link(episode)
        
        # Get quality lists
        self.quality_link = self._which_quality(episode_link)
        


    def download_episode(self):
        self._driver.get(self.quality_link)

        # Get link from continue button
        print("Downloading...")
        print("Please wait for it to begin...")
        for i in range(1, 6):
            try:
                a = self._driver.find_element(By.XPATH, "//a[text()='Continue']")
                link_to_download = a.get_attribute("href")
                self._driver.get(link_to_download)
                break
            except:
                # print(f"{i}/{5} retries, waiting 3s")
                time.sleep(3)

        self._driver.execute_script("""
            document.querySelector("body > div:last-of-type").style.display = "none"
        """)

        try:
            # click button
            self._driver.find_element(By.CSS_SELECTOR, ".download-form button").click()
            print("Leaving browser tab open, while downloading...")
        except:
            print("Something is up here, please check")

    def _ask_episode(self):
        total_episodes = self.anime_details['total']
        
        ans = int(input(f"There are {total_episodes} episodes, which do you want to download? ").strip())
        if 0 < ans and ans <= total_episodes:
            return ans
        else:
            return self._ask_episode()
    
    def _get_episode_link(self, episode):
        page = math.ceil(episode/30)
        position = (episode - (page - 1) * 30) - 1

        self._driver.get(
            f"https://animepahe.ru/api?m=release&id={self.jsonres['data'][self._choice-1]['session']}&sort=episode_asc&page={page}"
        )
        text =  self._driver.find_element(By.TAG_NAME, "pre")
        response = json.loads(text.get_attribute("innerHTML"))
        
        return f"https://animepahe.ru/play/{self.jsonres['data'][self._choice-1]['session']}/{response['data'][position]['session']}"


    def _which_quality(self, episode_link):
        # Get quality the user wants
        if (self._debug):
            print("Episode link:", episode_link)

        self._driver.get(episode_link)

        # time.sleep(0)
        qualities = []

        for a in self._driver.find_elements(By.CSS_SELECTOR, "#pickDownload .dropdown-item"):
            quality_text = a.get_attribute("innerText").split(" ")
            sub_dub = 'dub' if quality_text[-1] == 'eng' else 'sub'
            quality = quality_text[2]
            size = quality_text[3][1:-1]
            quality = {
                "name": f"{quality}{' ' * (15 - len(quality))}{size}{' ' * (15 - len(size))}{sub_dub}",
                "link": a.get_attribute("href")
            }
            qualities.append(quality)
        
        text = "\nHere are qualities found:\n"
        text += "\n".join([
            f"{i+1}. {qualities[i]['name']}"
            for i in range(len(qualities))
        ]) + "\n\n"
        text += "Which one do you want to download: "
        ans = int(input(text)) - 1

        if 0 <= ans and ans < len(qualities):
            return qualities[ans]["link"]
        else:
            return self._which_quality(episode_link)

