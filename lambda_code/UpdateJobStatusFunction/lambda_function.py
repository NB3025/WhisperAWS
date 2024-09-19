import json
import os
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE_NAME'])

def get_job_item(job_id):
    response = table.query(
        KeyConditionExpression=Key('JobId').eq(job_id)
    )
    items = response.get('Items', [])
    if not items:
        raise Exception(f"Job with ID {job_id} not found")
    return items[0]  # Assuming JobId is unique, return the first (and should be only) item

def lambda_handler(event, context):
    print (f'{event=}')
    try:
        job_id = event['job_id']
        status = event['status']
        
        # 항목 조회
        item = get_job_item(job_id)
        created_at = item['CreatedAt']
        
        update_expression = "SET #status = :status, UpdatedAt = :updated_at"
        expression_attribute_names = {'#status': 'Status'}
        expression_attribute_values = {
            ':status': status,
            ':updated_at': datetime.utcnow().isoformat()
        }
        
        if status == 'COMPLETED':
            completed_at = event['completedAt']
            update_expression += ", CompletedAt = :completed_at"
            expression_attribute_values[':completed_at'] = completed_at
        elif status == 'FAILED':
            error = event.get('error', 'Unknown error')
            update_expression += ", ErrorMessage = :error"
            expression_attribute_values[':error'] = error
        
        response = table.update_item(
            Key={
                'JobId': job_id,
                'CreatedAt': created_at
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps('Job status updated successfully')
        }
    except Exception as e:
        print(f"Error updating job status: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error updating job status: {str(e)}')
        }