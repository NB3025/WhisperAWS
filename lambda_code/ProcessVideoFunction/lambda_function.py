import json
import boto3
import os
import uuid
from datetime import datetime

def lambda_handler(event, context):
    try:
        # API Gateway에서 전달받은 body에서 S3 주소 추출
        body = json.loads(event['body'])
        s3_address = body['s3_address']
        output_bucket = body['output_bucket']
        
        s3_prefix = s3_address.rsplit('/', 1)[0]
        print (f'{s3_prefix=}')
        
        # 작업 식별자 생성
        job_id = str(uuid.uuid4())
        
        # Step Functions ARN은 환경 변수로 설정
        step_functions_arn = os.environ['STEP_FUNCTIONS_ARN']
        
        # DynamoDB 테이블 이름은 환경 변수로 설정
        dynamodb_table_name = os.environ['DYNAMODB_TABLE_NAME']
        
        # DynamoDB 클라이언트 생성
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(dynamodb_table_name)
        
        # 현재 시간 가져오기
        current_time = datetime.utcnow().isoformat()
        
        # DynamoDB에 작업 정보 저장
        table.put_item(
            Item={
                'JobId': job_id,
                'CreatedAt': current_time,
                'Status': 'STARTED',
                'S3Address': s3_address,
                'Output': f'{s3_prefix}/{job_id}.srt',
                'UpdatedAt': current_time
            }
        )
        
        # Step Functions 클라이언트 생성
        sfn_client = boto3.client('stepfunctions')
        
        # Step Functions 실행
        response = sfn_client.start_execution(
            stateMachineArn=step_functions_arn,
            input=json.dumps({
                'job_id': job_id,
                's3_address': s3_address,
                'output_bucket': output_bucket
            })
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Step Functions execution started',
                'jobId': job_id,
                'executionArn': response['executionArn']
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error processing request',
                'error': str(e)
            })
        }