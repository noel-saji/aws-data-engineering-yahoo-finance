import requests
import boto3
import json
import os
import time
from datetime import datetime
from botocore.exceptions import BotoCoreError, NoCredentialsError, ClientError
import logging

# Configure logging to show INFO and above
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("****Raw Data Retrivel Operations Started****")

def debug_credentials():
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials:
            logging.info("AWS Credentials Found")
            logging.info(f"Access Key: {credentials.access_key}")
        else:
            logging.info("No AWS Credentials Found")
    except Exception as e:
        logging.error(f"Error Debuging Credentials: {e}")

debug_credentials()

def fetch_secret(secret_name):
    try:
        client = boto3.client('secretsmanager', region_name=region)
        response = client.get_secret_value(SecretId=secret_name)

        return json.loads(response['SecretString'])

    except ClientError as e:
        logging.error(f"Error Fetching Secret: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error fetching secret: {e}")
        raise

def write_to_s3(bucket_name, data, key_prefix):
    try:
        s3 = boto3.client('s3')
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M-%S")
        key = f"{key_prefix}/stock_data_{timestamp}.json"

        s3.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(data, indent=2))
        logging.info(f"✅ Data Sucessfuly written to S3: {bucket_name}/{key}")

    except BotoCoreError as e:
        logging.error(f"Error writing to S3: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error writing to S3 bucket {bucket_name}: {e}")
        raise

def fetch_stock_details(symbols, api_key, retries=3):
    url = f"https://yfapi.net/v6/finance/quote?region=US&lang=en&symbols={','.join(symbols)}"
    logging.info(f'URL = {url}')
    headers = {"X-API-KEY": api_key}

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 429:
                logging.info(f"Rate limit hit. Retrying in {2 ** attempt} seconds...")
                time.sleep(2**attempt)
                continue
            logging.info(f"Respsone: {response.json}")
            return response.json()
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error: {e}")
            if attempt == retries - 1:
                raise
        except Exception as e:
            logging.error(f"Error fetching stock data: {e}")
            if attempt == retries - 1:
                raise

if __name__ == "__main__":
    # Get configuration from environment variables with defaults
    region = os.getenv("AWS_REGION", "ap-south-1") # Defaults to ap-south-1
    secret_name = os.getenv("SECRET_NAME", "YH_Finance_Api")
    bucket_name = os.getenv("S3_BUCKET", "BUCKET_NAME") #Enter your Bucket name here
    symbols = os.getenv("STOCK_SYMBOLS", "AAPL,MSFT,GOOGL").split()

    try:
        # Retrieve API key from AWS Secrets Manager
        secrets = fetch_secret(secret_name)
        api_key = secrets['yh_finance_api_key']

        # Fetch stock data for the specified symbols
        stock_data = fetch_stock_details(symbols, api_key)

        # Upload the fetched data to the S3 bucket
        write_to_s3(bucket_name, stock_data, "raw")
        
    except Exception as e:
        logging.error(f"An error occurred in the main execution: {e}")