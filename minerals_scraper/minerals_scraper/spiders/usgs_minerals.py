import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import wget
import re
from pathlib import Path
import time

class USGSMineralsRegionSpider(scrapy.Spider):
    name = 'usgs_minerals_region'
    allowed_domains = ['www.usgs.gov', 'd9-wret.s3.us-west-2.amazonaws.com', 
                      'd9-wret.s3-us-west-2.amazonaws.com', 'pubs.usgs.gov']
    
    start_urls = [
        'https://www.usgs.gov/centers/national-minerals-information-center/africa-and-middle-east',
    ]

    def __init__(self):
        super(USGSMineralsRegionSpider, self).__init__()
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=chrome_options)
        
        self.base_dir = 'mineral_data'
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def parse(self, response):
        return self.parse_region(response)

    def handle_popup(self):
        try:
            popup_close = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "fba-modal-close"))
            )
            popup_close.click()
            time.sleep(1)
        except:
            pass

    def process_xls_section(self, section, parent_dir, section_name):
        """Process XLS links from a section"""
        try:
            xls_format = section.find_element(By.XPATH, ".//li[contains(text(), 'XLS Format:')]")
            if xls_format:
                xls_links = section.find_elements(By.XPATH, 
                    ".//a[contains(@href, '.xls') or contains(@href, '.xlsx')]")
                
                for link in xls_links:
                    try:
                        file_url = link.get_attribute('href')
                        if not file_url:
                            continue

                        year_text = link.text.strip()
                        year_match = re.search(r'(19|20)\d{2}(?:-\d{2})?', year_text)
                        if not year_match:
                            year_match = re.search(r'(19|20)\d{2}(?:-\d{2})?', file_url)
                        
                        if year_match and file_url:
                            year = year_match.group(0)
                            file_ext = '.xlsx' if file_url.endswith('.xlsx') else '.xls'
                            filename = f"{section_name.lower().replace(' ', '_')}_{year}{file_ext}"
                            filepath = os.path.join(parent_dir, filename)
                            
                            if not os.path.exists(filepath):
                                self.logger.info(f"Downloading {filename} to {filepath}")
                                wget.download(file_url, filepath)
                                time.sleep(0.5)
                            
                            yield {
                                'section': section_name,
                                'year': year,
                                'url': file_url,
                                'file_path': filepath
                            }

                    except Exception as e:
                        self.logger.error(f"Error processing XLS link: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error finding XLS section: {str(e)}")

    def parse_region(self, response):
        region_name = response.url.split('/')[-1].replace('-', '_')
        region_dir = os.path.join(self.base_dir, region_name)
        if not os.path.exists(region_dir):
            os.makedirs(region_dir)

        self.driver.get(response.url)
        time.sleep(2)
        self.handle_popup()

        try:
            content_area = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "field-text-with-media"))
            )

            # First process regional summaries
            regional_sections = content_area.find_elements(By.XPATH, 
                "//ul/li[contains(., 'XLS Format:') and ./ancestor::li[contains(., 'Regional Summaries')]]")
            
            for section in regional_sections:
                section_name = section.find_element(By.XPATH, "./ancestor::li[1]/text()[1]").text.strip()
                if section_name:
                    section_dir = os.path.join(region_dir, section_name.lower().replace(' ', '_'))
                    if not os.path.exists(section_dir):
                        os.makedirs(section_dir)
                    
                    yield from self.process_xls_section(section, section_dir, section_name)

            # Then process country sections
            country_sections = content_area.find_elements(By.XPATH, 
                "//p[strong[not(contains(., 'Regional'))]]")
            
            for section in country_sections:
                try:
                    country_name = section.find_element(By.TAG_NAME, "strong").text.strip()
                    if country_name and not any(x in country_name.lower() for x in ['index', 'summaries', 'map']):
                        country_dir = os.path.join(region_dir, country_name.lower().replace(' ', '_'))
                        if not os.path.exists(country_dir):
                            os.makedirs(country_dir)

                        # Find the associated XLS section
                        next_ul = section.find_element(By.XPATH, "following-sibling::ul[1]")
                        if next_ul:
                            yield from self.process_xls_section(next_ul, country_dir, country_name)

                except Exception as e:
                    self.logger.error(f"Error processing country section: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error processing page {response.url}: {str(e)}")

    def closed(self, reason):
        if hasattr(self, 'driver'):
            self.driver.quit()