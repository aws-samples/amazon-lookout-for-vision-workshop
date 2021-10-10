"""
MIT License

Copyright (c) 2021 Jisoo Min

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


# Import all the libraries needed to get started:
from lookoutvision.image import Image
from lookoutvision.manifest import Manifest
from lookoutvision.metrics import Metrics
from lookoutvision.lookoutvision import LookoutForVision

import glob
import logging
import boto3
from botocore.exceptions import ClientError
import datetime
import random
import csv
import re
import os
import sys
from time import sleep

session = boto3.Session(region_name='us-east-1')
s3 = session.client('s3')

# Threshold of Confidence
confidence_threshold = 0.7

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name
        
    # Upload the file
    try:
        response = s3.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True
    
def save_result(s3_bucket_name, product_id, is_anomaly, reinspection_needed):
    output_filename = str(product_id) + ".csv"
    

    with open('/tmp/' + output_filename, 'w', newline='') as csvfile:
        
        fieldnames = ['ProductId', 'IsAnomaly', 'ReinspectionNeeded', 'CapturedDate']
        csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        now = datetime.datetime.now()
  
        csvwriter.writeheader()
        csvwriter.writerow({'ProductId': product_id, \
                            'IsAnomaly': is_anomaly, \
                            'ReinspectionNeeded': reinspection_needed, \
                            'CapturedDate'      : now})

    
    with open("/tmp/" + output_filename, "rb") as f:
        s3.upload_fileobj(f, s3_bucket_name, 'result/' + output_filename)

def main(argv):
    
    s3_bucket_name = argv[1] # s3 bucket name

    image_list = glob.glob("images/*")
    #random.shuffle(image_list)
    
    l4v = LookoutForVision(project_name="lookout-for-vision-workshop")
    
   
    for image_path in image_list:
        
        prediction = l4v.predict(local_file=image_path)
        print(prediction)
        
        filename = os.path.basename(image_path)
        product_id = int((re.findall(r'\d+', filename))[1])
        
        is_anomaly = 0
        if prediction['IsAnomalous'] == True:
            is_anomaly = 1
            
        confidence = prediction['Confidence']
        
        reinspection_needed = 0
        if confidence <= confidence_threshold:
            reinspection_needed = 1
        
        save_result(s3_bucket_name, product_id, is_anomaly, reinspection_needed)
        sleep(1)
        
        
if __name__ == "__main__":
    # execute only if run as a script
    main(sys.argv)
