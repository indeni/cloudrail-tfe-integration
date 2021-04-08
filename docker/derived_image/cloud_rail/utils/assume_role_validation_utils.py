import logging
import boto3

from environment_context.data.iam.policy import AssumeRolePolicy
from environment_context.data.iam.policy_statement import StatementEffect
from environment_context.data.iam.principal import PrincipalType
from environment_context.data.iam.role import Role


def can_assume_role(account_id: str, external_id: str, role_name: str) -> bool:
    role_arn = 'arn:aws:iam::{}:role/{}'.format(account_id, role_name)
    log_msg_suffix = f'using ARN: {role_arn} and external id {external_id} for account {account_id}'
    logging.info(f'Attempting to assume role {log_msg_suffix}')
    try:
        client = boto3.client('sts')
        client.assume_role(RoleArn=role_arn,
                           RoleSessionName='session',
                           DurationSeconds=1000,
                           ExternalId=external_id)
        logging.info(f'Successfully assumed role {log_msg_suffix}')
        return True
    except Exception:
        logging.error(f'Unable to assume role {log_msg_suffix}')
        return False


def is_allowing_external_assume(policy: AssumeRolePolicy, role: Role) -> bool:
    valid_principal_values = [role.account, 'amazonaws.com']
    for statement in policy.get_all_statements():
        return statement.principal.principal_values and \
               statement.principal.principal_type != PrincipalType.SERVICE and \
               any(all(valid_string not in value for valid_string in valid_principal_values) for value in statement.principal.principal_values) and \
               statement.effect == StatementEffect.ALLOW and \
               any('AssumeRole' in action for action in statement.actions)
