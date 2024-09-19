# Whisper 기반 자막 추출 시스템

이 프로젝트는 AWS 서비스를 활용하여 사용자가 업로드한 영상 또는 음성 파일에서 자동으로 자막을 추출하는 시스템을 구현합니다. OpenAI의 Whisper 오픈소스 라이브러리를 사용하여 고품질의 음성 인식 및 자막 생성을 수행합니다.

## 주요 기능

- Whisper 모델을 배치형태로 병렬 실행
- 사용자 영상/음성 파일 업로드
- Whisper 라이브러리를 이용한 자동 자막 추출
- 추출된 자막 다운로드 및 확인

## 사용된 AWS 서비스

- AWS Batch: Whisper 모델 실행을 위한 컴퓨팅 리소스 관리
- AWS Step Functions: 자막 추출 워크플로우 조정
- AWS Lambda: 이벤트 처리 및 상태 업데이트
- Amazon DynamoDB: 작업 상태 및 메타데이터 저장
- Amazon API Gateway: RESTful API 엔드포인트 제공
- Amazon S3: 파일 저장 및 관리
- Amazon ECR: Docker 이미지 저장

## 프로젝트 구조

```
├── cf_templates
│   ├── 00_VideoProcessingInfrastructureWithVPCAndDynamoDB.yaml
│   ├── 01_VideoProcessingBatch.yaml
│   ├── 02_VideoProcessingStepFunctions.yaml
│   └── 03_VideoProcessingAPI.yaml
├── docker_images
│   ├── Dockerfile
│   ├── process_audio.py
│   └── requirements.txt
├── frontend
│   ├── app.py
│   ├── static
│   │   ├── script.js
│   │   └── styles.css
│   └── templates
│       └── upload.html
└── lambda_code
    ├── ProcessVideoFunction
    │   ├── function.zip
    │   └── lambda_function.py
    └── UpdateJobStatusFunction
        ├── function.zip
        └── lambda_function.py
```

## 설정 및 배포 과정

### 1. 기본 인프라 구축

00_VideoProcessingInfrastructureWithVPCAndDynamoDB.yaml 템플릿을 실행하여 VPC, Subnet, DynamoDB 테이블을 생성합니다.

### 2. Docker 이미지 빌드 및 업로드

ECR 저장소를 생성하고 Whisper 모델이 포함된 Docker 이미지를 빌드하여 업로드합니다:

```bash
aws ecr create-repository --repository-name whisper-processor --region us-east-1 

aws ecr get-login-password --region us-east-1  | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

cd docker_images
docker build -t whisper-processor .
docker tag whisper-processor:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/whisper-processor:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/whisper-processor:latest
```

### 3. AWS Batch 설정

01_VideoProcessingBatch.yaml 템플릿을 실행하여 AWS Batch를 구성합니다:


### 4. Step Functions 생성

02 템플릿을 실행하여 Step Functions를 생성합니다:


### 5. S3 버킷 생성

```bash
aws s3 mb s3://your_bucket/ --region us-east-1 
```

### 6. Lambda 함수 코드 업로드

Lambda 함수 코드를 S3에 업로드합니다:

```bash
cd lambda_code/ProcessVideoFunction 
zip function.zip lambda_function.py
aws s3 cp function.zip s3://your_bucket/processVideo/function.zip  --region us-east-1

cd lambda_code/UpdateJobStatusFunction 
zip function.zip lambda_function.py
aws s3 cp function.zip s3://your_bucket/updateJobStatus/function.zip  --region us-east-1
```

### 7. API Gateway 및 Lambda 함수 생성

03_VideoProcessingAPI.yaml 템플릿을 실행하여 API Gateway와 Lambda 함수를 생성합니다:


### 8. 웹 애플리케이션 설정

`frontend/app.py` 파일에서 다음 설정을 수정합니다:

```python
S3_BUCKET = 'your_bucket'
DYNAMODB_TABLE = 'your_table'
AWS_REGION = 'us-east-1'
PROFILE_NAME = 'your_profile'
API_URL = 'https://g4jg40.execute-api.us-east-1.amazonaws.com/prod/process'
```

## 사용 방법

1. 웹 애플리케이션을 실행합니다: `python frontend/app.py`
2. 브라우저에서 제공된 URL로 접속합니다.
3. 영상 또는 음성 파일을 업로드합니다.
4. 처리가 완료되면 S3에서 자막 파일을 다운로드할 수 있습니다.

## 주의사항

- 모든 AWS 리소스는 사용자가 지정한 리전에 생성됩니다.
- AWS CLI 프로필을 사용하여 명령을 실행합니다.
- 각 단계를 순서대로 진행하며, 이전 단계의 출력값을 다음 단계의 입력으로 사용합니다.
- Whisper 모델의 성능은 입력 오디오의 품질과 언어에 따라 달라질 수 있습니다.

## 기여 방법

프로젝트에 기여하고 싶으시다면 다음 단계를 따라주세요:

1. 이 저장소를 포크합니다.
2. 새 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`).
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`).
4. 브랜치에 푸시합니다 (`git push origin feature/AmazingFeature`).
5. Pull Request를 생성합니다.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.