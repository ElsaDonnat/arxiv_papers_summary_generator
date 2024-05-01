#This simple script calls on the Arxiv.org API as well as the HuggingFace inference API (Bert model) 
#and summarizes recent papers in the field of Machine Learning and AI.

print("\n *** The script has STARTED... ***")
# Configure logging
import logging
import sys 

logging.basicConfig(filename='arxiv_summary_log.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

logging.info("\n\n *** The script has started *** \n")
logging.info(f"Python Executable: {sys.executable}") # if the script was run using my conda environment, 
#this line should be logged: INFO:Python Executable: C:\ProgramData\anaconda3\envs\project1_env\python.exe


import requests
import xml.etree.ElementTree as ET  
from time import sleep
import PyPDF2
import io
import json
import sys



# Function to download and extract text from PDF
def download_and_extract_pdf(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with io.BytesIO(response.content) as open_pdf_file:
                pdf = PyPDF2.PdfReader(open_pdf_file)
                text = ''
                for page in pdf.pages:
                    text += page.extract_text()
                return text
        else:
            logging.error(f"Failed to download PDF: {url}")
            return None
    except Exception as e:
        logging.exception(f"Error downloading or extracting PDF from {url}: {e}")
        return None
    
#Before writing the text to a JSON file, remove or replace characters that could cause encoding issues or are not relevant to your analysis.
def sanitize_text(text):
    # Replace or remove unwanted characters
    # This can be customized based on the type of issues you've observed
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = text.replace('- ', '')  # Remove hyphen followed by a space which indicates a word broken up over a line
    text = text.encode('utf-8', 'replace').decode('utf-8')

    return text
    
def summarize(text, max_retries=3):
    summary_retry_count = 0
    while summary_retry_count < max_retries:
        try:
            response = requests.post(bart_api_url, headers=headers, json={
                "inputs": text,
                "parameters": {"min_length": 500, "max_length": 600}  # Adjust these values as needed
            })
            if response.status_code == 200:
                # Log the raw response for debugging purposes
                logging.info(f"Raw summarization response: {response.json()}")
                # Assuming the response structure includes the summary directly
                summary_response = response.json()
                # Since the response is a list of dictionaries, access the first item
                if isinstance(summary_response, list) and len(summary_response) > 0 and "summary_text" in summary_response[0]:
                    return summary_response[0]["summary_text"]
                else:
                    logging.error("Unexpected response format or 'summary_text' key not found in response.")
                    return None
            else:
                logging.warning(f"Attempt {summary_retry_count + 1}: Failed to summarize, status code {response.status_code}")
        except Exception as e:
            logging.error(f"Error during summarization: {e}")
            return None
        summary_retry_count += 1
        sleep(5)  # Wait for a few seconds before retrying
    logging.error("Summarization failed after maximum retries.")
    return None

arxiv_api_url = "http://export.arxiv.org/api/query?"
parameters = {
    "search_query": "cat:cs.AI", # Filters for AI papers in Computer Science.
    "sortBy": "submittedDate", # Sorts by the submission date.
    "sortOrder": "descending", # Orders results from newest to oldest.
    "max_results": 2 # Limits the number of results.
}

bart_api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
headers = {"Authorization": "Bearer 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"}
# Fetching data from the API into XML format. The whole thing is wrapped in a try-except block to accomodate logging.
max_attempts = 5
attempt = 0

full_papers_data = []  # To store full papers
summaries_data = []    # To store summaries

while attempt < max_attempts:
# If the first step works, the script will continue within it according to the if/else block
    try:
        
        response = requests.get(arxiv_api_url, params=parameters)
        
        if response.status_code != 200:
            logging.error(f"Failed to fetch data from ArXiv API. Status code: {response.status_code}, Response: {response.content}")
            # Handle the error appropriately (like retrying or exiting)

        if response.status_code == 200:
            # Parse the XML response
            root = ET.fromstring(response.content)
            # Find the total number of results
            namespaces = {'open_search': 'http://a9.com/-/spec/opensearch/1.1/'}  # add more as needed. 
            #these are namespaces, the http adress is simply a unique identifier
            #it is what the arXiv API uses to define the elements that are part of the OpenSearch standard within its XML response. 
            #The root.find() method below searches for the opensearch:totalResults element, using the correct namespace.
            total_results = int(root.find('open_search:totalResults', namespaces).text)

            # Check if there are no results
            if total_results == 0:
                logging.warning(f"Attempt {attempt + 1}: The API returned 0 results. Retrying...")
                attempt += 1
                print("0 results returned by the API. Retrying in 5 seconds...")
                sleep(5)  # Wait for 5 seconds before the next attempt
                continue  # Skip the rest of the loop and try again

            logging.info("Yay! Successfully fetched the arxiv.org papers. They are now contained in an XLM formal in the \"papers\" variable.")
            
            # Here I continue the script, the first step worked and I have fetched data from API. Now I want to format it. 
            formatted_data = []
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                title = entry.find('{http://www.w3.org/2005/Atom}title').text
                abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text
                pdf_link = None #initializing the value with nothing in it so we can add the pdf papers below.
                for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
                    if link.get('type') == 'application/pdf': #This is a way to identify if the link points to a PDF document.
                        pdf_link = link.get('href')

                full_text = None
                if pdf_link:
                    full_text = download_and_extract_pdf(pdf_link)
                    if full_text:
                        sanitized_full_text = sanitize_text(full_text)
                        full_papers_data.append({"title": title, "text": sanitized_full_text})

                        summary = summarize(sanitized_full_text)
                        if summary:
                            logging.info(f"Using HuggingFace's inference API to attempt to summarize the paper titled: {title}")
                            summaries_data.append({"title": title, "summary": summary})
                        else:
                            logging.error(f"Failed to generate a summary for the paper titled: {title}")
                
            break  # Successful fetch and data formating, exit loop
            
        else:
            logging.error(f"Failure. Status code: {response.status_code}")
            attempt += 1
            sleep(5)  # Wait for a few seconds before retrying
            continue  # Continue to the next iteration of the loop
    except ET.ParseError:
        logging.exception("Failed to parse XML from arXiv response.")
        attempt += 1
        sleep(5)
        break  # Exit the loop on parsing error

    except requests.exceptions.ConnectionError as e:
        logging.exception("Network error occurred while fetching papers from arXiv.")
        attempt += 1
        sleep(30)  # Wait for 10 seconds before retrying
        continue  # Retry fetching data

    except requests.exceptions.RequestException as e:
        logging.exception(f"Request failed: {e}")
        attempt += 1
        sleep(5)

    except Exception as e:
        logging.exception("Oh no!! An error occurred during the process")
        attempt += 1
        sleep(5)
        break # Exit the loop on any other error
        
    
if attempt == max_attempts:
    logging.error(f"Reached maximum attempts ({max_attempts}) to fetch papers without success...")
    print("Sorry, fetching the papers did not work.")

# Writing the full papers to a JSON file
with open('full_papers_data.json', 'w', encoding='utf-8') as outfile:
    json.dump(full_papers_data, outfile, indent=4)
logging.info("Formated data written into full_papers_data Json file.")


# Writing the summaries to a separate JSON file
with open('summaries_data.json', 'w', encoding='utf-8') as outfile:
    json.dump(summaries_data, outfile, ensure_ascii=False, indent=4)
    #The ensure_ascii=False parameter allows the json.dump() method to output UTF-8 encoded text directly into the file, which should preserve the characters correctly.
logging.info("Summaries written into summaries_data Json file.")



logging.info("\n\n *** The script has ended *** \n ")
print("  *** The script has ENDED ***")