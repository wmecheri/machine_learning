import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

url = "https://www.drtusz.com/sitemap_wklady.php"

# List of user agents
user_agents = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188"
]

# Create a session for persistence
session = requests.Session()

api_url="http://api.scraperapi.com?api_key=f160deccd2e0e2e44a8d453730fb8075&url="

try:
    # Rotate user agents for each request
    headers = {'User-Agent': user_agents[0]}

    response = session.get(url, headers=headers)
    response.raise_for_status()  # Check for errors in the response

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all the <a> tags within the specified <td> elements
    all_tables = soup.find_all('table')

    if len(all_tables) > 1:
        # Select the second table
        second_table = all_tables[1]

        # Find all the <a> tags within the specified <td> elements in the second table
        all_links = second_table.select('tr.infoBoxContents td a')

        # Create an empty DataFrame to store the extracted information
        columns = ['URL', 'Name', 'Image URL', 'Product Name', 'Compatibilities', 'Category', 'Type', 'Class',
                   'Color', 'Compatible with', 'Catalog Number', 'Yield', 'Description', 'Model', 'Serie']
        df = pd.DataFrame(columns=columns)
        data_list = []

        iter = 0
        user =0

        # Extract and print the URLs and names
        print("Number of Products=", len(all_links))
        for link in all_links:
            link_url = link['href']
            link_name = link.text

            iter += 1
            user += 1
            print("iter=",iter)
            # Check if link_name is "continue shopping" and break out of the loop if true
            if iter <= 0 :
                continue
            if link_name.lower() == "continue shopping" or iter > 1708 :
                print("Reached 'continue shopping', stopping the loop.")
                break

            print(f"URL: {link_url}\nName: {link_name}")
            # Follow the link and scrape additional information
            try:
                # Rotate user agents for each request
                headers = {'User-Agent': user_agents[user % len(user_agents)]}

                product_response = session.get(api_url + link_url, headers=headers)
                #product_response = session.get(link_url, headers=headers)
                product_response.raise_for_status()

                product_soup = BeautifulSoup(product_response.text, 'html.parser')

                # Replace the following lines with your actual scraping logic
                product_name = product_soup.select_one('table.pageHeading td.pageHeading h1').text.strip()
                print(product_name)
                # Find the div with id 'duze_photo'
                duze_photo_div = product_soup.find('div', id='duze_photo')

                # Check if the div is found
                if duze_photo_div:
                    # Find the img tag within 'duze_photo'
                    img_tag = duze_photo_div.find('img', recursive=False)

                    # Check if the img tag is found
                    if img_tag:
                        # Construct the complete image URL by adding the base URL
                        product_image_url = f"https://www.drtusz.com/{img_tag['src']}"

                        # Print the extracted image URL
#                         print(f"Image URL: {product_image_url}")
                    else:
                        print("Image tag not found within 'duze_photo'.")
                else:
                    print("'duze_photo' div not found.")


                if product_soup.find('h3', string='Compatible with: ') != None :
                    compatibilities_table = product_soup.find('h3', string='Compatible with: ').find_next('table')
                    compatibilities_rows = compatibilities_table.find_all('td')[1::2]  # Select every second <td> starting from index 1
    
                    compatibility_list = [a.text for a in compatibilities_rows]
                else:
                    print("Issue with compatibility")
                    continue
                
               # Extracting information from the first newlisting_dane class
                newlisting_dane = product_soup.find('div', class_='newlisting_dane')

                if newlisting_dane:
                    # Extracting information
                    td_elements = newlisting_dane.find_all('td', class_='ProductHead')
                    data_dict = {}
                    current_key = None

                    for element in td_elements:
                        if element.text.strip() in ['Category', 'Type', 'Class', 'Color', 'Compatible with', 'Catalog Number', 'Yield', 'Cost per page']:
                            current_key = element.text.strip()
                        elif current_key:
                            value_element = element.find('b')
                            value = value_element.text.strip() if value_element else element.text.strip()
                            data_dict[current_key] = value
                            current_key = None
                    # Description, Model, and Serie handling
                    compatibilities_list = [a.text for a in compatibilities_rows]
                   # Create Description, Model, and Serie values
                    description = " - ".join(compatibilities_list)

                    # Add extracted information to the DataFrame
                    for i, compatibility in enumerate(compatibilities_list):
                        model = ''
                        serie = ''
                        if compatibility:
                            # The last element is the model
                            model = compatibility[-1]

                            # The rest are elements of the serie
                            serie_list = compatibility[:-1]

                            # Join the elements of the serie with a space
                            serie = ' '.join(serie_list)
                        else:
                            model = ''
                            serie = ''
                        row_data = {
                            'URL': link_url if i == 0 else '',
                            'Name': link_name if i == 0 else '',
                            'Image URL': product_image_url if i == 0 else '',
                            'Product Name': product_name if i == 0 else '',
                            'Compatibility': compatibility,
                            'Category': data_dict.get('Category', '') if i == 0 else '',
                            'Type': data_dict.get('Type', '') if i == 0 else '',
                            'Class': data_dict.get('Class', '') if i == 0 else '',
                            'Color': data_dict.get('Color', '') if i == 0 else '',
                            'Compatible with': data_dict.get('Compatible with', '') if i == 0 else '' ,
                            'Catalog Number': data_dict.get('Catalog Number', '') if i == 0 else '',
                            'Yield': data_dict.get('Yield', '') if i == 0 else '',
                            'Description': description if i == 0 else '',
                            'Model': model,
                            'Serie': serie
                        }
                        data_list.append(row_data)
                    
                else:
                    print("No information found in the newlisting_dane class.")

            except requests.exceptions.RequestException as e:
                print(f"Error during request: {e}")
                break  # Break the loop if an error occurs

            print("\n")
            # Introduce a delay between requests for politeness
            time.sleep(2)

    else:
        print("There are not enough tables in the HTML.")

    # Introduce a delay between requests
    time.sleep(2)

except requests.exceptions.RequestException as e:
    print(f"Error during request: {e}")

# Create a DataFrame from the list
df = pd.DataFrame(data_list)
# Save the DataFrame to a CSV file
df.to_csv('drtusz_4.csv', index=False)
print("file saved!")
# Close the session
session.close()