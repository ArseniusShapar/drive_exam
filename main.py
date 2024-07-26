import os
import time
from datetime import datetime
from pathlib import Path

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium_recaptcha_solver import RecaptchaSolver
from win10toast import ToastNotifier

import config
from tools import convert_date, trim_date, total_minutes, tsc_coords

ID = By.ID
XPATH = By.XPATH
CSS = By.CSS_SELECTOR
TAG = By.TAG_NAME


class Program:
    hsc_url = 'https://eq.hsc.gov.ua/'
    dates = [convert_date(date) for date in config.DATES]
    coords = tsc_coords(config.TSC)
    ES_path = str(Path(os.getcwd()) / config.ES)

    def __init__(self):
        useragent = UserAgent(os='windows')

        options = webdriver.ChromeOptions()
        options.add_argument(f'user-agent={useragent.firefox}')
        options.add_argument('window-size=1920x935')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('log-level=3')

        service = Service('./chromedriver.exe')

        self.driver = webdriver.Chrome(service=service, options=options)
        # self.driver.set_window_position(-10000, 0)

    def _click(self, elem: tuple[str, str] | WebElement) -> None:
        element = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(elem)
        )
        element.click()

    def _send_keys(self, elem: tuple[str, str] | WebElement, keys: str = '') -> None:
        element = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(elem)
        )
        element.send_keys(keys)

    def _wait_ready_page(self):
        WebDriverWait(self.driver, 10).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(2)

    def step1(self):
        self.driver.get(self.hsc_url)

        checkbox = (TAG, 'input')
        self._click(checkbox)

        confirm = (CSS, '.btn-hsc-green_s')
        self._click(confirm)

    def step2(self):
        file_carrier = (XPATH, '//a[@href="/euid-auth-js"]')
        self._click(file_carrier)

        WebDriverWait(self.driver, 10).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(1)
        upload = self.driver.find_element(ID, 'PKeyFileInput')
        upload.send_keys(self.ES_path)

        password = (ID, 'PKeyPassword')
        self._send_keys(password, config.PASSWORD)

        confirm = (ID, 'id-app-login-sign-form-file-key-sign-button')
        self._click(confirm)

    def step3(self):
        confirm = (ID, 'btnAcceptUserDataAgreement')
        self._click(confirm)

    def step4(self):
        sign_up = (CSS, 'br + button')
        self._click(sign_up)

    def step5(self):
        practice = (CSS, '.buttongroup > a:last-of-type')
        self._click(practice)

    def step6(self):
        idx = 1 if config.VEHICLE == 'tsc' else 3
        vehicle = (CSS, f'.buttongroup > :nth-child({idx})')
        self._click(vehicle)

        css_selector = '.modal-footer > button' if config.VEHICLE == 'tsc' else '#ModalCenter2 .modal-footer > button'
        confirm1 = (CSS, css_selector)
        self._click(confirm1)

        css_selector = '.modal-footer > a' if config.VEHICLE == 'tsc' else '#ModalCenter4 .modal-footer > button'
        confirm2 = (CSS, css_selector)
        self._click(confirm2)

        if config.VEHICLE == 'school':
            css_selector = '#ModalCenter5 .modal-footer > :nth-child(2)'
        elif config.VEHICLE == 'tsc' and config.TRANSMISSION == 'manual':
            css_selector = '.buttongroup > :nth-child(7)'
        elif config.VEHICLE == 'tsc' and config.TRANSMISSION == 'automatic':
            css_selector = '.buttongroup > :nth-child(9)'
        b_category = (CSS, css_selector)
        self._click(b_category)

    def step7(self):
        first_day = (CSS, '.buttongroup a')
        self._click(first_day)

    def launch(self):
        self.step1()
        self.step2()
        self.step3()
        self._wait_ready_page()

        self.check_and_pass_captcha()

        self.launch_after_captcha()

    def launch_after_captcha(self):
        self.step4()
        self.step5()
        self.step6()
        self.step7()

    def check_captcha(self):
        elems = self.driver.find_elements(ID, 'captchaform')
        return len(elems) > 0

    def pass_captcha(self):
        solver = RecaptchaSolver(driver=self.driver)
        recaptcha_iframe = self.driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')
        solver.click_recaptcha_v2(iframe=recaptcha_iframe)
        time.sleep(5)

        confirm = self.driver.find_element(CSS, '.btn-warning')
        confirm.click()

    def check_and_pass_captcha(self):
        if self.check_captcha():
            self.pass_captcha()

    def find_tsc(self):
        elems = self.driver.find_elements(TAG, 'img')
        for elem in elems:
            style = elem.get_attribute('style')
            if self.coords in style:
                return elem

    def check_tsc(self, tsc) -> bool:
        src = tsc.get_attribute('src')
        return src in ('https://eq.hsc.gov.ua/images/hsc_i.png', 'https://eq.hsc.gov.ua/images/hsc_.png')

    def check_tickets(self):
        next_day = self.driver.find_element(XPATH, '//div[@onclick="next()"]')
        previous_date = ''
        for _ in range(60):
            if self.check_captcha():
                self.pass_captcha()
                self.launch_after_captcha()

            date = trim_date(self.driver.find_element(ID, 'slider').text)

            if date == previous_date:
                break

            if (date in self.dates) or (not self.dates):
                tsc = self.find_tsc()
                if self.check_tsc(tsc):
                    self.take_ticket(tsc)
                    self.notify(date)
                    break

            next_day.click()
            previous_date = date
            time.sleep(1)

    def take_ticket(self, tsc):
        tsc.click()
        time.sleep(2)

        time_select = Select(self.driver.find_element(ID, 'id_chtime'))
        deltas = [abs(total_minutes(config.TIME) - total_minutes(option.text)) for option in time_select.options]
        idx = deltas.index(min(deltas))
        time_select.select_by_index(idx)

        email = self.driver.find_element(ID, 'email')
        email.send_keys(config.EMAIL)

        submit = self.driver.find_element(ID, 'submit')
        submit.click()
        self._wait_ready_page()

        confirm = self.driver.find_element(CSS, '.btn-hsc-green')
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
        self._wait_ready_page()

    def __del__(self):
        self.driver.quit()


def launch_listener(program: Program) -> None:
    print(f'\nCURRENT TIME: {datetime.now()}\n')
    program.launch()
    for i in range(10_000):
        print(f'REFRESH #{i}')
        program.check_tickets()
        time.sleep(1)
        program.refresh()
        if program.check_captcha():
            program.pass_captcha()
            program.launch_after_captcha()


def main():
    while True:
        try:
            program = Program()
            launch_listener(program)
        except KeyboardInterrupt:
            exit(0)
        except Exception as e:
            print(e)
            print('\nEMERGENCY RESTART\n')
        finally:
            del program


if __name__ == '__main__':
    main()
