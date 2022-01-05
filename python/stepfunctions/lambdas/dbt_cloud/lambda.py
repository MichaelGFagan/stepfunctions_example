import json
import boto3
import requests
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

# https://awslabs.github.io/aws-lambda-powertools-python/#features
tracer = Tracer()
logger = Logger()
metrics = Metrics()
app = ApiGatewayResolver()

SECRET_NAME = (
    "arn:aws:secretsmanager:us-west-2:111512425976:secret:/data-team/dbt_token-08EQKQ"
)
REGION_NAME = "us-west-2"

# Create a Secrets Manager client
API_BASE = "https://cloud.getdbt.com/api/v2"
ACCOUNT_ID = "7020"
JOB_ID = "47914"


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def run_job_handler(event, context: LambdaContext):
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=REGION_NAME)
    get_secret_value_response = client.get_secret_value(SecretId=SECRET_NAME)
    dbt_api_key = json.loads(get_secret_value_response["SecretString"])["dbt_token"]
    json_ = {'cause': 'Testing functionality'}
    HEADERS = {"Content-Type": "application/json", "Authorization": dbt_api_key}

    api_suffix = f"/accounts/{ACCOUNT_ID}/jobs/{JOB_ID}/run/"
    url = API_BASE + api_suffix
    response = requests.post(url, headers=HEADERS, json=json_)
    logger.info(response.json())
    run_id = response.json()['data']['id']
    if response.status_code != 200:
        return {"status": "API error.", "event": event}
    else:
        return {"status": "SUCCEEDED", "event": event, "run_id": run_id}

def check_run_handler(event, context: LambdaContext):
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=REGION_NAME)
    get_secret_value_response = client.get_secret_value(SecretId=SECRET_NAME)
    dbt_api_key = json.loads(get_secret_value_response["SecretString"])["dbt_token"]
    json_ = {'cause': 'Testing functionality'}
    HEADERS = {"Content-Type": "application/json", "Authorization": dbt_api_key}

    run_id = str(event['run_id'])

    api_suffix = f"/accounts/{ACCOUNT_ID}/runs/{run_id}/"
    url = API_BASE + api_suffix
    response = requests.get(url, headers=HEADERS, json=json_)
    run_status = response.json()['data']['status']
    if run_status in [20, 30]:
        return {"status": "Run failed.", "event": event}
    elif run_status == 10:
        return {"status": "SUCCEEDED", "event": event}
