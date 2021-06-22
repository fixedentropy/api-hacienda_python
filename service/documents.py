import base64
import logging
from functools import partial

from lxml import etree

from extensions import mysql
from helpers.arrangers import document as document_arranger
from helpers.errors.enums import InputErrorCodes, InternalErrorCodes
from helpers.errors.exceptions import InputError, ServerError
from helpers.utils import build_response_data, run_and_summ_collec_job, get_smtp_error_code
from helpers.validations import document as document_validator
from infrastructure import companies
from infrastructure import documents
from infrastructure import request_pool
from infrastructure.dbadapter import commit as db_commit
from . import api_facturae
from . import emails
from . import makepdf

docLogger = logging.getLogger(__name__)


def makeqr(_key_mh: str, date_doc: str):
    from base64 import b64encode
    import qrcode
    from io import BytesIO

    # base_url = 'https://api.spykacr.com/api/queryqr/'
    # h = sha3_512()
    # h.update(_key_mh.encode())
    # key_hash = h.hexdigest()

    # check if duplicate hash

    # qr_data = base_url + key_hash
    qr_data = _key_mh
    qr_img = qrcode.make(qr_data)
    buffered = BytesIO()
    qr_img.save(buffered, 'JPEG')
    b64_img_data = b64encode(buffered.getvalue()).decode()

    return b64_img_data
    # return {
    #     'b64img': b64_img_data,
    #     'keyhash': key_hash
    # }


def create_document(data):
    _company_user = data['nombre_usuario']

    company_data = companies.get_company_data(_company_user)
    if not company_data:
        raise InputError('company',
                         _company_user,
                         error_code=InputErrorCodes.NO_RECORD_FOUND)

    if not company_data['is_active']:
        raise InputError(error_code=InputErrorCodes.INACTIVE_COMPANY)

    _key_mh = data['clavelarga']
    if documents.verify_exists(company_data['id'], _key_mh):
        raise InputError('Document with key {}'.format(_key_mh),
                         error_code=InputErrorCodes.DUPLICATE_RECORD)

    signature = companies.get_sign_data(_company_user)
    if not signature:
        raise InputError(error_code=InputErrorCodes.NO_RECORD_FOUND,
                         message=("No signature information was found"
                                  " for the company; can't sign the document,"
                                  " so the document can't be created."))

    xml_data, pdf_data = document_arranger.arrange_data(data, company_data)
    document_validator.validate_data(xml_data)

    _type_document = xml_data['tipo']
    _email_costs = None  # MARKED FOR DEATH . Using _additional_emails now
    _additional_emails = []
    _email = None

    _receptor = xml_data.get('receptor')
    if _receptor:
        _email = _receptor.get('correo')
        _additional_emails = _receptor.get('correosAdicionales', [])

    _total_taxes = xml_data['totalImpuestos']
    _lines = xml_data['detalles']
    _total_document = xml_data['totalComprobantes']

    datecr = api_facturae.get_time_hacienda(True)

    try:
        xml = api_facturae.gen_xml_v43(
            company_data=company_data,
            document_type=_type_document,
            key_mh=_key_mh,
            consecutive=xml_data['consecutivo'],
            date=xml_data['fechafactura'],
            sale_conditions=xml_data['condicionVenta'],
            activity_code=xml_data['codigoActividad'],
            receptor=_receptor,
            total_servicio_gravado=xml_data['totalServGravados'],
            total_servicio_exento=xml_data['totalServExentos'],
            total_serv_exonerado=xml_data['totalServExonerado'],
            total_mercaderia_gravado=xml_data['totalMercanciasGravados'],
            total_mercaderia_exento=xml_data['totalMercanciasExentos'],
            total_merc_exonerada=xml_data['totalMercExonerada'],
            total_otros_cargos=xml_data['totalOtrosCargos'],
            base_total=xml_data['totalVentasNetas'],
            total_impuestos=_total_taxes,
            total_descuento=xml_data['totalDescuentos'],
            lines=_lines,
            otros_cargos=xml_data.get('otrosCargos'),
            invoice_comments=xml_data.get('otros'),
            referencia=xml_data.get('referencia'),
            payment_methods=xml_data['medioPago'],
            plazo_credito=xml_data['plazoCredito'],
            moneda=xml_data['codigoTipoMoneda'],
            total_taxed=xml_data['totalGravados'],
            total_exone=xml_data['totalExonerado'],
            total_untaxed=xml_data['totalExentos'],
            total_sales=xml_data['totalVentas'],
            total_return_iva=xml_data['totalIVADevuelto'],
            total_document=_total_document
        )
    except KeyError as ker:  # atm, this is just a baseImponible exception.
        raise  # TODO : return {'error' : str(ker)} # INVALID DOCUMENT ERROR #TODO

    xml_to_sign = str(xml)

    try:
        xml_sign = api_facturae.sign_xml(
            signature['signature'],
            company_data['pin_sig'], xml_to_sign
        )
    except Exception as ex:  # todo: be more specific about exceptions #TODO
        raise  # TODO : return {'error' : 'A problem occurred when signing the XML Document.'}  # INTERNAL ERROR

    xmlencoded = base64.b64encode(xml_sign)

    pdfencoded = None  # Por si ES tiquete que guarde nada como pdf
    if pdf_data is not None:  # _type_document != 'TE':
        qr_img = makeqr(_key_mh, datecr)
        pdf_data['footer']['qr_img'] = qr_img
        pdf_data['footer']['qr_size'] = 95
        try:
            pdf = makepdf.render_pdf(pdf_data)
        except Exception as ex:  # TODO : be more specific about exceptions
            raise  # TODO : 'A problem occured when creating the PDF File for the document.' # INTERNAL ERROR

        pdfencoded = base64.b64encode(pdf)

    doc_id = documents.save_document(
        _company_user, _key_mh, xmlencoded, 'creado', datecr, _type_document,
        _receptor, _total_document, _total_taxes, pdfencoded, _email, _email_costs
    )

    _id_company = company_data['id']

    if len(_additional_emails) > 0:
        save_additional_emails(doc_id, _additional_emails)

    save_document_lines(_id_company, doc_id, _lines)
    db_commit()

    return {
        'status': 'procesando',
        'http_status': 201,
        'message': 'Documento creado exitosamente.'
    }


