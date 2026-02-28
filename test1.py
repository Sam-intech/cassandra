from dotenv import load_dotenv

import boto3
import json


load_dotenv()

client = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

response = client.invoke_model(
    modelId='mistral.mistral-large-2402-v1:0',
    body=json.dumps({
        "prompt": "<s>[INST] You are CASSANDRA, an AI system that detects informed trading in crypto markets. Introduce yourself in 2 sentences. [/INST]",
        "max_tokens": 100,
        "temperature": 0.3
    })
)

result = json.loads(response['body'].read())
print(result['outputs'][0]['text'])