from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement as SeleniumWebElement
import time
import logging

logger = logging.getLogger(__name__)

def safe_click(driver, element, description="element", max_attempts=3):
    """
    Safely click an element with comprehensive error handling and retry logic.
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import (
        ElementClickInterceptedException, 
        StaleElementReferenceException,
        ElementNotInteractableException,
        TimeoutException,
        NoSuchElementException
    )
    import time
    
    logger.info(f"Attempting to click {description}")
    
    # Validate inputs
    if not element:
        logger.error(f"No element provided for {description}")
        return False
    
    # Check if we accidentally got the driver instead of element
    # If a driver instance (has find_element and no tag_name), reject
    try:
        _ = element.tag_name  # WebElement has tag_name
    except Exception:
        if hasattr(element, 'find_element'):
            logger.error(f"Driver object passed instead of element for {description}")
            return False
    
    for attempt in range(max_attempts):
        try:
            logger.debug(f"Click attempt {attempt + 1} for {description}")
            
            # Wait longer between attempts to let page settle
            if attempt > 0:
                wait_time = 3 + (attempt * 2)  # 3s, 5s, 7s
                logger.debug(f"Waiting {wait_time}s before attempt {attempt + 1}")
                time.sleep(wait_time)
            
            # Check if element is stale and re-find if necessary
            try:
                # Use a safer way to check if element is stale
                element.tag_name  # This will throw if stale
            except StaleElementReferenceException:
                logger.warning(f"Element became stale on attempt {attempt + 1}")
                if attempt < max_attempts - 1:
                    continue
                else:
                    raise
            except Exception as e:
                logger.warning(f"Error checking element state: {e}")
                if attempt < max_attempts - 1:
                    continue
                else:
                    raise
            
            # 1. Check for and dismiss any blocking overlays/modals
            overlay_selectors = [
                '[data-testid="confirmationSheetDialog"]',
                '[data-testid="sheetDialog"]',
                '[data-testid="mask"]',
                '.r-aqfbo4',  # Twitter modal backdrop
                '[data-testid="app-bar-close"]'
            ]
            # Detect if the compose modal is active; avoid sending ESC if so
            compose_active = False
            compose_url_active = False
            try:
                current_url = driver.current_url.lower()
                compose_url_active = ("compose/post" in current_url)
                # Consider compose active if any tweet textareas OR any contenteditable textboxes are visible
                textarea_visible = any(
                    e.is_displayed() for e in driver.find_elements(
                        By.CSS_SELECTOR,
                        '[role="dialog"] [data-testid^="tweetTextarea_"], [data-testid^="tweetTextarea_"], [contenteditable="true"][role="textbox"]'
                    )
                )
                compose_active = compose_url_active or textarea_visible
            except Exception:
                compose_active = False
                compose_url_active = False
            
            for selector in overlay_selectors:
                try:
                    # Avoid closing the compose backdrop/mask while composing a thread
                    if compose_active and selector in ('[data-testid="mask"]', '.r-aqfbo4'):
                        continue
                    overlays = driver.find_elements(By.CSS_SELECTOR, selector)
                    for overlay in overlays:
                        if overlay.is_displayed():
                            logger.debug(f"Found blocking overlay: {selector}")
                            # Try to close it
                            close_buttons = overlay.find_elements(By.CSS_SELECTOR, 
                                '[data-testid="app-bar-close"], [aria-label*="Close"], button[aria-label*="close"]')
                            if close_buttons:
                                close_buttons[0].click()
                                time.sleep(1)
                            else:
                                # Only send ESC if compose modal is NOT active (to avoid closing composer and prompting Save/Discard)
                                try:
                                    from selenium.webdriver.common.keys import Keys
                                    if not compose_active:
                                        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                                        time.sleep(1)
                                except Exception:
                                    pass
                except Exception as e:
                    logger.debug(f"Error handling overlay {selector}: {e}")
            
            # 2. Wait for element to be clickable with longer timeout
            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(element)
                )
            except TimeoutException:
                logger.warning(f"Element not clickable after 10s wait on attempt {attempt + 1}")
                if attempt < max_attempts - 1:
                    continue
            
            # 3. Scroll element into view and wait
            try:
                driver.execute_script("""
                    arguments[0].scrollIntoView({
                        behavior: 'smooth',
                        block: 'center',
                        inline: 'center'
                    });
                """, element)
                time.sleep(1.5)  # Longer wait for scroll to complete
            except Exception as e:
                logger.debug(f"Error scrolling element into view: {e}")
            
            # 4. Check if element is actually visible and interactable
            try:
                if not element.is_displayed():
                    logger.warning(f"Element not displayed on attempt {attempt + 1}")
                    if attempt < max_attempts - 1:
                        continue
                    else:
                        raise ElementNotInteractableException(f"Element {description} not displayed")
                
                if not element.is_enabled():
                    logger.warning(f"Element not enabled on attempt {attempt + 1}")
                    if attempt < max_attempts - 1:
                        continue
                    else:
                        raise ElementNotInteractableException(f"Element {description} not enabled")
            except Exception as e:
                logger.debug(f"Error checking element visibility/enabled state: {e}")
                # Continue anyway, maybe the element is still clickable
            
            # 5. Try different click strategies
            click_successful = False
            
            # Strategy A: Regular click
            try:
                element.click()
                click_successful = True
                logger.debug(f"Regular click successful for {description}")
            except (ElementClickInterceptedException, ElementNotInteractableException) as e:
                logger.debug(f"Regular click failed: {e}")
            except Exception as e:
                logger.debug(f"Regular click failed with unexpected error: {e}")
            
            # Strategy B: ActionChains click
            if not click_successful:
                try:
                    ActionChains(driver).move_to_element(element).pause(0.5).click().perform()
                    click_successful = True
                    logger.debug(f"ActionChains click successful for {description}")
                except Exception as e:
                    logger.debug(f"ActionChains click failed: {e}")
            
            # Strategy C: JavaScript click
            if not click_successful:
                try:
                    driver.execute_script("arguments[0].click();", element)
                    click_successful = True
                    logger.debug(f"JavaScript click successful for {description}")
                except Exception as e:
                    logger.debug(f"JavaScript click failed: {e}")
            
            # Strategy D: Force click with JavaScript
            if not click_successful:
                try:
                    driver.execute_script("""
                        var element = arguments[0];
                        var event = new MouseEvent('click', {
                            view: window,
                            bubbles: true,
                            cancelable: true
                        });
                        element.dispatchEvent(event);
                    """, element)
                    click_successful = True
                    logger.debug(f"Force JavaScript click successful for {description}")
                except Exception as e:
                    logger.debug(f"Force JavaScript click failed: {e}")
            
            if click_successful:
                logger.info(f"✅ Successfully clicked {description} on attempt {attempt + 1}")
                # Guard: if a Save/Discard (confirmation sheet) dialog appeared, cancel it and refocus compose
                try:
                    dialog = None
                    dialogs = driver.find_elements(By.CSS_SELECTOR, '[data-testid="confirmationSheetDialog"], [data-testid="sheetDialog"]')
                    for d in dialogs:
                        try:
                            if d.is_displayed():
                                dialog = d
                                break
                        except Exception:
                            continue
                    if dialog:
                        # Prefer explicit cancel/keep editing options if present
                        cancel_btn = None
                        try:
                            # Known testid for cancel in some flows
                            elems = dialog.find_elements(By.CSS_SELECTOR, '[data-testid="confirmationSheetCancel"]')
                            cancel_btn = elems[0] if elems else None
                        except Exception:
                            cancel_btn = None
                        if not cancel_btn:
                            # Fallbacks by visible text
                            try:
                                cancel_btn = dialog.find_element(By.XPATH, './/span[normalize-space(.)="Cancel"]/ancestor::*[@role="button" or self::button][1]')
                            except Exception:
                                try:
                                    # Match "Keep editing" variants, case-insensitive
                                    cancel_btn = dialog.find_element(
                                        By.XPATH,
                                        './/span[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "keep") and contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "edit")]/ancestor::*[@role="button" or self::button][1]'
                                    )
                                except Exception:
                                    cancel_btn = None
                            # Additional variants: "Stay", "Continue editing"
                            if not cancel_btn:
                                for xp in [
                                    './/span[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "stay")]/ancestor::*[@role="button" or self::button][1]',
                                    './/span[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "continue") and contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "edit")]/ancestor::*[@role="button" or self::button][1]'
                                ]:
                                    try:
                                        cancel_btn = dialog.find_element(By.XPATH, xp)
                                        if cancel_btn:
                                            break
                                    except Exception:
                                        pass
                        if cancel_btn:
                            try:
                                cancel_btn.click()
                                time.sleep(0.5)
                            except Exception:
                                pass
                        # Refocus the composer textbox if available
                        try:
                            editors = driver.find_elements(By.CSS_SELECTOR, '[role="dialog"] [contenteditable="true"][role="textbox"], [contenteditable="true"][role="textbox"]')
                            if editors:
                                editors[-1].click()
                                time.sleep(0.2)
                        except Exception:
                            pass
                except Exception:
                    pass
                time.sleep(2)  # Wait for any animations/transitions
                return True
            else:
                logger.warning(f"All click strategies failed on attempt {attempt + 1}")
                if attempt < max_attempts - 1:
                    continue
        
        except StaleElementReferenceException:
            logger.warning(f"Element became stale on attempt {attempt + 1}")
            if attempt < max_attempts - 1:
                continue
            else:
                raise
        
        except Exception as e:
            logger.warning(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < max_attempts - 1:
                continue
            else:
                raise
    
    logger.error(f"All {max_attempts} click attempts failed for {description}")
    return False


def safe_textbox_click(driver, target, logger_ref=None, max_retries=3):
    """
    Safely focus/click the current DraftJS contenteditable textbox in the Twitter/X composer.

    Supports:
    - target as a locator tuple: (By.CSS_SELECTOR, '[contenteditable=\"true\"][role=\"textbox\"]')
    - target as a WebElement (will drill down to the inner contenteditable if needed)

    Returns True if the textbox is focused/clicked successfully, False otherwise.
    """
    try:
        # Lazy imports to avoid hard dependencies at module import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.keys import Keys
        from selenium.common.exceptions import (
            NoSuchElementException,
            StaleElementReferenceException,
            ElementNotInteractableException,
        )
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time

        log = logger_ref or logger

        def _find_visible_textboxes():
            """Find all visible contenteditable textboxes on the page."""
            elements = driver.find_elements(By.CSS_SELECTOR, '[contenteditable="true"][role="textbox"]')
            return [e for e in elements if e.is_displayed()]

        # Resolve the target element
        element = None
        if isinstance(target, tuple) and len(target) == 2:
            by, selector = target
            try:
                candidates = driver.find_elements(by, selector)
            except Exception:
                candidates = []
            visible = [e for e in candidates if e.is_displayed()]
            if not visible and by != By.CSS_SELECTOR:
                # Fallback to CSS selector if locator type isn't CSS
                try:
                    candidates = driver.find_elements(By.CSS_SELECTOR, selector)
                    visible = [e for e in candidates if e.is_displayed()]
                except Exception:
                    visible = []
            if visible:
                # Prefer the last visible editable (newly added tweets often appear at bottom)
                element = visible[-1]
        elif hasattr(target, "tag_name"):
            element = target

        # If the provided element isn't the inner contenteditable, try to drill in
        if element is not None:
            try:
                if element.get_attribute("contenteditable") != "true" or element.get_attribute("role") != "textbox":
                    inner = element.find_element(By.CSS_SELECTOR, '[contenteditable="true"][role="textbox"]')
                    if inner and inner.is_displayed():
                        element = inner
            except Exception:
                pass

        # If we still don't have an element, try discovering any visible textboxes
        if element is None:
            boxes = _find_visible_textboxes()
            if boxes:
                element = boxes[-1]  # choose last visible
            else:
                # As a final fallback, try to open a compose area then re-scan
                try:
                    compose_button = None
                    # Try common compose triggers
                    for sel in (
                        '[data-testid="SideNav_NewTweet_Button"]',
                        '[href="/compose/post"]',
                        '[aria-label*="Post"]',
                    ):
                        btns = driver.find_elements(By.CSS_SELECTOR, sel)
                        compose_button = next((b for b in btns if b.is_displayed()), None)
                        if compose_button:
                            break
                    if compose_button:
                        safe_click(driver, compose_button, description="compose trigger", max_attempts=2)
                        time.sleep(1.5)
                        boxes = _find_visible_textboxes()
                        if boxes:
                            element = boxes[-1]
                except Exception:
                    pass

        if element is None:
            log.warning("safe_textbox_click: No contenteditable textbox found")
            return False

        # Dismiss potential overlays (reuse safe_click's logic indirectly by ESC and overlay selectors)
        try:
            overlay_selectors = [
                '[data-testid="confirmationSheetDialog"]',
                '[data-testid="sheetDialog"]',
                '[data-testid="mask"]',
                '.r-aqfbo4',  # Twitter modal backdrop
                '[data-testid="app-bar-close"]',
            ]
            # Avoid sending ESC if compose is active
            compose_active = False
            compose_url_active = False
            try:
                current_url = driver.current_url.lower()
                compose_url_active = ("compose/post" in current_url)
                compose_active = any(
                    e.is_displayed() for e in driver.find_elements(
                        By.CSS_SELECTOR,
                        '[role="dialog"] [data-testid^="tweetTextarea_"], [data-testid^="tweetTextarea_"], [contenteditable="true"][role="textbox"]'
                    )
                ) or compose_url_active
            except Exception:
                compose_active = False
                compose_url_active = False
            for selector in overlay_selectors:
                overlays = driver.find_elements(By.CSS_SELECTOR, selector)
                for overlay in overlays:
                    if overlay.is_displayed():
                        # Do not close compose backdrop/mask while composer is active
                        if compose_active and selector in ('[data-testid="mask"]', '.r-aqfbo4'):
                            continue
                        if not compose_active:
                            try:
                                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                                time.sleep(0.2)
                            except Exception:
                                pass
        except Exception:
            pass

        # Attempt focus/click with retries
        for attempt in range(max_retries):
            try:
                # Ensure element is not stale
                _ = element.tag_name  # will raise if stale
            except StaleElementReferenceException:
                # Re-resolve fresh textbox reference
                boxes = _find_visible_textboxes()
                element = boxes[-1] if boxes else None
                if element is None:
                    if attempt < max_retries - 1:
                        time.sleep(0.5)
                        continue
                    log.warning("safe_textbox_click: Textbox went stale and could not be re-found")
                    return False
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue

            # Scroll into view
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior:'smooth',block:'center',inline:'center'});", element
                )
                time.sleep(0.4)
            except Exception:
                pass

            # Wait for interactability
            try:
                WebDriverWait(driver, 5).until(EC.visibility_of(element))
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(0.5)

            # Try different strategies to focus/click the textbox
            try:
                element.click()
            except Exception:
                try:
                    ActionChains(driver).move_to_element(element).pause(0.2).click().perform()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", element)
                    except Exception:
                        pass

            # Send an extra click and small key to ensure DraftJS focus
            try:
                ActionChains(driver).move_to_element(element).pause(0.1).click().send_keys(Keys.SPACE).send_keys(Keys.BACK_SPACE).perform()
            except Exception:
                pass

            # Verify active element is the textbox
            try:
                is_active = driver.execute_script(
                    "var el = arguments[0]; var a = document.activeElement; "
                    "return !!a && (a === el || (a.getAttribute('contenteditable')==='true' && a.getAttribute('role')==='textbox'));",
                    element
                )
            except Exception:
                is_active = False

            if is_active:
                log.info("✅ safe_textbox_click: Textbox focused/clicked successfully")
                return True

            # If not active, retry after slight delay
            time.sleep(0.6)

        log.warning("safe_textbox_click: All attempts failed to focus/click the textbox")
        return False

    except Exception as e:
        (logger_ref or logger).warning(f"safe_textbox_click unexpected error: {e}")
        return False
