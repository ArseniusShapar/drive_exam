import os
import time
from datetime import datetime
from pathlib import Path

import chromedriver_autoinstaller
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium_recaptcha_solver import RecaptchaSolver
from win10toast import ToastNotifier

import config
from tools import convert_date, total_minutes, type_like_human, random_sleep

ID = By.ID
XPATH = By.XPATH
CSS = By.CSS_SELECTOR
TAG = By.TAG_NAME


class Program:
    hsc_url: str = 'https://eq.hsc.gov.ua/'
    ES_path = str(Path(os.getcwd()) / config.ES)

    def __init__(self):
        chromedriver_autoinstaller.install()

        useragent = UserAgent(os='windows')

        options = webdriver.ChromeOptions()
        options.add_argument(f'user-agent={useragent.chrome}')
        options.add_argument('window-size=1920x935')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('log-level=3')
        options.add_argument('start-maximized')

        service = Service()

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_window_position(-2000, 0)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        '''
        })

    def __del__(self):
        self.driver.quit()

    def _click(self, elem: tuple[str, str] | WebElement) -> None:
        if isinstance(elem, tuple):
            element = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(elem)
            )
        else:
            element = elem
        element.click()
        random_sleep()

    def _send_keys(self, elem: tuple[str, str] | WebElement, keys: str = '') -> None:
        if isinstance(elem, tuple):
            element = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(elem)
            )
        else:
            element = elem
        type_like_human(element, keys)
        random_sleep()

    def _wait_ready_page(self) -> None:
        WebDriverWait(self.driver, 10).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete'
        )
        random_sleep(1.5, 2.5)

    def step1(self) -> None:
        self.driver.get(self.hsc_url)
        self.driver.execute_script("window.scrollBy(0, 500);")
        random_sleep()

        checkbox = (TAG, 'input')
        self._click(checkbox)

        confirm = (TAG, 'button')
        self._click(confirm)

    def step2(self) -> None:
        accept_cookie = (ID, 'CybotCookiebotDialogBodyButtonAccept')
        self._click(accept_cookie)

        file_carrier = (XPATH, '//a[@href="/euid-auth-js"]')
        self._click(file_carrier)

        self._wait_ready_page()

        upload = self.driver.find_element(ID, 'PKeyFileInput')
        upload.send_keys(self.ES_path)
        random_sleep()

        password = (ID, 'PKeyPassword')
        self._send_keys(password, config.PASSWORD)

        confirm = (ID, 'id-app-login-sign-form-file-key-sign-button')
        self._click(confirm)

    def step3(self) -> None:
        confirm = (ID, 'btnAcceptUserDataAgreement')
        self._click(confirm)

    def step4(self) -> None:
        sign_up = (CSS, 'div.MuiGrid-root > a.MuiButtonBase-root')
        self._click(sign_up)

    def step5(self) -> None:
        practice = (CSS, 'div.MuiGrid-root:nth-child(2) > button.MuiButtonBase-root')
        self._click(practice)

    def step6(self) -> None:
        idx = 1 if config.VEHICLE == 'tsc' else 2
        vehicle = (CSS, f'div.MuiGrid-root:nth-child({idx}) > button')
        self._click(vehicle)

        css_selector = 'p + button'
        confirm1 = (CSS, css_selector)
        self._click(confirm1)

        b_category = (CSS, 'div.MuiGrid-root:nth-child(2) > button')
        self._click(b_category)

    def step7(self) -> None:
        search_field = (ID, '«ri»')
        self._send_keys(search_field, config.TSC)

        tsc = self.driver.find_element(CSS, 'div.MuiStack-root:nth-child(2) > button.MuiButtonBase-root')
        if tsc.is_enabled():
            self._click(tsc)
        else:
            print('NO TALONS')
            return

        accessible_days = self.driver.find_elements(CSS, 'button.react-calendar__tile:not([disabled])')
        dates = self._get_dates(accessible_days)

        for elem, date in zip(accessible_days, dates):
            if date in config.DATES or not config.DATES:
                self._click(elem)
                self.take_ticket(date)
                return

        print('NO TALONS ON DESIRED DATES')

    def _get_dates(self, accessible_days: list[WebElement]) -> list[str]:
        dates = []
        for elem in accessible_days:
            raw_date = elem.find_element(CSS, 'abbr').get_attribute('aria-label')
            date = convert_date(raw_date.lower())
            dates.append(date)
        return dates

    def launch(self) -> None:
        self.step1()
        self._wait_ready_page()
        self.step2()
        self._wait_ready_page()
        self.step3()
        self._wait_ready_page()
        self.step4()
        self._wait_ready_page()

    def take_ticket(self, date: str = ''):
        time_slots = self.driver.find_elements(CSS, 'div.MuiGrid-root > div.MuiGrid-root')
        times = self._get_times(time_slots)
        slot_idx = self._nearest_time(times)
        self._click(time_slots[slot_idx])
        random_sleep(2, 3)

        self.pass_captcha()

        confirm = (CSS, 'div.MuiStack-root div.MuiStack-root:last-child button.MuiButtonBase-root:last-child')
        self._click(confirm)

        self._wait_ready_page()
        _, phone, email = self.driver.find_elements(CSS, 'input.MuiInputBase-input')
        self._send_keys(phone, config.PHONE.lstrip('+380'))
        self._send_keys(email, config.EMAIL)

        confirm = (CSS, 'div.MuiStack-root button.MuiButtonBase-root:last-child')
        self._click(confirm)
        self.notify(date)

    def _get_times(self, time_slots: list[WebElement]) -> list[str]:
        times = []
        for elem in time_slots:
            times.append(elem.find_element(CSS, 'p').text)
        return times

    def _nearest_time(self, times: list[str]) -> int:
        deltas = [abs(total_minutes(config.TIME) - total_minutes(t)) for t in times]
        idx = deltas.index(min(deltas))
        return idx

    def pass_captcha(self):
        solver = RecaptchaSolver(driver=self.driver)
        recaptcha_iframe = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((XPATH, '//iframe[@title="reCAPTCHA"]'))
        )
        solver.click_recaptcha_v2(iframe=recaptcha_iframe)
        time.sleep(3)

    def check_tickets(self) -> None:
        self.step5()
        self.step6()
        self._wait_ready_page()
        self.step7()

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


def launch_listener(program: Program) -> None:
    print(f'\nCURRENT TIME: {datetime.now()}\n')
    program.launch()
    for i in range(10_000):
        program.check_tickets()
        print(f'REFRESH #{i}')
        time.sleep(60)
        program.refresh()


def main():
    while True:
        try:
            program = Program()
            launch_listener(program)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(e)
            print('\nEMERGENCY RESTART\n')
        finally:
            del program


if __name__ == '__main__':
    main()
