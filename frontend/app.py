import os
import boto3
import json
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import requests
import urllib.parse
from datetime import datetime, timedelta


app = Flask(__name__)

# AWS 설정
S3_BUCKET = 'video-processing-west-1-nb'
DYNAMODB_TABLE = 'StepFunctionsStateTable'
AWS_REGION = 'us-west-1'
PROFILE_NAME = 'subdomain'
API_URL = 'https://gbbt787v7g.execute-api.us-west-1.amazonaws.com/prod/process'

session = boto3.Session(profile_name=PROFILE_NAME, region_name=AWS_REGION)
s3 = session.client('s3')
dynamodb = session.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)


ALLOWED_EXTENSIONS = {'mp4', 'mp3'}

def secure_filename_with_korean(filename):
    return urllib.parse.quote(filename)

def format_date_to_utc_plus_9(date_string):
    if not date_string:
        return 'N/A'
    
    try:
        date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        utc_plus_9 = date + timedelta(hours=9)
        formatted_date = utc_plus_9.strftime('%Y-%m-%d %H:%M:%S')
        return formatted_date
    except ValueError:
        return date_string  # 파싱할 수 없는 경우 원래 문자열 반환

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/static/<path:filename>')
def send_js(filename):
    return send_from_directory('static', filename)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('file')
        print(f"Received {len(files)} files for upload")  # 디버깅: 업로드된 파일 수 출력
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename_with_korean(file.filename)
                file_content = file.read()
                
                print(f"Uploading file: {filename}")  # 디버깅: 업로드 중인 파일 이름 출력
                
                # S3에 파일 업로드
                try:
                    s3.put_object(Bucket=S3_BUCKET, Key=filename, Body=file_content)
                    print(f"Successfully uploaded {filename} to S3")  # 디버깅: S3 업로드 성공 메시지
                except Exception as e:
                    print(f"Error uploading {filename} to S3: {str(e)}")  # 디버깅: S3 업로드 실패 메시지
                    continue
                
                # API 호출
                api_url = API_URL
                payload = {
                    "s3_address": f"s3://{S3_BUCKET}/{filename}",
                    "output_bucket": S3_BUCKET
                }
                headers = {'Content-Type': 'application/json'}
                
                print(f"Calling API for {filename}")  # 디버깅: API 호출 시작 메시지
                try:
                    response = requests.post(api_url, json=payload, headers=headers)
                    if response.status_code == 200:
                        print(f"API call successful for {filename}")  # 디버깅: API 호출 성공 메시지
                    else:
                        print(f"API call failed for {filename}. Status code: {response.status_code}")  # 디버깅: API 호출 실패 메시지
                except Exception as e:
                    print(f"Error calling API for {filename}: {str(e)}")  # 디버깅: API 호출 예외 메시지
        
        return jsonify({"message": "Files uploaded successfully"}), 200

    return render_template('upload.html')

@app.route('/get_items', methods=['GET'])
def get_items():
    
    # DynamoDB에서 데이터 가져오기
    print("Fetching data from DynamoDB")  # 디버깅: DynamoDB 데이터 가져오기 시작 메시지
    try:
        response = table.scan()
        items = response['Items']
        print(f"Retrieved {len(items)} items from DynamoDB")  # 디버깅: 가져온 아이템 수 출력
    except Exception as e:
        print(f"Error fetching data from DynamoDB: {str(e)}")  # 디버깅: DynamoDB 데이터 가져오기 실패 메시지
        items = []
        
    for item in items:
        item['CreatedAt'] = format_date_to_utc_plus_9(item['CreatedAt'])
        if 'CompletedAt' in item:
            item['CompletedAt'] = format_date_to_utc_plus_9(item['CompletedAt'])

    # UpdatedAt 필드 제외
    items_excluded_updatedat = [
        {key: item[key] for key in item if key != 'UpdatedAt'}
        for item in items
    ]

    return jsonify(items_excluded_updatedat)

if __name__ == '__main__':
    app.run(debug=True)