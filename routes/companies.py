import connexion

from service import companies as service
from service import message as model_message
from service import documents as model_documents
from helpers import utils


def route_list_companies():
    result = service.get_list_companies()
    return utils.build_response(result)


def route_get_company_byid(company_id):
    result = service.get_list_companies(company_id)
    return utils.build_response(result)


def route_save_company():
    files = connexion.request.files
    body = connexion.request.form
    result = service.create_company(body, files)
    result['http_status'] = 201
    return utils.build_response(result)


def route_delete_company(company_id):
    result = service.delete_company(company_id)
    return utils.build_response(result)


def route_modify_company():
    files = connexion.request.files
    body = connexion.request.form
    result = service.modify_company(body, files)
    return utils.build_response(result)


def patch_company(company_id):
    files = connexion.request.files
    body = connexion.request.form
    result = service.patch_company(company_id, body, files)
    return utils.build_response(result)


def get_documents(company_user: str, doc_type: str, files: str = None,
                  since: str = None, until: str = None):
    result = model_documents.get_documents_by_type(
        company_user, doc_type, files, since, until
    )
    return utils.build_response(result)


def get_messages(company_user: str, files: str = None, since: str = None,
                 until: str = None):
    result = model_message.get_by_company(company_user, files, since, until)
    return utils.build_response(result)


def process_message(company_user: str, key: str, xml: str = None):
    result = model_message.process_message(company_user, key, include_xml=xml)
    return utils.build_response(result)
