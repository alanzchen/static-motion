from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from os.path import exists
from os import mkdir
import requests
import time
from pyquery import PyQuery as pq
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
    for notion in notions.values():
        notion.save()
    n.save()
    print("Site generated successfully.")
    driver.quit()


def download_file(url, local_filename, overwrite=False):
    # https://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py#16696317
    if local_filename.startswith("/"):
        local_filename = local_filename[1:]
    local_filename = "site/" + local_filename
    if exists(local_filename) and not overwrite:
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
        if url.startswith("https://"):
            self.driver.get(url)
        else:
            self.driver.get("https://notion.so" + url)
        time.sleep(wait)
        self.dom = BeautifulSoup(driver.page_source, "html.parser")
        self.source = self.driver.page_source
        self.wait_spinner()
        self.divs = [d for d in self.dom.find_all("div") if d.has_attr("data-block-id")]
        self.links = set()
        self.code_block = []
        if not options:
            options = {}
        self.options = options
        if is_index:
            self.filename = "index.html"
            self.init_site()
        else:
            url_list = url.split("/")[-1].split('-')
            if len(url_list) > 1:
                self.filename = '-'.join(url_list[:-1]) + ".html"
            else:
                self.filename = url_list[0] + ".html"

    def wait_spinner(self):
        i = 0
        while (self.dom.find(class_="loading-spinner")):
            i += 1
            print("Waiting for spinner... " + str(i))
            time.sleep(1)
            self.dom = BeautifulSoup(self.driver.page_source, "html.parser")
            self.source = self.driver.page_source

    def init_site(self):
        for f in assets:
            download_file("https://notion.so/" + f, f)
        if 'favicon' in self.options:
            download_file(self.options['favicon'], "images/favicon.ico")
        if 'apple_touch_icon' in self.options:
            download_file(self.options['apple_touch_icon'], 'images/logo-ios.png')
        if 'atom' in self.options:
            download_file(self.options['atom'], 'feed', overwrite=True)

    def mod(self, no_retry=False):
        try:
            self.save_assets()
            self.meta()
            # self.remove_overlay()
            self.clean()
            self.parse_links()
            self.remove_scripts()
            self.iframe()
            self.div()
            self.disqus()
            self.gen_html()
        except:
            time.sleep(2)
            print("Exception occurred, sleep for 2 secs and retry...")
            self.dom = BeautifulSoup(self.driver.page_source, "html.parser")
            if no_retry:
                print(self.dom)
                raise
            else:
                self.mod(no_retry=True)

    def save(self):
        if self.is_mobile:
            local_filename = "site/m/" + self.filename
        else:
            local_filename = "site/" + self.filename
        md(local_filename)
        with open(local_filename, "w") as f:
            f.write(self.html)

    def gen_html(self):
        s = str(self.dom)
        d_source = pq(self.source)
        print('d_source')
        print(d_source)
        print(len(self.source))
        for div_id in self.code_block:
            print('Processing code block: ', div_id)
            selector = 'div[data-block-id="' + div_id + '"]'
            print(d_source(selector).html())
            # tmp = d_source(selector).outer_html().replace(' data-block-id=', ' id=')
            # s = s.replace('<' + div_id + '>', tmp)
        self.html = s

    def clean(self):
        cursor_div = self.dom.find(class_='notion-cursor-listener')
        if cursor_div:
            css = cursor_div["style"]
            cursor_div["style"] = ";".join([i for i in css.strip().split(";")
                                            if 'cursor' not in i])
        wrapper_div = [i for i in self.dom.find_all("div")
                       if i.has_attr('style') and 'padding-bottom: 30vh;' in i['style']]
        if wrapper_div:
            wrapper_div = wrapper_div[0]
            css = wrapper_div['style']
            wrapper_div['style'] = ";".join([i for i in css.strip().split(";")
                                             if '30vh' not in i])
        intercom_css = self.dom.find('style', id_="intercom-stylesheet")
        if intercom_css:
            intercom_css.decompose()


    def disqus(self):
        for div in self.divs:
            if div.text.strip() == "[comment]":
                div.string = ""
                div["id"] = "disqus_thread"

    def div(self):
        in_comment = False
        in_html = False
        for div in self.divs:
            div["id"] = div["data-block-id"]
            div["class"] = ["content-block"]
            text = div.text.strip()
            # Comments
            if text == '/*':
                in_comment = True
                div.decompose()
                continue
            if text == '*/':
                in_comment = False
                div.decompose()
                continue
            if in_comment:
                div.decompose()
                continue
            # HTML
            if text == '[html]':
                in_html = True
                div.decompose()
                continue
            if text == '[/html]':
                in_html = False
                div.decompose()
                continue
            if in_html:
                inner_html = BeautifulSoup(div.text, "html.parser")
                div.replace_with(inner_html)
                print('Custom HTML inserted: ')
                print('----------------------')
                print(div)
                print('----------------------')
                continue
            if div.find('span', class_='token'):
                self.code_block.append(div["id"])
                div.replace_with('<' + div['id'] + '>')
                continue
            # For lightGallery.js
            img = div.find('img')
            if img and img.has_attr('src') and not div.find('a'):
                img['data-src'] = img['src']
                div['class'].append('lg')

    def iframe(self):
        for iframe in self.dom.find_all('iframe'):
            if iframe.has_attr('style'):
                css = iframe['style'].split(';')
                new_css = [i for i in css if 'pointer' not in i]
                iframe['style'] = ';'.join(new_css)

    def parse_links(self):
        for a in self.dom.find_all("a"):
            href = a['href']
            if href.startswith('/'):
                if href == '/login':
                    a.decompose()
                    continue
                elif href[1:] == self.options["index"].split("/")[-1]:
                    a['href'] = '/'
                else:
                    self.links.add(href)
                    href_list = href.split("/")[-1].split('-')
                    if len(href_list) > 1:
                        a['href'] = "/" + '-'.join(href_list[:-1])
                    else:
                        a['href'] = "/" + href_list[0]
            if 'anchor' in self.options and href.startswith("https://www.notion.so/") and "#" in href:
                url_ = href.split('/')[-1].split("#")
                page_url = "/" + url_[0]
                anchor = url_[1]
                if self.url == page_url:
                    a["target"] = ""
                    a["href"] = '#' + anchor
                else:
                    a["href"] = '/' + '-'.join(url_[0].split('-')[:-1]) + '#' + anchor
                print("Internal link with anchor detected: " + a['href'])

    def meta(self):
        if self.dom.find('html').has_attr("manifest"):
            self.dom.find('html')["manifest"] = ''
        titles = [i for i in self.dom.find_all(
            "div") if (i.has_attr("style") and "2.25em" in i["style"])]
        title = titles[0].text.strip()
        titles[0]["id"] = 'title'
        if self.is_index:
            self.title = title
            self.options["site_title"] = title
        else:
            self.title = title + ' ' + \
                self.options["title_sep"] + ' ' + self.options["site_title"]
        self.dom.find("title").string = self.title
        self.dom.find("meta", attrs={"name": "twitter:site"})[
            "content"] = self.options["twitter"]
        page_path = '-'.join(self.url.split('/')[-1].split('-')[:-1])
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
        # Add Canonical URL for SEO
        if self.is_mobile:
            new_tag = self.dom.new_tag("link", rel='canonical',
                                       href=self.options["base_url"] + page_path)
        else:
            new_tag = self.dom.new_tag("link", rel='alternate', media='only screen and (max-width: 768px)',
                           href=self.options["base_url"] + 'm/' + page_path)
        self.dom.find('head').append(new_tag)
        if 'atom' in self.options:
            atom = self.dom.new_tag('link', rel='feed', type="application/atom+xml", href="/feed")
        self.dom.find('head').append(atom)
        print("Title: " + self.dom.find("title").string)
        imgs = [i for i in self.dom.find_all('img') if i.has_attr(
            "style") and "30vh" in i["style"]]
        if imgs:
            img_src = imgs[0]["src"]
            if img_src.startswith('/'):
                img_url = self.options["base_url"] + img_src[1:]
            else:
                img_url = img_src
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
        global visited, notions
        for link in self.links:
            if link not in visited:
                page = Notion(link, self.driver, options=options, is_mobile=self.is_mobile)
                notions[link] = page
                page.mod()
                visited.add(link)
                page.walk()



if __name__ == "__main__":
    motion()
    if "build_mobile" in options:
        motion(is_mobile=True)
