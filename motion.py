from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from os.path import exists
from os import mkdir
import requests
import time

from const import assets
from os import environ as options


blacklist = ["inter", "segment", "facebook", "fullstory", "loggly.js", "app-"]
notions = {}
user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_0 like Mac OS X) AppleWebKit/602.1.38 (KHTML, like Gecko) Version/10.0 Mobile/14A300 Safari/602.1'
visited = set()
notions = {}


def motion(is_mobile=False):
    global visited, notions
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    visited = set()
    notions = {}
    print("Parsing index...")
    if is_mobile:
        print("Building mobile version...")
        chrome_options.add_argument('--user-agent=' + user_agent)
    driver = webdriver.Chrome(chrome_options=chrome_options)
    n = Notion(options['index'], driver, options=options, is_index=True, is_mobile=is_mobile)
    n.mod()
    print("Index page looks good.")
    n.walk()
    n.save()
    print("Site generated successfully.")
    driver.quit()


def download_file(url, local_filename):
    # https://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py#16696317
    if local_filename.startswith("/"):
        local_filename = local_filename[1:]
    local_filename = "site/" + local_filename
    if exists(local_filename):
        print("File " + local_filename + " found. Skipping.")
        return
    md(local_filename)
    print("Downloading: " + url + " to " + local_filename)
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                # f.flush() commented by recommendation from J.F.Sebastian
    return local_filename


def md(local_filename):
    folders = [i for i in local_filename.split("/") if i]
    if folders:
        tmp = folders[0]
        for folder in folders[1:]:
            if not exists(tmp):
                print("Making missing directory: " + tmp)
                mkdir(tmp)
            tmp += "/" + folder


class Notion:
    def __init__(self, url, driver, options=None, is_index=False, wait=0, is_mobile=False):
        self.driver = driver
        print("Visiting " + url)
        self.is_index = is_index
        self.is_mobile = is_mobile
        self.url = url
        self.driver.get(url)
        time.sleep(wait)
        self.dom = BeautifulSoup(driver.page_source, "html.parser")
        self.links = set()
        if not options:
            options = {}
        self.options = options
        if is_index:
            self.filename = "index.html"
            self.init_site()
        else:
            self.filename = '-'.join(url.split("/")
                                     [-1].split('-')[:-1]) + ".html"

    def init_site(self):
        for f in assets:
            download_file("https://notion.so/" + f, f)

    def mod(self, no_retry=False):
        try:
            self.meta()
            self.remove_overlay()
            self.parse_links()
            self.remove_scripts()
            self.save_assets()
        except:
            time.sleep(2)
            print("Exception occurred, sleep for 2 secs and retry...")
            self.dom = BeautifulSoup(self.driver.page_source, "html.parser")
            if no_retry:
                raise
            else:
                self.mod(no_retry=True)

    def save(self):
        if self.is_mobile:
            local_filename = "site/m/" + self.filename
        else:
            local_filename = "site/" + self.filename
        with open(local_filename, "w") as f:
            f.write(str(self.dom))

    def parse_links(self):
        for a in self.dom.find_all("a"):
            href = a['href']
            if href.startswith('/'):
                if href == '/login':
                    a.decompose()
                elif href[1:] == self.options["index"].split("/")[-1]:
                    a['href'] = '/'
                else:
                    if self.is_index:
                        self.links.add(href)
                    a['href'] = "/" + \
                        '-'.join(href.split("/")[-1].split('-')[:-1])

    def meta(self):
        if self.dom.find('html').has_attr("manifest"):
            self.dom.find('html')["manifest"] = ''
        titles = [i.text.strip() for i in self.dom.find_all(
            "div") if (i.has_attr("style") and "2.25em" in i["style"])]
        title = titles[0]
        if self.is_index:
            self.title = title
            self.options["site_title"] = title
        else:
            self.title = title + ' ' + \
                self.options["title_sep"] + ' ' + self.options["site_title"]
        self.dom.find("title").string = self.title
        self.dom.find("meta", attrs={"name": "twitter:site"})[
            "content"] = self.options["twitter"]
        page_path = '-'.join(self.url.split("/")[-1].split('-')[:-1])
        self.dom.find("meta", attrs={"name": "twitter:url"})[
            "content"] = self.options["base_url"] + page_path
        self.dom.find("meta", attrs={"property": "og:url"})[
            "content"] = self.options["base_url"] + page_path
        self.dom.find("meta", attrs={"property": "og:title"})[
            "content"] = self.title
        self.dom.find("meta", attrs={"name": "twitter:title"})[
            "content"] = self.title
        self.dom.find("meta", attrs={"property": "og:site_name"})[
            "content"] = self.options["site_title"]
        self.dom.find("meta", attrs={"name": "description"})[
            "content"] = self.options["description"]
        self.dom.find("meta", attrs={"name": "twitter:description"})[
            "content"] = self.options["description"]
        self.dom.find("meta", attrs={"property": "og:description"})[
            "content"] = self.options["description"]
        print("Title: " + self.dom.find("title").string)
        imgs = [i for i in self.dom.find_all('img') if i.has_attr(
            "style") and "30vh" in i["style"]]
        if imgs:
            img_url = self.options["base_url"] + imgs[0]["src"][1:]
            self.dom.find("meta", attrs={"property": "og:image"})[
                "content"] = img_url
            self.dom.find("meta", attrs={"name": "twitter:image"})[
                "content"] = img_url
        else:
            self.dom.find("meta", attrs={"property": "og:image"}).decompose()
            self.dom.find("meta", attrs={"name": "twitter:image"}).decompose()

    def remove_scripts(self):
        for s in self.dom.find_all("script"):
            if s.has_attr("src"):
                if any([bool(b in s["src"]) for b in blacklist]):
                    pass
                else:
                    continue
            s.decompose()
        for s in self.dom.find_all("noscript"):
            s.decompose()

    def save_assets(self):
        for css in self.dom.find_all("link"):
            if css["href"].startswith("/") and ("stylesheet" in css["rel"]):
                download_file("https://notion.so" +
                              css["href"], css["href"][1:])
        for img in self.dom.find_all("img"):
            if img["src"].startswith("/"):
                download_file("https://notion.so" + img["src"], img["src"][1:])
#             elif img["src"].startswith("https://notion.imgix.net/"):
#                 download_file(img["src"], img)
        for script in self.dom.find_all("script"):
            if script.has_attr("src") and script["src"].startswith("/"):
                download_file("https://notion.so" +
                              script["src"], script["src"][1:])

    def remove_overlay(self):
        overlay = self.dom.find(class_="notion-overlay-container")
        if overlay:
            overlay.decompose()

    def walk(self):
        global visited
        for link in self.links:
            if link not in visited:
                page = Notion("https://notion.so" + link, self.driver, options=options, is_mobile=self.is_mobile)
                notions[link] = page
                page.mod()
                page.save()
                visited.add(link)
                page.walk()


if __name__ == "__main__":
    motion()
    motion(is_mobile=True)
