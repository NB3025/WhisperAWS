import json
import os
import sys
import boto3
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from botocore.exceptions import ClientError
from moviepy.editor import VideoFileClip

s3_client = boto3.client('s3')
AUDIO_EXTENSIONS = ['.wav', '.mp3', '.flac', '.aac']
model_id = "openai/whisper-large-v3"

def download_from_s3(s3_address: str, local_path: str) -> None:
    bucket, key = s3_address.replace("s3://", "").split("/", 1)
    try:
        print(f"Attempting to download {key} from bucket {bucket}")
        s3_client.download_file(bucket, key, local_path)
        print(f"Successfully downloaded {key} to {local_path}")
    except ClientError as e:
        print(f"An error occurred: {e}")
        raise

def upload_to_s3(local_path: str, bucket: str, key: str) -> None:
    s3_client.upload_file(local_path, bucket, key)

def extract_audio(video_path: str, audio_path: str) -> None:
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(audio_path)
        print(f"Audio extracted from {video_path} to {audio_path}")
    except Exception as e:
        print(f"Error extracting audio: {e}")
        raise

def time_to_srt_format(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

def create_srt_content(chunks: list) -> str:
    srt_lines = []
    for i, chunk in enumerate(chunks, start=1):
        start_time = time_to_srt_format(chunk['timestamp'][0])
        end_time = time_to_srt_format(chunk['timestamp'][1])
        srt_lines.append(f"{i}\n{start_time} --> {end_time}\n{chunk['text']}\n")
    return "\n".join(srt_lines)

def process_audio(input_audio_file: str, language: str = "korean") -> tuple[bool, str, list, str]:
    try:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
        )
        model.to(device)
        
        processor = AutoProcessor.from_pretrained(model_id)
        
        pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=16,
            return_timestamps=True,
            torch_dtype=torch_dtype,
            device=device
        )

        if not any(input_audio_file.lower().endswith(ext) for ext in AUDIO_EXTENSIONS):
            print(f"{input_audio_file} is not an audio file. Extracting audio...")
            audio_file = 'extracted_audio.wav'
            extract_audio(input_audio_file, audio_file)
            input_audio_file = audio_file

        print(f'Processing audio file: {input_audio_file}')
        result = pipe(input_audio_file, generate_kwargs={"language": language})
        transcription_segments = result["chunks"]
        srt_content = create_srt_content(transcription_segments)
        
        return True, "Transcription completed successfully", transcription_segments, srt_content
    except Exception as e:
        print(f"Error in process_audio: {str(e)}")
        return False, str(e), [], ""

if __name__ == "__main__":
    s3_address = sys.argv[1]
    output_bucket = sys.argv[2]
    job_id = sys.argv[3]

    output_bucket = output_bucket.replace("s3://", "")

    local_input_video_file = 'input_video.mp4'
    local_output_file = f'output_transcript_{job_id}'

    try:
        download_from_s3(s3_address, local_input_video_file)
        success, message, transcription_segments, srt_content = process_audio(local_input_video_file)

        if success:
            with open(f"{local_output_file}.srt", 'w', encoding='utf-8') as f:
                f.write(srt_content)

            # Upload SRT file to S3
            output_key = f"transcripts/{job_id}.srt"
            upload_to_s3(f"{local_output_file}.srt", output_bucket, output_key)

            result = {
                "status": "SUCCEEDED",
                "inputFile": s3_address,
                "outputBucket": output_bucket,
                "outputKey": output_key,
                "jobId": job_id  # 결과에 job_id 추가
            }
        else:
            result = {
                "status": "FAILED",
                "error": message,
                "jobId": job_id  # 실패 결과에도 job_id 추가
            }
    except Exception as e:
        result = {
            "status": "FAILED",
            "error": str(e),
            "jobId": job_id  # 예외 결과에도 job_id 추가
        }
    finally:
        # Clean up temporary files
        for file in ['extracted_audio.wav', local_input_video_file, f"{local_output_file}.srt"]:
            if os.path.exists(file):
                os.remove(file)

    print(json.dumps(result))
    sys.exit(0 if result["status"] == "SUCCEEDED" else 1)