from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import  TimeoutException
import time

def get_driver():
    # Use an absolute path to the Firefox executable
    firefox_binary_path = '/usr/bin/firefox' 
    # Adjust this path if your geckodriver binary is not in the same folder as the scirpt
    geckodriver_path = ''  
    
    options = webdriver.FirefoxOptions()
    # Uncomment the next line if you want Firefox to run headlessly doesnt work on wsl
    options.add_argument('-headless')
    options.binary_location = firefox_binary_path
    options.set_preference("dom.disable_beforeunload", True)
    options.set_preference("geo.prompt.testing", False)
    options.set_preference("geo.prompt.testing.allow", False)   
    
    return webdriver.Firefox(options=options)

def states(driver):
    print("Navigating to the Best Buy store directory...")
    driver.get("https://stores.bestbuy.com/")
    print("Collecting state links...")
    state_links = WebDriverWait(driver, 60).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 
                                             "ul.c-directory-list-content li a"))
    )
    state_urls = [link.get_attribute('href') for link in state_links]
    state_nums = WebDriverWait(driver, 60).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 
                                             "ul.c-directory-list-content li span"))
    )
    state_num = [int((link.text).strip('()')) for link in state_nums]
    state_urls.pop(1)
    state_num.pop(1) #Alaska isnt formatted right
    return state_urls, state_num

def cities(driver, state, num):
    print(f"Visiting state page: {state}")
    driver.get(state)
        # Collect all store links on the state page
    print("Collecting city links within the state...")
    try:
        city_links = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 
                                                        "ul.c-directory-list-content li a"))
            )

        city_nums = WebDriverWait(driver, 1).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 
                                                    "ul.c-directory-list-content li span"))
        )
    except TimeoutException:
        return stores(driver, state, num)
    city_urls = [link.get_attribute('href') for link in city_links]
    city_num = [int((link.text).strip('()')) for link in city_nums]

    return city_urls, city_num

def stores(driver, city, num):
           
    print(f"Visiting city page: {city}")
    driver.get(city)
    print("Collecting store links within the city...")

    store_links = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 
                                                "ul.c-LocationGridList li article header h2 a"))
    )
    store_nums = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 
                                                "div.Directory-subtitle.Text--bold > span"))
    )
    
    store_urls = [link.get_attribute('href') for link in store_links]
    store_num =  int((store_nums[0].text).strip('()')) 
    return store_urls, store_num

num = 0 # for diagnostics 
def record(driver, name="diag"):
    if name == "diag":
        name += str(num)
        num += 1
    print(driver.current_url)
    print(name)
    page_source = driver.page_source
    with open(name+".html", "w", encoding="utf-8") as file:
        file.write(page_source)
    
def search_query(driver, site, query, sku):
    driver.get(site)
    # Locate the search input field by its class name and send the search term 'test'
    search_input = driver.find_element(By.CLASS_NAME, "Header-searchInput")
    search_input.clear()  # Clear any pre-filled text in the input field
    search_input.send_keys(query)

    # Locate the submit button by its class name and click it to submit the form
    search_button = driver.find_element(By.CLASS_NAME, "Header-searchButton")
    search_button.click()
   
    search_results = driver.find_elements(By.CLASS_NAME, "sku-item")

    try:
        # Wait for the element with a timeout of 60 seconds
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".country-selection"))
        )
        usa_link = driver.find_element(By.CSS_SELECTOR, "a.us-link")
        usa_link.click()
    except TimeoutException:
        pass  
    specific_sku_item = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f'[data-sku-id="{sku}"]'))
    )

    time.sleep(2)    
    while True:
        try:
            time.sleep(1)
            open_box = WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a.open-box-option__button')))
            # Click the element
            open_box.click()
            print("Successfully clicked on the 'Open Box' button.")
            break
        except TimeoutError:
            print("Had to wait too long")
            return -1     
    time.sleep(2)
    """sidebar = WebDriverWait(driver, 60).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.fulfillment-add-to-cart-button"))  
            )
    if "ADD_TO_CART" in driver.page_source:
        return 1
    return -1"""
    """try:
        button = driver.find_element(By.XPATH, "//button[contains(@class, 'add-to-cart-button')]")

        # Check if the button is disabled and contains the text "Unavailable Nearby"
        if button.get_attribute("disabled") and button.text == "Unavailable Nearby":
            print("The button is disabled and contains the text 'Unavailable Nearby'")
            return 1
        else:
            print("The button is either enabled or does not contain the text 'Unavailable Nearby'")
            return -1

    except Exception as e:
        print("Error:", e)"""
    


    sidebar = WebDriverWait(driver, 60).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.fulfillment-add-to-cart-button"))  
            )
    if "Unavailable" in driver.page_source:
        return -1
    return 1

def main():
    fast = True
    driver = get_driver()
    query = "zenbook pro 14\"" 
    sku = "6552809"
    max_per_city = 1
    max_per_state = 3
    

    state_urls, state_num = states(driver)
    if (len(state_urls) != len(state_num)):
        print("Mismatch in number of states and counts")
        return -2
    
    print(f"Found {len(state_urls)} states to check.")
    
    for i in range(20, 51):
        state_url = state_urls[i]
        if state_num[i] == 1:
            print(state_url)
            ret = search_query(driver, state_url, query, sku)
            if ret > 0:
                print("found:", driver.current_url)
                driver.quit()
                #return 0
                
            time.sleep(2)
            continue  # Delay to avoid rapid page loading that might seem suspicious
        city_urls, city_nums = cities(driver, state_url, state_num[i])
        if (len(city_urls) != len(city_nums)):
            print("Mismatch in number of states and counts")
            driver.quit()
            return -2
        
        print(f"Found {len(city_urls)} cities to check in this state.")
        for j, city_url in enumerate(city_urls):
            if j >= max_per_state:
                break 

            print(city_url, city_nums[j])
            if city_nums[j] == 1:
                print(state_url, city_url)
                ret = search_query(driver, city_url, query, sku)
                if ret > 0:
                    print("found:", driver.current_url)
                    driver.quit()
                    #return 0
                    
                continue

               
            
            store_urls, store_num = stores(driver, city_url, city_nums[j])
            if len(store_urls) != store_num:
                print("len error")
                driver.quit()
                return -2
            
            print(f"Found {len(store_urls)} stores to check in this city.")
            if fast:
                ret = search_query(driver, store_urls[0], query,
                                   sku)
                if ret > 0:
                    print("found:", driver.current_url)
            else:
                for k, store_url in enumerate(store_urls):
                    if k >= max_per_city:
                        break
                    print(state_url, city_url, store_url)
                    ret = search_query(driver, store_url, query, sku)
                    if ret > 0:
                        print("found:", driver.current_url)
                        driver.quit()
                        #return 0
                        

    driver.quit()
    print("Completed checking all stores in all states.")
    return 1

if __name__ == "__main__":
    main()
