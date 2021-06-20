# -*- coding: utf-8 -*-
import connexion
import json
from service import documents as service
from helpers import utils
from helpers.debugging import set_debug_mode


@set_debug_mode
def create_documents():
    body = json.loads(connexion.request.data)
    result = service.create_document(body['data'])
    return utils.build_response(result)


def processing_documents():
    body = json.loads(connexion.request.data)
    result = service.processing_documents(
        body['data']['nombre_usuario'],
        body['data']['clavelarga'],
        body['data'].get('respuesta', False)
    )
    return utils.build_response(result)


def consult_documents():
    body = json.loads(connexion.request.data)
    result = service.consult_document_notdatabase(body['data']['id_compania'], body['data']['clave'],
                                                  body['data']['tipo_documento'])
    return utils.build_response(result)


def get_documents_report():
    body = json.loads(connexion.request.data)
    result = service.document_report(body['data']['id_compania'], body['data']['tipo_documento'])
    return utils.build_response(result)


def route_get_vouchers(emisor=None, receptor=None, offset=None, limit=None):
    body = json.loads(connexion.request.data)
    result = service.consult_vouchers(body['data']['id_compania'], emisor, receptor, offset, limit)
    return utils.build_response(result)


def route_get_voucher_byid(clave):
    body = json.loads(connexion.request.data)
    result = service.consult_voucher_byid(body['data']['id_compania'], clave)
    return utils.build_response(result)


def get_pdf(company_user: str, key: str):
    result = service.get_pdf(company_user, key)
    return utils.build_response(result)


def get_signed(company_user: str, key: str):
    result = service.get_property(company_user, key, 'signxml')
    return utils.build_response(result)


def get_answer(company_user: str, key: str):
    result = service.get_property(company_user, key, 'answerxml')
    return utils.build_response(result)
