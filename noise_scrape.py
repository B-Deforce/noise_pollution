from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
from bs4 import BeautifulSoup
import pandas as pd
from datetime import timedelta
import os
import numpy as np

# read trigger scenario-file
data_PATH = "C:/Users/u0143591/OneDrive - KU Leuven/PhD/side_projects/noise_pol_leuven"
nudge_df = pd.read_excel(data_PATH + "/trigger_scenario_activities_2022_12_01.xlsx",
                         sheet_name="run",
                         parse_dates=[['EventDate', 'EventTime']])

nudge_df.drop(columns="Unnamed: 0", inplace=True)
nudge_df["EventDate_EventTime"].replace({"nan nan": np.nan}, inplace=True)
nudge_df.dropna(subset=["EventDate_EventTime"], inplace=True)
nudge_df["EventDate_EventTime"] = pd.to_datetime(nudge_df["EventDate_EventTime"].str.split("00:00:00").apply(lambda x: ''.join(x)))
nudge_df = nudge_df.set_index("EventDate_EventTime")

PATH = "../web_scraping/chromedriver.exe"
service = Service(PATH)
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://leuven-geluid.munisense.net/web/v5/nl/general/graph")

WebDriverWait(driver, timeout=5).until(lambda d: d.find_element(By.ID, "username_field"))
search1 = driver.find_element(By.ID, "username_field")
search2 = driver.find_element(By.ID, "password_field")

search1.send_keys("")
search2.send_keys("")
search2.send_keys(Keys.RETURN)

WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.CLASS_NAME, "ssts_starttime"))

# the advanced settings need to be set only once, so we exclude it from the loop
# advncd buttons
advncd_btn_xpath = "//div[@class='sub-header']"
search_btn = driver.find_element(By.XPATH, advncd_btn_xpath)
search_btn.click()

output_type = driver.find_element(By.ID, "output_type")
Select(output_type).select_by_visible_text("Csv")

sample_xpath = "//*[@id='override_samplerate']"
sample_btn = driver.find_element(By.XPATH, sample_xpath)
# scroll
time.sleep(1)
driver.execute_script("window.scrollTo(0, 300)") 
time.sleep(1)

# manual click due to issues with sample_btn being "not clickable"
action = ActionChains(driver)
action.move_to_element(sample_btn)
action.click()
action.perform()

# set sampling rate
sample_rate_xpath = "/html/body/app-root/app-layout/div/div[2]/div[3]/div/ng-component/div/div[2]/div[2]/div[2]/div[5]/div/input"
sample_rate = driver.find_element(By.XPATH, sample_rate_xpath)
sample_rate.send_keys("1")

# select sensor
sensor_xpath = "//table[@class='datatable query']//tr[@class='sensor-row']//input[@type='checkbox']"
sensor_check = driver.find_elements(By.XPATH, sensor_xpath)
# scroll
time.sleep(1)
driver.execute_script("window.scrollTo(0, 50)") 
time.sleep(1)
for i in range(8):
    sensor_check[i*4].click() # we multiply by 4 to jump 4 checkboxes ahead since we only care about first column

# start date & time
# we only take 30min before and after a nudging event as other measurements (e.g. during daytime) are not of interest here
for i in nudge_df.index:
    if any(str(i.date()) in x for x in os.listdir(data_PATH + "/noise_scrapes")):
        continue
    else:
        start = i - timedelta(minutes=30)
        end = i + timedelta(minutes=30)

        sdate = str(start.date().strftime("%d%m%Y"))
        stime = str(start.time().strftime("%I%M%S%p"))
        startdate_xpath = "//div[@class='ssts_starttime']/input[@type='text']"
        search_startdate = driver.find_element(By.XPATH, startdate_xpath)
        search_startdate.send_keys(Keys.CONTROL, 'a')
        search_startdate.send_keys(sdate)

        starttime_xpath = "//div[@class='ssts_starttime']/input[@type='time']"
        search_starttime = driver.find_element(By.XPATH, starttime_xpath)
        search_starttime.send_keys(stime)

        # end date & time
        edate = str(end.date().strftime("%d%m%Y"))
        etime = str(end.time().strftime("%I%M%S%p"))
        enddate_xpath = "//div[@class='ssts_endtime']/input[@type='text']"
        search_enddate = driver.find_element(By.XPATH, enddate_xpath)
        search_enddate.send_keys(Keys.CONTROL, 'a')
        search_enddate.send_keys(edate)

        endtime_xpath = "//div[@class='ssts_endtime']/input[@type='time']"
        search_endtime = driver.find_element(By.XPATH, endtime_xpath)
        search_endtime.send_keys(etime)

        # execute
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 500)")
        time.sleep(1)
        exec_btn_xpath = "/html/body/app-root/app-layout/div/div[2]/div[3]/div/ng-component/div/div[2]/div[3]/div"
        exec_btn = driver.find_element(By.XPATH, exec_btn_xpath)
        exec_btn.click()

        time.sleep(7)
driver.quit()
