import datetime
import os
import time
from pathlib import Path

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from win10toast import ToastNotifier

import config
from tools import convert_date, trim_date, total_minutes, tsc_coords


class Program:
    hsc_url = 'https://eq.hsc.gov.ua/'
    dates = [convert_date(date) for date in config.DATES]
    coords = tsc_coords(config.TSC)

    def __init__(self):
        useragent = UserAgent()
        options = webdriver.ChromeOptions()
        options.add_argument(f'user-agent={useragent["google chrome"]}')
        # options.add_argument('--headless')
        options.add_argument('window-size=1920x935')
        self.driver = webdriver.Chrome(options=options)

    def step1(self):
        self.driver.get(self.hsc_url)

        checkbox = self.driver.find_element(By.TAG_NAME, 'input')
        checkbox.click()

        confirm = self.driver.find_element(By.XPATH, '/html/body/main/div/div/div/div/div/div/div[2]/div[2]/a')
        confirm.click()
        time.sleep(4)

    def step2(self):
        file_carrier = self.driver.find_element(By.XPATH, '//a[@href="/euid-auth-js"]')
        file_carrier.click()
        time.sleep(7)

        upload = self.driver.find_element(By.ID, 'PKeyFileInput')
        path = Path(os.getcwd()) / config.ES
        upload.send_keys(str(path))

        password = self.driver.find_element(By.ID, 'PKeyPassword')
        password.send_keys(config.PASSWORD)

        confirm = self.driver.find_element(By.ID, 'id-app-login-sign-form-file-key-sign-button')
        confirm.click()
        time.sleep(7)

    def step3(self):
        confirm = self.driver.find_element(By.ID, 'btnAcceptUserDataAgreement')
        confirm.click()
        time.sleep(4)

    def step4(self):
        sign_up = self.driver.find_element(By.XPATH, '/html/body/main/div/div/div[1]/div[2]/div/button[1]')
        sign_up.click()
        time.sleep(4)

    def step5(self):
        practice = self.driver.find_element(By.XPATH, '/html/body/main/div/div/div[2]/div/div/div/div/a[5]')
        practice.click()
        time.sleep(4)

    def step6(self):
        if config.VEHICLE == 'tsc':
            vehicle = self.driver.find_elements(By.CSS_SELECTOR, "div.buttongroup > button")[0]
        elif config.VEHICLE == 'school':
            vehicle = self.driver.find_elements(By.CSS_SELECTOR, "div.buttongroup > button")[1]
        else:
            raise ValueError(f'Invalid vehicle: {config.VEHICLE}')
        vehicle.click()
        time.sleep(2)

        if config.VEHICLE == 'tsc':
            css_selector = '#ModalCenterServiceCenter > div > div > div.modal-footer > button:nth-child(2)'
        elif config.VEHICLE == 'school':
            css_selector = '#ModalCenter2 > div > div > div.modal-footer > button:nth-child(2)'
        confirm1 = self.driver.find_element(By.CSS_SELECTOR, css_selector)
        confirm1.click()
        time.sleep(2)

        if config.VEHICLE == 'tsc':
            css_selector = '#ModalCenterServiceCenter1 > div > div > div.modal-footer > a:nth-child(2)'
        elif config.VEHICLE == 'school':
            css_selector = '#ModalCenter4 > div > div > div.modal-footer > button'
        confirm2 = self.driver.find_element(By.CSS_SELECTOR, css_selector)
        confirm2.click()
        time.sleep(2)

        if config.VEHICLE == 'school':
            css_selector = '#ModalCenter5 > div > div > div.modal-footer > a:nth-child(2)'
        elif (config.VEHICLE == 'tsc') and (config.TRANSMISSION == 'manual'):
            css_selector = 'body > main > div > div > div:nth-child(2) > div > div > div > div > a:nth-child(7)'
        elif (config.VEHICLE == 'tsc') and (config.TRANSMISSION == 'automatic'):
            css_selector = 'div.buttongroup > a:nth-child(9)'
        b_category = self.driver.find_element(By.CSS_SELECTOR, css_selector)
        b_category.click()
        time.sleep(4)

    def step7(self):
        elem = self.driver.find_element(By.CSS_SELECTOR, 'div.buttongroup > div > div:nth-child(1) > a')
        elem.click()
        time.sleep(5)

    def launch(self):
        self.step1()
        self.step2()
        self.step3()
        self.step4()
        self.step5()
        self.step6()
        self.step7()

    def find_tsc(self):
        elems = self.driver.find_elements(By.TAG_NAME, 'img')
        for elem in elems:
            style = elem.get_attribute('style')
            if self.coords in style:
                return elem

    def check_tsc(self, tsc) -> bool:
        src = tsc.get_attribute('src')
        return src in ('https://eq.hsc.gov.ua/images/hsc_i.png', 'https://eq.hsc.gov.ua/images/hsc_.png')

    def check_tickets(self):
        next_day = self.driver.find_element(By.XPATH, '//div[@onclick="next()"]')
        previous_date = ''
        for _ in range(60):
            date = trim_date(self.driver.find_element(By.ID, 'slider').text)

            if date == previous_date:
                break

            if date in self.dates:
                tsc = self.find_tsc()
                if self.check_tsc(tsc):
                    self.take_ticket(tsc)
                    self.notify(date)
                    break

            next_day.click()
            previous_date = date
            time.sleep(2)

    def take_ticket(self, tsc):
        tsc.click()
        time.sleep(2)

        time_select = Select(self.driver.find_element(By.CSS_SELECTOR, '#id_chtime'))
        deltas = [abs(total_minutes(config.TIME) - total_minutes(option.text)) for option in time_select.options]
        idx = deltas.index(min(deltas))
        time_select.select_by_index(idx)

        email = self.driver.find_element(By.CSS_SELECTOR, '#email')
        email.send_keys(config.EMAIL)

        submit = self.driver.find_element(By.CSS_SELECTOR, '#submit')
        submit.click()
        time.sleep(5)

        confirm = self.driver.find_element(By.CSS_SELECTOR, 'body > main > div > div > div:nth-child(2) > div > div > div > div.footer > a')
        confirm.click()

    def notify(self, date):
        print(f"ВІЛЬНИЙ ТАЛОН {date}")

        toast = ToastNotifier()
        toast.show_toast(
            "ВІЛЬНИЙ ТАЛОН",
            f"ВІЛЬНИЙ ТАЛОН {date}",
            duration=10,
            threaded=True,
        )

        time.sleep(120)
        os.system('pause')

    def refresh(self):
        self.driver.refresh()
        time.sleep(3)

    def quit(self):
        self.driver.close()
        time.sleep(10)


def main(program):
    print(f'\n\nCURRENT TIME: {datetime.datetime.now()}\n\n')
    try:
        program.launch()
        i = 0
        while True:
            print(f'REFRESH #{i}')
            # time.sleep(10000)
            program.refresh()
            program.check_tickets()
            time.sleep(30)
            i += 1
    except KeyboardInterrupt:
        exit(0)
    except Exception as e:
        print('\n' + str(e))
        print('\n\nEMERGENCY RESTART\n\n')
        program.quit()
        time.sleep(120)
        main(program)


if __name__ == '__main__':
    program = Program()
    main(program)