def save_document_lines(company_id, doc_id, lines):
    for _line in lines:
        _line_number = _line['numero']
        _quantity = _line['cantidad']
        _unity = _line['unidad']
        _detail = _line['detalle']
        _unit_price = _line['precioUnitario']
        _net_tax = _line['impuestoNeto']
        _total_line = _line['totalLinea']

        line_id = documents.save_document_line_info(
            company_id, doc_id, _line_number, _quantity, _unity, _detail,
            _unit_price, _net_tax, _total_line
        )

        _taxes = _line.get('impuesto')
        if _taxes:
            save_document_taxes(doc_id, line_id, _taxes)

    return True


def save_document_taxes(doc_id, line_number, taxes):
    for _tax in taxes:
        _rate_code = _tax.get('codigoTarifa')
        _code = _tax['codigo']
        _rate = _tax['tarifa']
        _amount = _tax['monto']

        documents.save_document_line_taxes(
            doc_id, line_number, _rate_code, _code, _rate, _amount
        )

    return True


def save_additional_emails(doc_id, _emails):
    for email in _emails:
        documents.save_document_additional_email(doc_id, email)

    return True


def processing_documents(company_user, key_mh, answer: bool):
    company_data = companies.get_company_data(company_user)
    if not company_data:
        raise InputError('company', company_user,
                         error_code=InputErrorCodes.NO_RECORD_FOUND)

    if not company_data['is_active']:
        raise InputError(error_code=InputErrorCodes.INACTIVE_COMPANY)

    document_data = documents.get_document(company_data['id'], key_mh)
    if not document_data:
        raise InputError('document', key_mh,
                         error_code=InputErrorCodes.NO_RECORD_FOUND)

    if document_data['status'] == 'creado':  # todo: optimize
        result = validate_document(company_data, document_data)
    else:
        result = consult_document(company_data, document_data, answer)
    return result


