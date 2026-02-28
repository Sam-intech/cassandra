#!/usr/bin/env python3
"""List Mistral foundation models available in AWS Bedrock."""
from dotenv import load_dotenv

load_dotenv()

import boto3

client = boto3.client("bedrock", region_name="us-east-1")
models = client.list_foundation_models(byProvider="Mistral")

for m in models["modelSummaries"]:
    print(m["modelId"])
