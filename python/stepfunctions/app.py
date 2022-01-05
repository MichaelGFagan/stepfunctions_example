#!/usr/bin/env python3

import os
import aws_cdk as cdk
from aws_cdk import App
from stepfunctions.stepfunctions_stack import JobPollerStack

aws_environment = cdk.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"], region="us-west-2"
)

app = App()
JobPollerStack(app, "aws-stepfunctions-integ", env=aws_environment)
app.synth()
