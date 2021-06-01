import base64
from logging import getLogger

from bs4 import BeautifulSoup
from jinja2 import Template

from infrastructure import company_smtp
from infrastructure import documents
from infrastructure import template as dao_template
from configuration import globalsettings
from infrastructure.emails import send_email
from service import fe_enums
from helpers.errors.enums import InputErrorCodes, InternalErrorCodes
from helpers.errors.exceptions import InputError, ServerError
from helpers.utils import build_response_data
from helpers.validations.document import KEY_PARTS_SLICES

cfg = globalsettings.cfg
TEMPLATE_TYPES = {
    'email': 1
}
_logger = getLogger(__name__)


def sent_email_fe(data: dict):
    if 'email' not in data:  # arbitrary af check
        document = documents.get_document(data['key_mh'])
    else:
        document = data.copy()

    if not document:
        raise InputError('document', data['key_mh'], error_code=InputErrorCodes.NO_RECORD_FOUND)

    if document['status'] != 'aceptado':
        raise InputError(
            error_code=InputErrorCodes.OTHER,
            message=(
                """No se puede enviar el documento: su estado no es: "aceptado".
Estado del documento: "{}" """
            ).format(document['status'])
        )
    if document['document_type'] == "TE":
        raise InputError(
            error_code=InputErrorCodes.OTHER,
            message=(
                """No se puede enviar el documento: se especifico que no se \
pueden enviar Tiquetes Electronicos por correo."""
            )
        )
    if not document['email']:
        raise InputError(
            error_code=InputErrorCodes.OTHER,
            message=(
                """No se puede enviar el documento: no se especifico un correo \
electronico para el receptor. """
            )
        )

    smtp_data = company_smtp.get_company_smtp(data['company_user'])
    if smtp_data:
        host = smtp_data['host']
        sender = smtp_data['sender']
        username = smtp_data['user']
        password = smtp_data['password']
        port = smtp_data['port']
        encrypt_type = smtp_data['encrypt_type']
    else:
        host = cfg['email']['host']
        sender = cfg['email']['sender']
        username = cfg['email']['user']
        password = cfg['email']['password']
        port = cfg['email']['port']
        encrypt_type = cfg['email']['encrypt_type']

    email_template = dao_template.select_unique_template(
        TEMPLATE_TYPES['email'], document['company_id']
    )
    if email_template is None:
        email_template = dao_template.select_common_templates(TEMPLATE_TYPES['email'])
        if email_template is None:
            _logger.error('''***Error: no se encontro plantilla para generar email.
Compañia emisora: {}
Tipo Plantilla: {}'''.format(document['company_name'], TEMPLATE_TYPES['email']))
            raise ServerError(
                error_code=InternalErrorCodes.INTERNAL_ERROR
            )
    email_template = base64.b64decode(email_template).decode('utf-8')

    primary_recipient = document['email']
    receivers = [primary_recipient]
    additional_recipients = documents.get_additional_emails(data['key_mh'])
    if isinstance(additional_recipients, list):
        receivers += list(x['email'] for x in additional_recipients)

    sequence_slice = KEY_PARTS_SLICES['sequence']
    doc_type_desc = fe_enums.tagNamePDF[document['document_type']]
    subject = "Envio de {}: {} del Emisor: {}".format(
        doc_type_desc,
        document['key_mh'][sequence_slice],
        document['company_name']
    )

    template_content = Template(email_template)
    template_context = {
        'doc_type': doc_type_desc,
        'issuer': document['company_name']
    }
    email_content = template_content.render(template_context)
    content = email_content

    signed_name = document['document_type'] + "_" + document['key_mh'] + '.xml'
    signed_file = base64.b64decode(document['signxml'])

    answer_name = "AHC_" + document['key_mh'] + '.xml'
    answer_file = base64.b64decode(document['answerxml'])

    attachments = [
        {'name': signed_name, 'file': signed_file},
        {'name': answer_name, 'file': answer_file}
    ]

    if document['pdfdocument'] is not None:
        pdf_name = document['document_type'] + '_' + document['key_mh'] + '.pdf'
        pdf_file = base64.b64decode(document['pdfdocument'])

        attachments.append({'name': pdf_name, 'file': pdf_file})

    send_email(receivers, host, sender, port, encrypt_type,
               username, password, subject, content, attachments)
    return build_response_data({'message': 'Email successfully sent.'})


def send_custom_email(data, file1, file2, file3):
    smtp_data = company_smtp.get_company_smtp(data['company_id'])
    if not smtp_data:
        raise InputError('company SMTP', data['company_id'],
                         error_code=InputErrorCodes.NO_RECORD_FOUND)

    receivers = data['receivers'].split(',')
    if not receivers[0]:
        raise InputError(error_code=InputErrorCodes.MISSING_PROPERTY, message='No recipient(s) specified.')

    subject = data['subject']
    content = {
        'plain': _html_to_plain(data['content']),
        'html': data['content']
    }
    # wish these were just a list...
    # files are optional, so, let's create a list containing any files given
    attachments = []
    if file1:
        name_file1 = file1.filename
        file1 = file1.stream.read()
        attachments.append({'file': file1, 'name': name_file1})

    if file2:
        name_file2 = file2.filename
        file2 = file2.stream.read()
        attachments.append({'file': file2, 'name': name_file2})

    if file3:
        name_file3 = file3.filename
        file3 = file3.stream.read()
        attachments.append({'file': file3, 'name': name_file3})

    host = smtp_data['host']
    sender = smtp_data['sender']
    username = smtp_data['user']
    password = smtp_data['password']
    port = smtp_data['port']
    encrypt_type = smtp_data['encrypt_type']
    send_email(receivers, host, sender, port, encrypt_type,
               username, password, subject, content, attachments)
    return build_response_data({'message': 'email sent successfully'})


def _html_to_plain(html: str) -> str:
    soup = BeautifulSoup(html, features='html.parser')

    for garbage in soup(['head','style','script']):
        garbage.extract()

    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split('  '))
    return '\n'.join(chunk for chunk in chunks if chunk)
