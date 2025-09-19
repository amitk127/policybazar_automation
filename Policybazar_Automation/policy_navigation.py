import os
import time
import subprocess
import platform
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from insurance_details import InsuranceDetails
from policy_database import PolicyDatabase
from email_sender import EmailSender
import logging
logger = logging.getLogger(__name__)


class PolicyBazaarNavigation:

    mail_sent = set()
    @staticmethod
    def policy_bazaar_initiate(policy_url: str, driver_path: str):
        try:
            if platform.system() == "Windows":
                import getpass
                username = getpass.getuser()
                subprocess.run(f'taskkill /F /IM chrome.exe /FI "USERNAME eq {username}"',
                               shell=True, capture_output=True)
                logger.info("Killed Chrome Processes")
                time.sleep(3)

                logger.info("Clearing DNS Cache...")
                subprocess.run("ipconfig /flushdns", shell=True, capture_output=True)
                time.sleep(3)

                logger.info("Clearing Temp files...")
                temp_path = os.environ.get('TEMP', '')
                if temp_path:
                    subprocess.run(f'del /q/f/s "{temp_path}\\*"', shell=True, capture_output=True)
                subprocess.run('del /q/f/s "C:\\Windows\\Temp\\*"', shell=True, capture_output=True)
                time.sleep(3)

            service = Service(driver_path)
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")

            driver = webdriver.Chrome(service=service, options=options)
            driver.get(policy_url)
            driver.maximize_window()

            return driver

        except Exception as e:
            logger.info(f"Error initializing WebDriver ")

            raise

    @staticmethod
    def navigation(connection, driver, record, policy_url, screenshot_dir,email_config):

        mail_sent=PolicyBazaarNavigation.mail_sent
        wait = WebDriverWait(driver, 120)
        car_number = record.get_registration_number()
        record_id = record.get_id()
        PolicyBazaarNavigation.mail_sent.discard(record_id)

        try:
            time.sleep(2)
            logger.info(f"\nProcessing ID: {record_id} | Car: {car_number}")
            car_number_input = driver.find_element(
                By.XPATH, "//div[contains(@class,'textinput')]//input[contains(@id,'regNoTextBox')]"
            )
            time.sleep(2)
            car_number_input.send_keys(car_number)
            time.sleep(2)

            view_price = driver.find_element(
                By.XPATH, "//button[contains(@id,'btnGetQuotes')]//span[contains(@id,'spanGetQuote')]"
            )
            PolicyBazaarNavigation._safe_click(view_price, "viewPrice", record_id, car_number, driver, screenshot_dir, mail_sent, email_config)
            logger.info("Navigated to vehicle details")
            time.sleep(5)

            try:
                popup_wait = WebDriverWait(driver, 10)
                popup_wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='policyDetailsPopupBox']//div[contains(text(),'Please confirm your ownership status')]"
                                                                )))
                logger.info(f"Ownership status popup detected for record  id: {record_id}, ending case")

                PolicyBazaarNavigation._take_screenshot(driver, "ownership_status_popup_detected", record_id, car_number, screenshot_dir, mail_sent, email_config)
                PolicyDatabase.update_new_ui_popup_remarks(connection, record_id)
                return

            except TimeoutException:
                pass
            time.sleep(5)
            date_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Policy Expiry Date')]/following::input[1]")))
            driver.execute_script("arguments[0].focus();", date_input)

            date_input.send_keys(Keys.CONTROL + "a")
            time.sleep(2)
            future_date = (datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(days=3)).strftime("%d/%m/%Y")

            for char in future_date:
                date_input.send_keys(char)
                time.sleep(0.1)

            date_input.send_keys(Keys.ENTER)
            time.sleep(2)

            try:
                wait.until(EC.presence_of_element_located((By.XPATH,
                                                           "//div[contains(text(),'Previous year NCB')]")))
                ncb_elements = driver.find_elements(By.XPATH,
                                                    "//div[contains(text(),'Previous year NCB')]")
                if len(ncb_elements) == 0:
                    logger.info(f"Previous Year NCB Element not present for record ID: {record_id}")

                    PolicyBazaarNavigation._take_screenshot(driver, "ncb_element_not_present", record_id, car_number, screenshot_dir, mail_sent,email_config)
                    PolicyDatabase.update_ncb_elements_missing_remark(connection, record_id)
                    return
            except Exception as e:
                logger.info(f"Previous Year NCB Element not present for for record ID: {record_id}")
                PolicyBazaarNavigation._take_screenshot(driver, "ncb_element_not_present", record_id, car_number,
                                                        screenshot_dir, mail_sent, email_config)
                PolicyDatabase.update_ncb_elements_missing_remark(connection, record_id)
                return


            ncb_selection_success = PolicyBazaarNavigation._handle_ncb_selection(driver, wait, record, record_id,car_number, screenshot_dir, mail_sent, email_config)

            if not ncb_selection_success:
                logger.info(f"NCB not found in UI for record ID: {record_id}. Updating database and skipping to next record.")


                PolicyDatabase.update_ncb_not_found_remarks(connection, record_id)
                return

            PolicyBazaarNavigation._handle_claim_checkbox(driver, wait, record, record_id, car_number, screenshot_dir, mail_sent, email_config)

            time.sleep(3)
            previous_insurer_success = PolicyBazaarNavigation._select_previous_insurer(driver, wait, record_id, car_number, screenshot_dir, mail_sent, email_config)

            if not previous_insurer_success:

                PolicyDatabase.update_ui_error_remarks(connection, record_id)
                return

            time.sleep(3)
            view_quotes = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//button[contains(@class,'btn forward')]"
            )))
            PolicyBazaarNavigation._safe_click(view_quotes, "view_Quotes", record_id, car_number, driver, screenshot_dir, mail_sent, email_config)
            time.sleep(2)
            logger.info("Click to the View Quotes")

            driver.switch_to.default_content()
            time.sleep(30)

            try:
                wait.until(EC.presence_of_element_located((By.XPATH,
                                                           "//p[normalize-space()='Select IDV']//span[@class='arrowRight whiteArrowDown']")))
                idv_elements = driver.find_elements(By.XPATH,
                                                    "//p[normalize-space()='Select IDV']//span[@class='arrowRight whiteArrowDown']")
                if len(idv_elements) == 0:
                    logger.info(f"Next page failed to load after View Quotes for record ID: {record_id}")

                    PolicyBazaarNavigation._take_screenshot(driver, "view_quotes_page_load_failed", record_id, car_number, screenshot_dir, mail_sent,email_config)

                    PolicyDatabase.update_ui_error_remarks(connection, record_id)
                    return
            except Exception as e:
                logger.info(f"Next page failed to load after View Quotes for record ID: {record_id}")
                PolicyBazaarNavigation._take_screenshot(driver, "view_quotes_page_load_failed", record_id, car_number,
                                                        screenshot_dir, mail_sent, email_config)

                PolicyDatabase.update_ui_error_remarks(connection, record_id)
                return

            PolicyBazaarNavigation._select_idv(driver, wait, record_id, car_number, screenshot_dir, mail_sent, email_config)

            selected_addon_count = PolicyBazaarNavigation._select_add_ons(driver, wait, record.get_add_on(), record_id,
                                                                          car_number, screenshot_dir, mail_sent, email_config)

            record.selected_addon_count = selected_addon_count
            time.sleep(10)
            PolicyBazaarNavigation._scrape_insurance_data(connection, driver, wait, record, screenshot_dir, mail_sent, email_config)

        except Exception as e:
            # navigation_error_end_time = datetime.datetime.now().replace(microsecond=0)
            # navigation_error_duration = navigation_error_end_time - start_time
            # duration_str = str(navigation_error_duration)

            if record_id not in PolicyBazaarNavigation.mail_sent:
                EmailSender.send_error_email(None, "Navigation Error", str(record_id), car_number, email_config)
                PolicyBazaarNavigation.mail_sent.add(record_id)
                logger.info("Navigation Error Email sent.")
            logger.info("Navigation error")

            raise
        finally:
            driver.get(policy_url)
            time.sleep(3)



    @staticmethod
    def _handle_ncb_selection(driver, wait, record, record_id, car_number, screenshot_dir, mail_sent, email_config):
        original_ncb = record.get_ncb()
        if not original_ncb.endswith('%'):
            original_ncb += '%'

        if original_ncb == "0%":
            target_ncb = "0%"
        elif original_ncb == "20%":
            target_ncb = "0%"
        elif original_ncb == "25%":
            target_ncb = "20%"
        elif original_ncb == "35%":
            target_ncb = "25%"
        elif original_ncb == "45%":
            target_ncb = "35%"
        elif original_ncb == "50%":
            target_ncb = "45%"
        elif int(original_ncb.replace('%','')) > 50:
            target_ncb = "50%"
        else:
            logger.info(f"Unsupported NCB: {original_ncb}")
            PolicyBazaarNavigation._take_screenshot(driver, f"unsupported_ncb_{original_ncb}",
                                                    record_id, car_number, screenshot_dir, mail_sent, email_config)
            return False

        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, "//ul/li[@role='button']")))

            ncb_option = wait.until(EC.element_to_be_clickable((
                By.XPATH, f"//ul/li[@role='button' and text()='{target_ncb}']")
            ))
            PolicyBazaarNavigation._safe_click(ncb_option, f"ncbOption_{target_ncb}",
                                               record_id, car_number, driver, screenshot_dir, mail_sent, email_config)
            logger.info(f"Selected NCB: {target_ncb} (Original: {original_ncb})")

            record.selected_ncb = target_ncb
            time.sleep(2)
            return True

        except TimeoutException:
            logger.info(f"NCB {target_ncb} not found in UI")
            PolicyBazaarNavigation._take_screenshot(driver, f"ncb_{target_ncb}_not_found",
                                                    record_id, car_number, screenshot_dir, mail_sent, email_config)
            return False
        except Exception:
            logger.info(f"Error during NCB selection")
            PolicyBazaarNavigation._take_screenshot(driver, "ncb_selection_error",
                                                    record_id, car_number, screenshot_dir, mail_sent, email_config)
            return False

    @staticmethod
    def _handle_claim_checkbox(driver, wait, record, record_id, car_number, screenshot_dir, mail_sent, email_config):
        claim_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                "//label[contains(text(),'Did you make claim')]/following-sibling::div[contains(@class,'toggle-wrapper')]//input[@type='checkbox']")))

        original_ncb = record.get_ncb()
        if not original_ncb.endswith('%'):
            original_ncb += '%'

        if original_ncb == "0%" and not claim_checkbox.is_selected():
            PolicyBazaarNavigation._safe_click(claim_checkbox, "claimCheckbox", record_id, car_number, driver,
                                               screenshot_dir, mail_sent, email_config)
            logger.info("Claim set to YES for NCB 0%")
            time.sleep(2)
        else:
            time.sleep(2)


    #
    # @staticmethod
    # def _handle_ncb_selection(driver, wait, record, record_id, car_number,screenshot_dir, mail_sent, email_config):
    #     previous_year_ncb = record.get_ncb()
    #
    #     if not previous_year_ncb.endswith('%'):
    #         previous_year_ncb += '%'
    #
    #     try:
    #         wait.until(EC.visibility_of_element_located((By.XPATH, "//ul/li[@role='button']")))
    #         ncb_options = driver.find_elements(By.XPATH, "//ul/li[@role='button']")
    #         ncb_found = False
    #         available_ncbs = []
    #
    #         for option in ncb_options:
    #             option_text = option.text.strip()
    #             available_ncbs.append(option_text)
    #             if option_text == previous_year_ncb:
    #                 ncb_found = True
    #
    #         if not ncb_found:
    #             logger.info(f"NCB {previous_year_ncb} not found in UI. Available NCBs: {available_ncbs}")
    #             PolicyBazaarNavigation._take_screenshot(driver, f"ncb_{previous_year_ncb}_not_found",
    #                                                     record_id, car_number, screenshot_dir,mail_sent, email_config)
    #             return False
    #
    #         ncb_option = wait.until(EC.element_to_be_clickable((
    #             By.XPATH, f"//ul/li[@role='button' and text()='{previous_year_ncb}']")
    #         ))
    #         PolicyBazaarNavigation._safe_click(ncb_option, f"ncbOption_{previous_year_ncb}",
    #                                            record_id, car_number, driver, screenshot_dir, mail_sent, email_config)
    #         logger.info(f"Selected NCB: {previous_year_ncb}")
    #
    #         record.selected_ncb = previous_year_ncb
    #
    #         time.sleep(2)
    #         return True
    #
    #     except TimeoutException as e:
    #         logger.info(f"Error: NCB dropdown not found or no NCB options available: ")
    #         PolicyBazaarNavigation._take_screenshot(driver, "ncb_dropdown_error", record_id, car_number, screenshot_dir, mail_sent, email_config)
    #         return False
    #
    #     except Exception as e:
    #
    #         logger.info(f"Unexpected error during NCB selection: ")
    #
    #         PolicyBazaarNavigation._take_screenshot(driver, "ncb_selection_unexpected_error", record_id, car_number, screenshot_dir, mail_sent, email_config)
    #         return False
    # @staticmethod
    # def _handle_claim_checkbox(driver, wait, record, record_id, car_number, screenshot_dir, mail_sent, email_config):
    #     claim_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH,
    #                                                            "//label[contains(text(),'Did you make claim')]/following-sibling::div[contains(@class,'toggle-wrapper')]//input[@type='checkbox']")))
    #
    #     selected_ncb = record.selected_ncb or "0%"
    #     if not selected_ncb.endswith('%'):
    #         selected_ncb += '%'
    #
    #     if selected_ncb == "0%" and not claim_checkbox.is_selected():
    #         PolicyBazaarNavigation._safe_click(claim_checkbox, "claimCheckbox", record_id, car_number, driver, screenshot_dir, mail_sent, email_config)
    #
    #         time.sleep(2)
    #     else:
    #
    #         time.sleep(2)


    @staticmethod
    def _select_previous_insurer(driver, wait, record_id, car_number, screenshot_dir, mail_sent, email_config):
        try:
            if driver.find_elements(By.XPATH, "//div[contains(@class, 'form-group-border disabled')]//div[@class='label' and text()= 'Previous Insurer']"):
                logger.info(f"Previous Insurer dropdown is disabled for Record ID: {record_id}")
                PolicyBazaarNavigation._take_screenshot(driver, "previous_year_dropdown_disabled", record_id, car_number,
                                                        screenshot_dir, mail_sent, email_config)
                return False
            previous_insurer = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//div[@class='right']//div[@class='customSelectValueContainer css-hlgwow']")))
            PolicyBazaarNavigation._safe_click(previous_insurer, "previousInsurer_dropdown",
                                               record_id, car_number, driver, screenshot_dir, mail_sent, email_config)
            time.sleep(3)

            # previous_insurer2 = wait.until(EC.element_to_be_clickable((
            #     By.XPATH, "//div[contains(text(),'Bajaj Allianz')]"
            # )))
            previous_insurer2 = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//div[contains(text(),'National Insurance')]"
            )))
            PolicyBazaarNavigation._safe_click(previous_insurer2, "previous_insurer",
                                               record_id, car_number, driver, screenshot_dir, mail_sent, email_config)
            time.sleep(2)
            return True

        except Exception as e:
            logger.info(f"Previous insurer selection failed for record ID: {record_id}")
            return False



    @staticmethod
    def _select_idv(driver, wait, record_id, car_number, screenshot_dir, mail_sent, email_config):
        dropdown_idv = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//p[normalize-space()='Select IDV']//span[@class='arrowRight whiteArrowDown']"
        )))
        PolicyBazaarNavigation._safe_click(dropdown_idv, "dropdownIDV", record_id, car_number, driver, screenshot_dir, mail_sent, email_config)
        time.sleep(2)

        select_idv = wait.until(EC.element_to_be_clickable((
            By.XPATH, "(//span[normalize-space()='Minimum IDV'])[1]"
        )))
        PolicyBazaarNavigation._safe_click(select_idv, "selectIDV", record_id, car_number, driver, screenshot_dir, mail_sent, email_config)
        time.sleep(3)

        update_idv = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[normalize-space()='Update']"
        )))
        PolicyBazaarNavigation._safe_click(update_idv, "updateIDV", record_id, car_number, driver, screenshot_dir, mail_sent, email_config)
        time.sleep(2)

    @staticmethod
    def _select_add_ons(driver, wait, add_on_string, record_id, car_number, screenshot_dir, mail_sent, email_config):
        all_add_ons = {
            "zero depreciation": "Zero Depreciation",
            "24x7 roadside assistance": "24x7 Roadside Assistance",
            "engine protection cover": "Engine Protection Cover",
            "consumables": "Consumables",
            "key & lock replacement": "Key & Lock Replacement",
            "invoice price cover": "Invoice Price Cover",
            "tyre protector": "Tyre Protector",
            "loss of personal belongings": "Loss of Personal Belongings",
            "daily allowance": "Daily Allowance",
            "rim damage cover": "RIM Damage Cover",
            "ncb protector": "NCB Protector"
        }

        if not add_on_string or not add_on_string.strip():
            logger.info("No add-ons specified in input")
            return None


        try:
            see_all_button = wait.until(EC.element_to_be_clickable((
                By.XPATH, "(//button[contains(text(),'See all')])[1]"
            )))
            see_all_button.click()

        except Exception as e:
            logger.info(f"Error clicking 'See All' button:")


            time.sleep(2)

        longer_wait = WebDriverWait(driver, 10)
        longer_wait.until(EC.visibility_of_element_located((
            By.XPATH, "//div[contains(@class, 'customCheckbox')]"
        )))

        normalized_add_ons = (add_on_string.replace("+", ",")
                              .replace(" and ", ",")
                              .replace(";", ","))
        normalized_add_ons = ",".join([part.strip() for part in normalized_add_ons.split(",")])
        normalized_add_ons = normalized_add_ons.lower().strip()

        add_on_array = normalized_add_ons.split(",")
        add_ons_to_select = set()

        for add_on in add_on_array:
            trimmed = add_on.strip().lower()
            if trimmed and trimmed in all_add_ons:
                add_ons_to_select.add(trimmed)

        selected_count = 0
        for identifier, display_name in all_add_ons.items():
            try:
                xpath = f"//div[contains(@class, 'customCheckbox') and contains(., '{display_name}')]"
                add_on_elements = driver.find_elements(By.XPATH, xpath)
                is_available = len(add_on_elements) > 0 and add_on_elements[0].is_displayed()

                if is_available and identifier in add_ons_to_select:
                    add_on_div = longer_wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
                    checkbox = add_on_div.find_element(By.XPATH, ".//input[@type='checkbox']")
                    label = add_on_div.find_element(By.XPATH, ".//label")

                    if not checkbox.is_selected():
                        driver.execute_script("arguments[0].scrollIntoView(true);", label)
                        driver.execute_script("arguments[0].click();", label)
                        selected_count += 1
                        time.sleep(1)
                    else:
                        logger.info(f"Add-on already selected: {display_name}")

                elif not is_available and identifier in add_ons_to_select:
                    logger.info(f"Requested add-on not available: {display_name}")
                    PolicyBazaarNavigation._take_screenshot(driver, f"add_on_not_available_{display_name}",
                                                            record_id, car_number, screenshot_dir, mail_sent, email_config)

            except (NoSuchElementException, TimeoutException) as e:
                if identifier in add_ons_to_select:
                    logger.info(f"Error with add-on {display_name} ")


                    PolicyBazaarNavigation._take_screenshot(driver, f"add_on_error_{display_name}",
                                                            record_id, car_number, screenshot_dir, mail_sent, email_config)

        logger.info(f"Total add-ons successfully selected: {selected_count}")
        return selected_count


    @staticmethod
    def _scrape_insurance_data(connection, driver, wait, record, screenshot_dir, mail_sent, email_config):
        record_id = record.get_id()
        car_number = record.get_registration_number()
        try:
            time.sleep(5)
            wait.until(EC.visibility_of_element_located((
                By.XPATH, "//span[contains(@class,'insurerLogo')]/img[contains(@class,'imgLogo')]"
            )))
            insurance_logos = driver.find_elements(By.XPATH, "//span[contains(@class,'insurerLogo')]")
        except TimeoutException as e:
            logger.info(f"Timeout waiting for insurer logo elements: ")

            PolicyBazaarNavigation._take_screenshot(driver, "insurer_logos_timeout_error",
                                                    record_id, car_number, screenshot_dir, mail_sent, email_config)
            insurance_logos = []
            logger.info("Proceeding with empty insurance logos list.")

        liberty_details = None
        top_details = []
        wishlists = []

        size_of_insurer = len(insurance_logos)
        logger.info(f"Total Insurance Providers: {size_of_insurer}")

        processed_insurance = set()
        liberty_insurance_name = "Liberty General Insurance"

        wish_list = PolicyDatabase.fetch_wishlist_name(record.get_wishlist())
        time.sleep(2)

        liberty_ranking = None
        for i in range(1, size_of_insurer + 1):
            try:
                insurer_logo = wait.until(EC.visibility_of_element_located((
                    By.XPATH, f"(//span[contains(@class,'insurerLogo')]/img)[{i}]"
                )))
                insurance_name = insurer_logo.get_attribute("alt")
                time.sleep(1)
                if insurance_name and "Liberty General Insurance".lower() in insurance_name.lower():
                    liberty_ranking = i
                    logger.info(f"Liberty General Insurance found at ranking: {liberty_ranking}")

                time.sleep(1)
            except TimeoutException as e:
                PolicyBazaarNavigation._take_screenshot(driver, f"insurer_logo_timeout_{i}",
                                                        record_id, car_number, screenshot_dir, mail_sent, email_config)
                continue

        for i in range(1, size_of_insurer + 1):
            try:
                insurer_logo = driver.find_element(
                    By.XPATH, f"(//span[contains(@class,'insurerLogo')]/img)[{i}]"
                )
                PolicyBazaarNavigation._safe_click(insurer_logo, f"insurer_logo_{i}",
                                                   record_id, car_number, driver,screenshot_dir, mail_sent, email_config)
                time.sleep(2)

                insurance_name = insurer_logo.get_attribute("alt")
                time.sleep(1)

                if (liberty_details is None and insurance_name and
                        liberty_insurance_name.lower() in insurance_name.lower()):
                    liberty_details = PolicyBazaarNavigation._navigation_helper(
                        driver, wait, i, insurance_name, record_id, car_number, screenshot_dir
                    , mail_sent, email_config)
                    time.sleep(2)
                    processed_insurance.add(insurance_name)
                    time.sleep(2)
                    break

            except TimeoutException as e:
                logger.info(f"Timeout waiting for insurer logo {i}")


                PolicyBazaarNavigation._take_screenshot(driver, f"insurer_logo_timeout_{i}",
                                                        record_id, car_number, screenshot_dir, mail_sent, email_config)
                continue


        validated_top_count = 0
        for i in range(1, size_of_insurer + 1):
            if validated_top_count >= 5:
                break

            try:
                insurer_logo = driver.find_element(
                    By.XPATH, f"(//span[contains(@class,'insurerLogo')]/img)[{i}]"
                )
                insurance_name = insurer_logo.get_attribute("alt")
                time.sleep(1)

                if not insurance_name or insurance_name in processed_insurance:
                    continue

                top_detail = PolicyBazaarNavigation._navigation_helper(
                    driver, wait, i, insurance_name, record_id, car_number, screenshot_dir
                , mail_sent, email_config)
                top_details.append(top_detail)
                processed_insurance.add(insurance_name)
                validated_top_count += 1


            except Exception as e:

                logger.info(f"Error processing top insurer logo {i}: ")

                PolicyBazaarNavigation._take_screenshot(driver, f"top_insurer_error_{i}",
                                                        record_id, car_number, screenshot_dir, mail_sent, email_config)
                continue

        logger.info(f"Total validated top 5 insurers processed: {validated_top_count}")

        wishlist_count = 0
        wishlist_processed = set()

        for i in range(1, size_of_insurer + 1):
            if wishlist_count >= 4:
                break

            try:
                insurer_logo = wait.until(EC.visibility_of_element_located((
                    By.XPATH, f"(//span[contains(@class,'insurerLogo')]/img)[{i}]"
                )))
                insurance_name = insurer_logo.get_attribute("alt")
                time.sleep(1)

                if not insurance_name or insurance_name in wishlist_processed:
                    continue

                for wish_item in wish_list:
                    if wish_item and wish_item.lower().strip() in insurance_name.lower():
                        wish_detail = PolicyBazaarNavigation._navigation_helper(
                            driver, wait, i, insurance_name, record_id, car_number, screenshot_dir
                        , mail_sent, email_config)
                        wishlists.append(wish_detail)
                        wishlist_processed.add(insurance_name)
                        wishlist_count += 1
                        time.sleep(2)
                        break


            except (TimeoutException, NoSuchElementException) as e:
                logger.info(f"Error processing wishlist insurer {i}: ")


                PolicyBazaarNavigation._take_screenshot(driver, f"wishlist_insurer_error_{i}",
                                                        record_id, car_number, screenshot_dir, mail_sent, email_config)
                continue

        top5 = [None] * 5
        for i in range(min(5, len(top_details))):
            top5[i] = top_details[i]

        wish_details = [None] * 4
        for i in range(min(4, len(wishlists))):
            wish_details[i] = wishlists[i]

        time.sleep(2)

        PolicyDatabase.insert_policy_details(
            connection, record_id, liberty_details,
            top5[0], top5[1], top5[2], top5[3], top5[4],
            wish_details[0], wish_details[1], wish_details[2], wish_details[3]
        )

    @staticmethod
    def _navigation_helper(driver, wait, index, insurance_name, record_id, car_number, screenshot_dir, mail_sent, email_config):

        details = InsuranceDetails()
        details.insurer = "Zuno General" if insurance_name and "insurer" in insurance_name.lower() else insurance_name

        details.ranking = index

        try:

            policy_buttons = driver.find_elements(By.XPATH, "//p[contains(text(),'Policy Details')]")

            if index <= len(policy_buttons):
                policy_button = policy_buttons[index - 1]
                wait.until(lambda d: policy_button.is_displayed() and policy_button.is_enabled())
                PolicyBazaarNavigation._safe_click(policy_button, f"policyButton_{insurance_name}",
                                                   record_id, car_number, driver, screenshot_dir, mail_sent, email_config)
                time.sleep(2)

            time.sleep(5)

            details.carvalue = PolicyBazaarNavigation._get_value_safely(driver, "(//div[@class='headingV3'])[1]")
            time.sleep(1)

            details.damage = PolicyBazaarNavigation._get_value_safely(driver,
                                                                      "//li[contains(text(),'Premium Breakup')]/following::p[contains(text(),'Basic Own Damage Premium')][1]/following::p[1]")
            time.sleep(1)

            details.third_party_cover_premium = PolicyBazaarNavigation._get_value_safely(driver,
                                                                                         "//p[@class='textGray' and contains(text(), 'Third Party Cover Premium')]/following::p[1]")
            time.sleep(1)

            details.zero_depreciation = PolicyBazaarNavigation._get_value_safely(driver,
                                                                                 "//p[@class='textGray' and contains(text(), 'Zero Depreciation')]/following::p[1]")
            time.sleep(1)

            details.roadside = PolicyBazaarNavigation._get_value_safely(driver,
                                                                        "//p[@class='textGray' and contains(text(), '24x7 Roadside Assistance')]/following::p[1]")
            time.sleep(1)

            details.engine_protection_cover = PolicyBazaarNavigation._get_value_safely(driver,
                                                                                       "//p[@class='textGray' and contains(text(), 'Engine Protection Cover')]/following::p[1]")
            time.sleep(1)

            details.consumables = PolicyBazaarNavigation._get_value_safely(driver,
                                                                           "//p[@class='textGray' and contains(text(), 'Consumables')]/following::p[1]")
            time.sleep(1)

            details.package_premium = PolicyBazaarNavigation._get_value_safely(driver,
                                                                               "(//p[contains(text(),'Package Premium')]/following::p)[1]")
            time.sleep(1)

            details.premium = PolicyBazaarNavigation._get_value_safely(driver,
                                                                       "(//div[contains(text(),'Final premium ')]/following::span)[1]")
            time.sleep(1)

            details.tyre = PolicyBazaarNavigation._get_value_safely(driver,
                                                                    "(//p[@class='textGray' and contains(text(), 'Tyre Protector')]/following::p[1])")
            time.sleep(1)

            details.key_lock_replacement = PolicyBazaarNavigation._get_value_safely(driver,
                                                                                    "//p[@class='textGray' and normalize-space(text()) = 'Key & Lock Replacement']/following::p[1]")
            time.sleep(1)

            details.gap_cover = PolicyBazaarNavigation._get_value_safely(driver,
                                                                                    "//p[@class='textGray' and normalize-space(text()) = 'Invoice Price']/following::p[1]")
            time.sleep(1)

            details.loss_of_personal_belongings = PolicyBazaarNavigation._get_value_safely(driver,
                                                                                           "//p[@class='textGray' and normalize-space(text()) = 'Loss of Personal Belongings']/following::p[1]")
            time.sleep(1)

            details.daily_allowance = PolicyBazaarNavigation._get_value_safely(driver,
                                                                                           "//p[@class='textGray' and normalize-space(text()) = 'Daily Allowance']/following::p[1]")
            time.sleep(1)

            details.rim_damage_cover = PolicyBazaarNavigation._get_value_safely(driver,
                                                                                           "//p[@class='textGray' and normalize-space(text()) = 'RIM Damage Cover']/following::p[1]")
            time.sleep(1)

            details.ncb_protector = PolicyBazaarNavigation._get_value_safely(driver,
                                                                                           "//p[@class='textGray' and normalize-space(text()) = 'NCB Protector']/following::p[1]")
            time.sleep(1)

            details.premium_other_addon_autoselected_bundle = PolicyBazaarNavigation._combine_additional_addons(
                details.key_lock_replacement,
                details.daily_allowance,
                details.rim_damage_cover,
                details.ncb_protector,
                details.loss_of_personal_belongings
            )



            close_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='crossBtn']")))
            PolicyBazaarNavigation._safe_click(close_btn, f"closeBtn_{insurance_name}",
                                               record_id, car_number, driver, screenshot_dir, mail_sent, email_config)
            time.sleep(1)

        except Exception as e:
            logger.info(f"Error scraping details for {insurance_name}")
            PolicyBazaarNavigation._take_screenshot(driver, f"scrape_error_{insurance_name}",
                                                    record_id, car_number, screenshot_dir, mail_sent, email_config)

        return details

    @staticmethod
    def _combine_additional_addons(key_lock_replacement, daily_allowance, rim_damage_cover,
                                   ncb_protector, loss_of_personal_belongings):

        addon_components = []

        addons = [
            ("Key & Lock Replacement", key_lock_replacement),
            ("Daily Allowance", daily_allowance),
            ("RIM Damage Cover", rim_damage_cover),
            ("NCB Protector", ncb_protector),
            ("Loss of Personal Belongings", loss_of_personal_belongings)
        ]

        for addon_name, addon_value in addons:
            if addon_value and addon_value.strip() and addon_value.strip().lower() != "not available":
                cleaned_value = addon_value.strip()
                addon_components.append(f"{addon_name}:{cleaned_value}")

        if not addon_components:
            return "Not Available"
        else:
            return ",".join(addon_components)
    @staticmethod
    def _get_value_safely(driver, xpath):

        try:
            elements = driver.find_elements(By.XPATH, xpath)
            if elements and elements[0].is_displayed():
                return PolicyBazaarNavigation._clean_value(elements[0].text)
        except Exception:
            pass
        return "Not Available"

    @staticmethod
    def _clean_value(value):
        return value.replace("₹", "").replace(",", "").replace("-", "").replace(" ", "").strip()

    @staticmethod
    def _safe_click(element, element_name, record_id, car_number, driver, screenshot_dir, mail_sent, email_config, max_attempts=2):

        for attempt in range(max_attempts):
            try:
                element.click()
                return
            except Exception as e:
                if attempt == max_attempts - 1:
                    logger.info(f"Error clicking {element_name} ")


                    PolicyBazaarNavigation._take_screenshot(driver, f"{element_name}_error",
                                                            record_id, car_number, screenshot_dir, mail_sent, email_config)
                    raise
                time.sleep(1)

    @staticmethod
    def _safe_send_keys(element, text, element_name, record_id, car_number, driver, screenshot_dir, mail_sent, email_config, max_attempts=2):

        for attempt in range(max_attempts):
            try:
                element.send_keys(text)
                # logger.info(f"{element_name} entered ({'First' if attempt == 0 else 'Second'} attempt)")
                return
            except Exception as e:
                if attempt == max_attempts - 1:

                    logger.info(f"Error entering {element_name} ")
                    PolicyBazaarNavigation._take_screenshot(driver, f"{element_name}_error",
                                                            record_id, car_number, screenshot_dir, mail_sent, email_config)
                    raise
                time.sleep(1)

    @staticmethod
    def _take_screenshot(driver, file_name, record_id, car_number, screenshot_dir, mail_sent, email_config):

        custom_directory = screenshot_dir
        full_file_name = f"{file_name}_{int(time.time() * 1000)}.png"
        destination = os.path.join(custom_directory, full_file_name)

        try:
            os.makedirs(custom_directory, exist_ok=True)

            if not os.access(custom_directory, os.W_OK):
                logger.info(f"Directory is not writable: {custom_directory}")
                if record_id not in mail_sent:

                    EmailSender.send_error_email(
                        None, f"Directory Not Writable: {file_name}",
                        str(record_id), car_number, email_config
                    )
                    PolicyBazaarNavigation.mail_sent.add(record_id)
                    logger.info(f"Directory Not Writable Email sent")
                    return

            success = driver.save_screenshot(destination)

            if not success or not os.path.exists(destination):
                logger.info(f"Screenshot file was not created: {destination}")
                if record_id not in mail_sent:

                    EmailSender.send_error_email(
                        None, f"Screenshot File Not Created: {file_name}",
                        str(record_id), car_number
                    , email_config)
                    PolicyBazaarNavigation.mail_sent.add(record_id)
                    logger.info(f"Screenshot File Not Created Email sent")
                return
            logger.info(f"Screenshot taken: {destination}")
            if record_id not in mail_sent:
                EmailSender.send_error_email(destination, file_name, str(record_id), car_number, email_config)
                PolicyBazaarNavigation.mail_sent.add(record_id)
                logger.info(f"Error Email sent of {record_id}")

        except Exception as e:
            logger.info(f"Error taking or saving screenshot: ")


            if record_id not in mail_sent:
                logger.info(f"Error taking or saving screenshot: ")
                EmailSender.send_error_email(
                    None, f"Screenshot Failure: {file_name} ",
                    str(record_id), car_number, email_config)
                PolicyBazaarNavigation.mail_sent.add(record_id)