# @log_section('Sending Documents')
def validate_documents(env: str):
    item_cb = validate_document
    collec_cb_args = (0, env)
    with mysql.app.app_context():
        return _run_and_summ_docs_job(item_cb=item_cb,
                                      collec_cb_args=collec_cb_args)


def validate_document(company_user, key_mh):
    response = {
        'status': 'procesando',
        'message': 'procesando'
    }

    if not request_pool.spend():
        return response

    if isinstance(company_user, str):
        company_data = companies.get_company_data(company_user)
    else:
        company_data = company_user

    if isinstance(key_mh, str):
        document_data = documents.get_document(company_data['id'], key_mh)
    else:
        document_data = key_mh

    date_cr = api_facturae.get_time_hacienda(False)
    date = api_facturae.get_time_hacienda(True)

    try:
        token_m_h = api_facturae.get_token_hacienda(
            company_data['company_user'], company_data['user_mh'],
            company_data['pass_mh'], company_data['env']
        )
    except Exception as ex:  # TODO : be more specific about exceptions
        raise  # TODO : 'A problem occured when attempting to get the token from Hacienda.' # INTERNAL ERROR

    recipient = {
        'dni_type_receiver': document_data['dni_type_receiver'],
        'dni_receiver': document_data['dni_receiver']
    }
    try:
        api_facturae.send_xml_fe(
            company_data, recipient, document_data['key_mh'], token_m_h,
            date_cr, document_data['signxml'], company_data['env']
        )
    except Exception as ex:  # TODO : be more specific about exceptions
        raise  # TODO: 'error' : 'A problem occurred when attempting to send the document to Hacienda.' # INTERNAL ERROR

    documents.update_document(
        company_data['company_user'], document_data['key_mh'], None,
        'procesando', date
    )

    db_commit()

    return response


# @log_section("Fetching Documents' Statuses")
def consult_documents(env):
    item_cb = partial(consult_document, answer=False)
    collec_cb_args = (1, env)
    with mysql.app.app_context():
        return _run_and_summ_docs_job(item_cb=item_cb,
                                      collec_cb_args=collec_cb_args)


def consult_document(company_user, key_mh, answer: bool):  # todo: review this...
    if isinstance(company_user, str):
        company_data = companies.get_company_data(company_user)
    else:
        company_data = company_user

    if isinstance(key_mh, str):
        document_data = documents.get_document(company_data['id'], key_mh)
    else:
        document_data = key_mh

    date = api_facturae.get_time_hacienda(True)

    response = {
        'status': document_data['status'],
        'data': {
            'date': date,
            'detail': extract_answer_detail(document_data['answerxml'])
        }
    }
    if answer:
        response['data']['xml-respuesta'] = document_data['answerxml']

    if not request_pool.spend():
        return response

    try:
        token_m_h = api_facturae.get_token_hacienda(
            company_data['company_user'], company_data['user_mh'],
            company_data['pass_mh'], company_data['env']
        )
    except Exception as ex:  # TODO
        raise  # TODO : 'error' : 'A problem occured when attempting to get the token from Hacienda.' # INTERNAL ERROR

    try:
        response_json = api_facturae.consulta_clave(
            document_data['key_mh'], token_m_h, company_data['env']
        )
    except Exception as ex:  # TODO : be more specific about exceptions
        raise  # TODO : A problem occurred when attempting to query the document to Hacienda.' # INTERNAL ERROR

    res_doc_status = response_json.get('ind-estado')
    res_answer_xml = response_json.get('respuesta-xml')

    document_data['status'] = res_doc_status
    if res_answer_xml is not None:  # got an xml? save it
        documents.update_document(company_data['company_user'], document_data['key_mh'], res_answer_xml,
                                  res_doc_status, date)
        document_data['answerxml'] = res_answer_xml
    else:  # check if we already had an xml...
        doc_answer_xml = document_data['answerxml']
        if doc_answer_xml is not None:  # If we had one, do not overwrite it, but update answer date
            documents.update_document(company_data['company_user'], document_data['key_mh'],
                                      doc_answer_xml.encode('utf8'),
                                      res_doc_status, date)
        else:  # just update the answer date
            documents.update_document(company_data['company_user'], document_data['key_mh'], None,
                                      res_doc_status, date)

    # just to mask that the document hasn't been sent to hacienda... for the dbase systems...
    if res_doc_status == 'creado':
        res_doc_status = 'procesando'

    response['status'] = res_doc_status
    if document_data['isSent'] is None:
        mail_sent = 0
        try:
            emails.sent_email_fe(document_data)
        except InputError:
            pass
        except Exception as ex:  # TODO : be more specific about exceptions
            docLogger.error("**Email couldn't be sent for some reason:***", exc_info=ex)
            response['data']['warning'] = 'A problem occurred when attempting to send the email.'  # WARNING
            # temp juggling insanity... nevermind, don't look at it...
            mail_sent = get_smtp_error_code(ex)

        documents.update_is_sent(document_data['id'], mail_sent)

    if res_answer_xml:
        response['data']['detail'] = extract_answer_detail(res_answer_xml)
        if answer:
            response['data']['xml-respuesta'] = res_answer_xml

    db_commit()

    return response


