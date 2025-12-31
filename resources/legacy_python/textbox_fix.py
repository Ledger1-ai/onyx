from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

def safe_textbox_click(driver, textbox, logger, max_retries=3):
    """Safely click textbox with comprehensive fallback handling for Twitter"""
    
    for attempt in range(max_retries):
        try:
            # Wait for textbox to be clickable
            wait = WebDriverWait(driver, 10)
            clickable_textbox = wait.until(EC.element_to_be_clickable(textbox))
            
            # Scroll into view with better positioning to avoid toolbar interception
            driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth', 
                    block: 'center',
                    inline: 'center'
                });
            """, clickable_textbox)
            time.sleep(1)  # Allow scroll animation and any dynamic content to settle
            
            # Dismiss any overlays that might intercept the click
            _dismiss_twitter_overlays(driver, logger)
            
            # Try regular click first
            clickable_textbox.click()
            logger.info(f"Clicked textbox successfully on attempt {attempt + 1}")
            
            # Verify the textbox is focused
            if _verify_textbox_focus(driver, clickable_textbox):
                return True
            else:
                logger.warning(f"Textbox not focused after click on attempt {attempt + 1}")
                
        except ElementClickInterceptedException as e:
            logger.warning(f"Textbox click intercepted on attempt {attempt + 1}: {e}")
            
            # Try to handle intercepting elements
            _handle_intercepting_elements(driver, textbox, logger)
            
            # Use JavaScript fallback
            try:
                driver.execute_script("arguments[0].click();", textbox)
                driver.execute_script("arguments[0].focus();", textbox)
                logger.info(f"JavaScript textbox click successful on attempt {attempt + 1}")
                return True
            except Exception as js_error:
                logger.warning(f"JavaScript textbox click failed: {js_error}")
                
        except StaleElementReferenceException:
            logger.warning(f"Textbox became stale on attempt {attempt + 1}")
            return False  # Caller should re-find the element
            
        except TimeoutException:
            logger.warning(f"Textbox not clickable within timeout on attempt {attempt + 1}")
            
        except Exception as e:
            logger.warning(f"Unexpected textbox click error on attempt {attempt + 1}: {e}")
        
        # Wait before retry
        if attempt < max_retries - 1:
            time.sleep(1.5)
    
    logger.error(f"Failed to click textbox after {max_retries} attempts")
    return False

def _dismiss_twitter_overlays(driver, logger):
    """Dismiss Twitter-specific overlays that commonly intercept textbox clicks"""
    overlay_selectors = [
        '[data-testid="app-bar-close"]',  # Twitter app bar
        '[data-testid="modal-header"] [role="button"]',  # Modal dialogs
        '[aria-label="Close"]',  # Generic close buttons
        '[data-testid="toast"] [role="button"]',  # Toast notifications
        '.r-1loqt21',  # Twitter overlay classes
        '[data-testid="toolBar"]',  # Tweet composer toolbar
        '[data-testid="tweetButtonInline"]',  # Inline tweet buttons that might overlay
    ]
    
    for selector in overlay_selectors:
        try:
            overlays = driver.find_elements(By.CSS_SELECTOR, selector)
            for overlay in overlays:
                if overlay.is_displayed() and overlay.is_enabled():
                    # Check if overlay is actually blocking
                    overlay_rect = driver.execute_script("""
                        var rect = arguments[0].getBoundingClientRect();
                        return {
                            top: rect.top,
                            left: rect.left,
                            bottom: rect.bottom,
                            right: rect.right
                        };
                    """, overlay)
                    
                    # Only dismiss if overlay is in a position that could block
                    if overlay_rect['top'] < 200:  # Top area where textboxes usually are
                        driver.execute_script("arguments[0].style.display = 'none';", overlay)
                        logger.info(f"Dismissed potentially blocking overlay: {selector}")
                        time.sleep(0.2)
        except Exception:
            continue  # Ignore errors when dismissing overlays

def _handle_intercepting_elements(driver, textbox, logger):
    """Handle elements that are intercepting textbox clicks"""
    try:
        # Get textbox position
        textbox_rect = driver.execute_script("""
            var rect = arguments[0].getBoundingClientRect();
            return {
                x: rect.left + rect.width/2,
                y: rect.top + rect.height/2
            };
        """, textbox)
        
        # Find what's at that position
        intercepting = driver.execute_script("""
            return document.elementFromPoint(arguments[0], arguments[1]);
        """, textbox_rect['x'], textbox_rect['y'])
        
        if intercepting and intercepting != textbox:
            # Try to move or dismiss the intercepting element
            intercepting_tag = intercepting.tag_name.lower()
            intercepting_class = intercepting.get_attribute('class') or ''
            
            logger.info(f"Found intercepting element: {intercepting_tag} with class: {intercepting_class}")
            
            # Common Twitter elements that can be safely hidden
            if any(cls in intercepting_class for cls in ['r-1loqt21', 'r-1oszu61', 'r-1777fci']):
                driver.execute_script("arguments[0].style.display = 'none';", intercepting)
                logger.info("Hid intercepting Twitter UI element")
            
    except Exception as e:
        logger.debug(f"Could not handle intercepting elements: {e}")

def _verify_textbox_focus(driver, textbox):
    """Verify that the textbox is actually focused after clicking"""
    try:
        active_element = driver.switch_to.active_element
        return active_element == textbox
    except Exception:
        return False

def enhanced_textbox_interaction(driver, selector, text_to_type, logger, max_retries=3):
    """Enhanced textbox interaction that handles finding, clicking, and typing"""
    
    for attempt in range(max_retries):
        try:
            # Find the textbox
            textbox = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            # Click the textbox
            if safe_textbox_click(driver, textbox, logger):
                # Clear any existing text
                textbox.clear()
                time.sleep(0.3)
                
                # Type the text
                textbox.send_keys(text_to_type)
                logger.info(f"Successfully typed text into textbox on attempt {attempt + 1}")
                return True
                
        except TimeoutException:
            logger.warning(f"Could not find textbox with selector {selector} on attempt {attempt + 1}")
        except Exception as e:
            logger.warning(f"Error interacting with textbox on attempt {attempt + 1}: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(2)
    
    logger.error(f"Failed to interact with textbox after {max_retries} attempts")
    return False 