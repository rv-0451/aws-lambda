import boto3
import json


class Elbv2Service:
    def __init__(self, listener_arn: str, region_name: str):
        self.elbv2_client = boto3.client('elbv2', region_name=region_name)
        self.listener_arn = listener_arn

    def get_certs(self) -> list:
        response = self.elbv2_client.describe_listener_certificates(
            ListenerArn=self.listener_arn
        )
        cert_list = response['Certificates']
        filtered_certs = list(
            filter(lambda x: x['IsDefault'] is False, cert_list))
        cert_arns = list(
            map(lambda x: x['CertificateArn'], filtered_certs))
        return cert_arns

    def remove_certs(self, cert_arns: list) -> None:
        for cert_arn in cert_arns:
            _ = self.elbv2_client.remove_listener_certificates(
                ListenerArn=self.listener_arn,
                Certificates=[{'CertificateArn': cert_arn}]
            )

    def update_certs(self, cert_arns: list) -> None:
        for cert_arn in cert_arns:
            _ = self.elbv2_client.add_listener_certificates(
                ListenerArn=self.listener_arn,
                Certificates=[{'CertificateArn': cert_arn}]
            )


class AcmService:
    def __init__(self, region_name: str):
        self.acm_client = boto3.client('acm', region_name=region_name)

    def _get_cert_summary_list(self) -> list:
        return self.acm_client.list_certificates()['CertificateSummaryList']

    def get_cert_arns(self, new_dn_list: list) -> list:
        cert_list = self._get_cert_summary_list()
        filtered_certs = list(filter(lambda x: any(
            dn == x['DomainName'] for dn in new_dn_list), cert_list))
        cert_arns = list(
            map(lambda x: x['CertificateArn'], filtered_certs))
        return cert_arns


def lambda_response(status_code: int, msg: str, err="") -> dict:
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'Message': msg,
            'Error': err
        })
    }


def lambda_handler(event, context) -> dict:
    region_name = event['region_name']
    listener_arn = event['listener_arn']
    new_dn_list = event['new_dn_list']

    elbv2_svc = Elbv2Service(listener_arn, region_name)
    acm_svc = AcmService(region_name)

# Remove old certs from the LB's listener
    try:
        current_cert_arns = elbv2_svc.get_certs()
    except Exception as e:
        return lambda_response(500, "Failed to list ALB certificates", str(e.args))

    try:
        elbv2_svc.remove_certs(current_cert_arns)
    except Exception as e:
        return lambda_response(500, "Failed to remove old ALB certificates", str(e.args))

# Bind new certs to the LB's listener
    try:
        new_cert_arns = acm_svc.get_cert_arns(new_dn_list)
    except Exception as e:
        return lambda_response(500, "Failed to get new certificates from ACM", str(e.args))

    try:
        elbv2_svc.update_certs(new_cert_arns)
    except Exception as e:
        return lambda_response(500, "Failed to update ALB with new certificates", str(e.args))

    return lambda_response(200, "Operation was successful")
