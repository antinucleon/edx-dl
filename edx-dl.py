#!/usr/bin/python3

import time
from collections import OrderedDict
import os
import json
import click
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located

class EdxCourse(object):
    def __init__(self,
                 username,
                 pwd,
                 course_url,
                 driver="./bin/chromedriver",
                 workingdir=""):
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        options.add_argument('--start-maximized')
        prefs = {"download.default_directory": workingdir,
                 "directory_upgrade": True}
        options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(
            executable_path=driver, chrome_options=options)
        self.wait = WebDriverWait(self.driver, 20)
        self._login(username, pwd)
        self._goto(course_url)
        self.wait.until(presence_of_element_located(
            (By.CLASS_NAME, "course-title-lockup")))
        title = self.driver.find_element_by_class_name("course-title-lockup")
        root_dir = self.format_title(title.text)
        self.mkdir(root_dir)
        os.chdir(root_dir)

    def __call__(self):
        units = self._parse_course()
        for unit_title, sub_units in units.items():
            unit_title = self.format_title(unit_title)
            self.mkdir(unit_title)
            os.chdir(unit_title)
            for i, (sub_title, url) in enumerate(sub_units):
                sub_title = self.format_title(sub_title)
                sub_title = "%d_%s" % (i, sub_title)
                self.mkdir(sub_title)
                os.chdir(sub_title)
                assets = self._parse_unit(sub_title, url)
                if assets is None:
                    assets = []
                base_path = ""
                for j, item in enumerate(assets):
                    self.mkdir(str(j))
                    os.chdir(str(j))
                    if item[0] == "pdf":
                        output_path = os.path.join(base_path, "slides.pdf")
                        self._download_cmd(item[1], str(output_path))
                    elif item[0] == "video":
                        output_path = os.path.join(base_path, item[2] + ".mp4")
                        self._download_cmd(item[1], str(output_path))
                    elif item[0] == "youtube":
                        self._download_youtube(item[1])
                    elif item[0] == "png":
                        with open(item[2] + ".png", "wb") as fo:
                            fo.write(item[1])
                    os.chdir("..")
                os.chdir("..")
            os.chdir("..")

    def _download_cmd(self, url, output=None):
        cmd = 'aria2c --user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15" '
        if output is not None:
            cmd += ' --out="{output}" '.format(output=output)
        cmd += " " + url
        print(cmd)
        os.system(cmd)
        time.sleep(2)

    def _download_youtube(self, url):
        cmd = "youtube-dl {url}".format(url=url)
        os.system(cmd)
        time.sleep(16)

    def format_title(self, title):
        return title.replace("\n", "_").replace(" ", "_").replace("/", "|")

    def mkdir(self, path):
        if not os.path.exists(path):
            os.mkdir(path)

    def _goto(self, url):
        time.sleep(1)
        self.driver.get(url)
        time.sleep(5)

    def _login(self, username, pwd):
        self._goto("https://edx.org")
        self._goto("https://courses.edx.org/login")
        self.wait.until(presence_of_element_located(
            (By.NAME, "emailOrUsername")))
        uname_input = self.driver.find_element_by_name("emailOrUsername")
        uname_input.send_keys(username)
        time.sleep(2)
        pwd_input = self.driver.find_element_by_name("password")
        pwd_input.send_keys(pwd + Keys.RETURN)
        self.wait.until(presence_of_element_located(
            (By.CLASS_NAME, "view-dashboard")))
        time.sleep(2)

    def _parse_course(self):
        module_list = self.wait.until(
            presence_of_element_located((By.CLASS_NAME, "list-unstyled")))
        module_titles = module_list.find_elements_by_class_name(
            "collapsible-trigger")
        for title in module_titles:
            if title.get_attribute("aria-expanded") == "false":
                title.click()
        module_bodies = module_list.find_elements_by_class_name(
            "collapsible-card-lg")
        units = OrderedDict()
        for module in module_bodies:
            tmp = module.find_elements_by_class_name("align-middle")
            key = ""
            for item in tmp:
                title = item.text
                try:
                    url = item.find_element_by_tag_name(
                        "a").get_attribute("href")
                    units[key].append((title, url))
                except Exception as e:
                    key = title
                    units[key] = []
        return units

    def _parse_unit(self, title, url):
        assets = []
        if "discussion" in title:
            return assets
        self._goto(url)
        _ = self.wait.until(
            presence_of_element_located((By.ID, "unit-iframe")))

        # parse each tab
        tabs = self.driver.find_element_by_class_name(
            "sequence-navigation-tabs")
        buttons = tabs.find_elements_by_tag_name("button")
        for button in buttons:
            button.click()
            _ = self.wait.until(presence_of_element_located(
                (By.CLASS_NAME, "unit-container")))
            time.sleep(5)
            tab_type = button.find_element_by_tag_name(
                "svg").get_attribute("data-icon")
            if tab_type == "video":
                # videos
                _ = self.wait.until(
                    presence_of_element_located((By.ID, "unit-iframe")))
                self.driver.switch_to.frame("unit-iframe")
                try:
                    video = self.driver.find_element_by_class_name(
                        "video-download-button")
                    url = video.get_attribute("href")
                    note = self.driver.find_element_by_tag_name("h3").text
                    assets.append(("video", url, note))
                except:
                    video = self.driver.find_element_by_class_name("video")
                    meta = json.loads(video.get_attribute("data-metadata"))
                    url = meta["streams"].split(":")[-1]
                    note = self.driver.find_element_by_tag_name("h3").text
                    assets.append(("youtube", url, note))

                self.driver.switch_to.parent_frame()
            else:
                # text
                _ = self.wait.until(
                    presence_of_element_located((By.ID, "unit-iframe")))
                unit = self.driver.find_element_by_class_name("unit-container")
                png = unit.screenshot_as_png
                note = self.driver.find_element_by_tag_name("h1").text
                note = self.format_title(note)
                if "Slides for" in note:
                    self.driver.switch_to.frame("unit-iframe")
                    url = self.driver.find_element_by_partial_link_text(
                        "Slides for").get_attribute("href")
                    assets.append(("pdf", url))
                else:
                    assets.append(("png", png, note))
        return assets


@click.command()
@click.option("--user", prompt="Edx Username or email address", required=True)
@click.password_option("--pwd", prompt="Edx Password", required=True, confirmation_prompt=False)
@click.option("--url", prompt="Course home URL", required=True)
def run(user, pwd, url):
  course = EdxCourse(user, pwd, url)
  course()

if __name__ == "__main__":
    run()
