import connexion

from service import message as model_message
from helpers.utils import build_response
from helpers.debugging import set_debug_mode


def create_message():
    body = connexion.request.json
    result = model_message.create(body)
    result['http_status'] = 201
    return build_response(result)


def process_message():
    data = connexion.request.json
    result = model_message.process_message(
        company_user=data['compania'],
        key_mh=data['clave'],
        rec_seq_num=data['consecutivo'],
        include_xml=data.get('xml')
    )
    return build_response(result)


def get_by_company(company: str, files: str = None):
    result = model_message.get_by_company(company, files)
    return build_response(result)


def get_prop(company_user: str, key: str, prop_name: str):
    result = model_message.get_prop(company_user, key, prop_name)
    return build_response(result)
