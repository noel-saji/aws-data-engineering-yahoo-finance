import boto3
import json
import os
from datetime import datetime
import logging

# Configure logging to show INFO and above
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("****Transform Operations Started****")

def read_from_s3(bucket_name, prefix):
    """
    Read the latest file from the given S3 bucket and prefix.
    """
    s3 = boto3.client("s3")
    logging.info(f"Bucket name for reading raw Data:{bucket_name}")
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

    if "Contents" not in response:
        raise FileNotFoundError(f"No files found in bucket {bucket_name} with prefix {prefix}")

    # Get the latest file
    files = sorted(response["Contents"], key=lambda x: x["LastModified"], reverse=True)
    latest_file = files[0]["Key"]

    logging.info(f"Reading data from: {bucket_name}/{latest_file}")
    file_obj = s3.get_object(Bucket=bucket_name, Key=latest_file)
    
    return json.loads(file_obj["Body"].read().decode("utf-8"))

def transform_data(data):
    """
    Perform the necessary transformations on the stock data.
    """
    transformed_data = []
    for stock in data["quoteResponse"]["result"]:
        transformed_stock = {
            "company_id": stock.get("symbol"),
            "company_name": stock.get("longName"),
            "currency": stock.get("currency"),
            "current_price": stock.get("regularMarketPrice"),
            "day_low": stock.get("regularMarketDayLow"),
            "day_high": stock.get("regularMarketDayHigh"),
        }
        transformed_data.append(transformed_stock)

    logging.info(f"Transformed {len(transformed_data)} records.")
    return transformed_data

def write_to_s3(bucket_name, data, key_prefix):
    """
    Write transformed data to S3 in: prefix/month/day/filename format.
    """
    s3 = boto3.client("s3")
    
    # Get current time for folder structure
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m") # e.g., '03'
    day = now.strftime("%d")   # e.g., '20'
    full_timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    
    # Construct the dynamic key
    # Result: transformed/03/20/transformed_stock_data_2026-03-20_13-40-00.json
    key = f"{key_prefix}/{year}/{month}/{day}/transformed_stock_data_{full_timestamp}.json"
    
    s3.put_object(
        Bucket=bucket_name, 
        Key=key, 
        Body=json.dumps(data, indent=2)
    )
    logging.info(f"✅ Transformed data written to S3: {bucket_name}/{key}")

if __name__ == "__main__":
    # Environment variables
    raw_bucket = os.getenv("S3_BUCKET", "BUCKET_NAME") # Raw data S3 bucket
    transformed_bucket = os.getenv("S3_BUCKET", "BUCKET_NAME") # Transformed data S3 bucket
    raw_prefix = os.getenv("RAW_PREFIX", "raw/") # Prefix for raw data in S3
    transformed_prefix = os.getenv("TRANSFORMED_PREFIX", "transformed") # Prefix for transformed data in S3

try:
    # Step 1: Read raw data from S3
    logging.info("Reading raw data from S3...")
    raw_data = read_from_s3(raw_bucket, raw_prefix)

    # Step 2: Transform the data
    logging.info("Transforming data...")
    transformed_data = transform_data(raw_data)

    # Step 3: Write transformed data to S3
    logging.info("Writing transformed data to S3...")
    write_to_s3(transformed_bucket, transformed_data, transformed_prefix)

    logging.info("Data transformation completed successfully.")

except Exception as e:
    logging.error(f"An error occurred: {e}")
    raise
