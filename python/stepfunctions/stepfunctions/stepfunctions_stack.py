from aws_cdk import (
    aws_stepfunctions as _aws_stepfunctions,
    aws_stepfunctions_tasks as _aws_stepfunctions_tasks,
    aws_lambda as _lambda,
    aws_secretsmanager as secrets,
    App, Duration, Stack
)


class JobPollerStack(Stack):
    def __init__(self, app: App, id: str, **kwargs) -> None:
        super().__init__(app, id, **kwargs)

        layer_path = "layers/stepfunctions.zip"

        dbt_cloud_api_key = secrets.Secret.from_secret_complete_arn(
          self,
          "secret_id",
          "arn:aws:secretsmanager:us-west-2:111512425976:secret:/data-team/dbt_token-08EQKQ",
        )

        self.lambda_layer = _lambda.LayerVersion(
          self,
          "lambda_layer",
          layer_version_name="stepfunctions",
          code=_lambda.Code.from_asset(layer_path)
        )

        # Lambda Handlers Definitions

        # submit_lambda = _lambda.Function(self, 'submitLambda',
        #                                  handler='lambda_function.lambda_handler',
        #                                  runtime=_lambda.Runtime.PYTHON_3_9,
        #                                  code=_lambda.Code.from_asset('lambdas/submit'))

        submit_lambda = _lambda.Function(self, "submitLambda",
                                         handler="lambda.run_job_handler",
                                         runtime=_lambda.Runtime.PYTHON_3_9,
                                         code=_lambda.Code.from_asset("lambdas/dbt_cloud"),
                                         layers=[self.lambda_layer])

        check_run_lambda = _lambda.Function(self, "checkRunLambda",
                                         handler="lambda.check_run_handler",
                                         runtime=_lambda.Runtime.PYTHON_3_9,
                                         code=_lambda.Code.from_asset("lambdas/dbt_cloud"),
                                         layers=[self.lambda_layer])

        dbt_cloud_api_key.grant_read(submit_lambda)
        dbt_cloud_api_key.grant_read(check_run_lambda)

        status_lambda = _lambda.Function(self, 'statusLambda',
                                         handler='lambda_function.lambda_handler',
                                         runtime=_lambda.Runtime.PYTHON_3_9,
                                         code=_lambda.Code.from_asset('lambdas/status'))


        # Step functions Definition

        # submit_job = _aws_stepfunctions_tasks.LambdaInvoke(
        #     self, "Submit Job",
        #     lambda_function=submit_lambda,
        #     output_path="$.Payload",
        # )

        submit_job = _aws_stepfunctions_tasks.LambdaInvoke(
              self, "Submit dbt Cloud job",
              lambda_function=submit_lambda,
              output_path="$.Payload"
        )

        wait_job = _aws_stepfunctions.Wait(
            self, "Wait 30 Seconds",
            time=_aws_stepfunctions.WaitTime.duration(
                Duration.seconds(30))
        )

        status_job = _aws_stepfunctions_tasks.LambdaInvoke(
            self, "Get Status",
            lambda_function=status_lambda,
            output_path="$.Payload",
        )

        check_run = _aws_stepfunctions_tasks.LambdaInvoke(
            self, "Get Run Status",
            lambda_function=check_run_lambda,
            output_path="$.Payload",
        )

        fail_job = _aws_stepfunctions.Fail(
            self, "Fail",
            cause='AWS Batch Job Failed',
            error='DescribeJob returned FAILED'
        )

        succeed_job = _aws_stepfunctions.Succeed(
            self, "Succeeded",
            comment='AWS Batch Job succeeded'
        )

        # Create Chain

        # definition = submit_job.next(wait_job)\
        #     .next(status_job)\
        #     .next(_aws_stepfunctions.Choice(self, 'Job Complete?')
        #           .when(_aws_stepfunctions.Condition.string_equals('$.status', 'FAILED'), fail_job)
        #           .when(_aws_stepfunctions.Condition.string_equals('$.status', 'SUCCEEDED'), succeed_job)
        #           .otherwise(wait_job))

        definition = submit_job.next(wait_job)\
            .next(check_run)\
            .next(_aws_stepfunctions.Choice(self, 'Job Complete?')
                  .when(_aws_stepfunctions.Condition.string_equals('$.status', 'FAILED'), fail_job)
                  .when(_aws_stepfunctions.Condition.string_equals('$.status', 'SUCCEEDED'), succeed_job)
                  .otherwise(wait_job))

        # Create state machine
        sm = _aws_stepfunctions.StateMachine(
            self, "StateMachine",
            definition=definition,
            timeout=Duration.minutes(5),
        )