def document_report(company_user, document_type):
    result = documents.get_documentsreport(company_user, document_type)
    return build_response_data({'data': {'documents': result}})


def get_pdf(company_user: str, key: str):
    company = companies.get_company_data(company_user)
    if not company:
        raise InputError(
            error_code=InputErrorCodes.NO_RECORD_FOUND,
            message='La compañia indicada no fue encontrada.'
        )

    document = documents.get_document(company['id'], key)
    if not document:
        raise InputError('document', key,
                         error_code=InputErrorCodes.NO_RECORD_FOUND)

    if document['pdfdocument']:
        data = {'data': {'pdf': document['pdfdocument']}}
    else:
        data = {
            'message': """The specified document does not have a PDF file.
Document Type: {}
*If the document type is not 'TE', please contact the API Admin.""".format(
                document['document_type'])
        }

    return build_response_data(data)


def get_property(company_user: str, key: str, prop_name: str):
    company = companies.get_company_data(company_user)
    if not company:
        raise InputError(
            error_code=InputErrorCodes.NO_RECORD_FOUND,
            message='La compañia indicada no fue encontrada.'
        )

    document = documents.get_document(company['id'], key)
    if not document:
        raise InputError('document', key,
                         error_code=InputErrorCodes.NO_RECORD_FOUND)

    if prop_name not in document:
        raise InputError(
            error_code=InputErrorCodes.MISSING_PROPERTY,
            message='"{}" no es una propiedad del recurso solicitado.'.format(
                prop_name
            )
        )

    return build_response_data({
        'data': {
            prop_name: document[prop_name]
        }
    })


def get_files(company_user: str, key: str):
    company = companies.get_company_data(company_user)
    if not company:
        raise InputError(
            error_code=InputErrorCodes.NO_RECORD_FOUND,
            message='La compañia indicada no fue encontrada.'
        )

    document = documents.get_document(company['id'], key)
    if not document:
        raise InputError('document', key,
                         error_code=InputErrorCodes.NO_RECORD_FOUND)

    data = {
        'id': document['id'],
        'pdfdocument': document['pdfdocument'],
        'signxml': document['signxml'],
        'answerxml': document['answerxml']
    }
    return build_response_data({
        'data': data
    })


# if this fails horribly, I will rollback and apply a simpler solution...
_run_and_summ_docs_job = partial(
    run_and_summ_collec_job,
    collec_cb=documents.get_documents,
    item_id_keys='key_mh',
    item_cb_kwargs_map={
        'company_user': 'company_user',
        'key_mh': 'key_mh'
    },
    sleepme=15
)


def extract_answer_detail(xml) -> str:
    if xml is None:
        return ''

    decoded = base64.b64decode(xml)
    parsed_answer_xml = etree.fromstring(decoded)
    return parsed_answer_xml.findtext('{*}DetalleMensaje') or ''


