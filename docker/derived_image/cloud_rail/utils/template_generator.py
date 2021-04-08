import os

from api.dtos.customer_dto import CustomerDTO


def generate_templates(customer: CustomerDTO,
                       template_path: str,
                       trusted_account_id: str,
                       working_dir: str = None):
    working_dir = working_dir or os.getcwd()
    template_folder = os.path.join(working_dir, 'templates')
    os.makedirs(template_folder, exist_ok=True)
    with open(template_path, 'r') as template_file:
        template = template_file.read()
        iac_template = template \
            .replace('{{ROLE_NAME}}', customer.role_name) \
            .replace('{{EXTERNAL_ID}}', customer.external_id) \
            .replace('{{INDENI_ACCOUNT_ID}}', trusted_account_id)
        template_file_name = os.path.splitext(os.path.basename(template_path))[0]
        with open(os.path.join(template_folder, template_file_name), 'w') as iac_file:
            iac_file.write(iac_template)
    return iac_file.name