def consult_voucher_byid(company_user, clave):
    company_data = companies.get_company_data(company_user)
    if not company_data:
        raise InputError('company', company_user,
                         error_code=InputErrorCodes.NO_RECORD_FOUND)

    try:
        token_m_h = api_facturae.get_token_hacienda(company_user,
                                                    company_data['user_mh'],
                                                    company_data['pass_mh'],
                                                    company_data['env'])
    except Exception as ex:  # TODO : be more specific with exceptions
        raise  # TODO : hacienda token error return 'A problem occurred when attempting to get the token from Hacienda.'

    try:
        response_json = api_facturae.get_voucher_byid(clave, token_m_h)
    except Exception as ex:  # TODO : be more specific with exceptions
        raise  # TODO : Internal get voucher error "A problem occurred when attempting to fetch the specified document."

    response_status = response_json.get('status')
    response_text = response_json.get('text')
    if response_status == 200:
        return build_response_data({'data': {'Comprobante': response_text}})
    else:
        raise ServerError(error_code=InternalErrorCodes.INTERNAL_ERROR)
        # return errors.build_internalerror_error('Hacienda considered the query as unauthorized.')


def consult_document_notdatabase(company_user, key_mh, document_type):
    company_data = companies.get_company_data(company_user)
    if not company_data:
        raise InputError('company', company_user,
                         error_code=InputErrorCodes.NO_RECORD_FOUND)

    date = api_facturae.get_time_hacienda(True)

    try:
        token_m_h = api_facturae.get_token_hacienda(company_user,
                                                    company_data['user_mh'],
                                                    company_data['pass_mh'],
                                                    company_data['env'])
    except Exception as ex:  # TODO : be more specific about exceptions
        raise  # TODO 'A problem occurred when attempting to get the token from Hacienda.' # INTERNAL ERROR

    try:
        response_json = api_facturae.consulta_documentos(key_mh,
                                                         company_data['env'],
                                                         token_m_h, date, document_type)
    except Exception as ex:  # TODO : be more specific about exceptions
        raise  # TODO: 'A problem occurred when attempting to fetch the document from Hacienda.' # INTERNAL ERROR

    response_status = response_json.get('ind-estado')
    response_text = response_json.get('respuesta-xml')

    if response_text:
        return build_response_data({'message': response_status,
                                    'data': {'xml-respuesta': response_text}})
    else:
        raise ServerError(error_code=InternalErrorCodes.INTERNAL_ERROR)  # TODO : new code: 2 bad data hacienda


def consult_vouchers(company_user, emisor, receptor, offset, limit):
    company_data = companies.get_company_data(company_user)
    if not company_data:
        raise InputError('company', company_user,
                         error_code=InputErrorCodes.NO_RECORD_FOUND)

    try:
        token_m_h = api_facturae.get_token_hacienda(company_user,
                                                    company_data['user_mh'],
                                                    company_data['pass_mh'],
                                                    company_data['env'])
    except Exception as ex:  # TODO : be more specific with exceptions
        raise  # TODO:new InternalErrorCode 3 token. A problem occurred when attempting to get the token from Hacienda.'

    parameters = {}
    if emisor is not None:
        parameters['emisor'] = emisor
    if receptor is not None:
        parameters['receptor'] = receptor
    if offset is not None:
        parameters['offset'] = offset
    if limit is not None:
        parameters['limit'] = limit

    try:
        response_json = api_facturae.get_vouchers(token_m_h, parameters)
    except Exception as ex:  # TODO : be more specific with exceptions
        raise  # TODO : "A problem occurred when attempting to get the company's vouchers." # INTERNAL ERROR

    response_status = response_json.get('status')
    response_text = response_json.get('text')

    if 200 <= response_status <= 206:
        return build_response_data({'data': {'Comprobantes': response_text}})
    else:
        raise ServerError(error_code=InternalErrorCodes.INTERNAL_ERROR)  # TODO : Hacienda Unauthorized
        # return errors.build_internalerror_error('Hacienda considered the query as unauthorized.')
