from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal

from dateutil import parser
from dateutil import tz
from dateutil.utils import default_tzinfo

from service import fe_enums, utils
from infrastructure import companies as companies_dao
from infrastructure import documents as documents_dao
# from helpers.debugging import time_my_func
from helpers.errors.exceptions import ValidationError
from helpers.errors.enums import ValidationErrorCodes

NO_PDF_TYPES = (fe_enums.TipoDocumentApiSwapped['TE'],)
DATETIME_DISPLAY_FORMAT = '%d-%m-%Y'
DEFAULT_MONEY_VALUE = '0.00000'
DEFAULT_PDF_DECIMAL_VALUE = '0.0'
LOCAL_CURRENCY = 'CRC'
CREDIT_CONDITION_CODE = '02'
CREDIT_CURRENCY_EXCHANGE_POLICY = """\
Si la factura no se cancela dentro del mes de su facturación, \
se debe pagar al tipo de cambio oficial al dia de su cancelación."""
TZ_CR = tz.gettz('America/Costa_Rica')


def arrange_data(data: dict, company_data: dict) -> tuple:
    xml_data = arrange_xml_data(data, company_data)
    if generates_pdf(data):
        pdf_data = arrange_pdf_data(data, company_data)
        xml_data['detalles'], pdf_data['lines'] = arrange_details(data['detalles'])
    else:
        pdf_data = None
        xml_data['detalles'] = arrange_details(data['detalles'], False)

    return xml_data, pdf_data


def arrange_xml_data(data: dict, company: dict) -> dict:
    xml_data = deepcopy(data)

    xml_data['tipoC'] = data['tipo']
    xml_data['tipo'] = fe_enums.TipoDocumentoApi[data['tipo']]
    xml_data['fechafactura'] = parse_datetime(
        data['fechafactura'], 'fechafactura'
    ).isoformat()
    if xml_data['tipo'] == 'FEC':
        recipient = xml_data.get('receptor')
        if recipient and 'codigoActividad' in recipient:
            xml_data['codigoActividad'] = recipient['codigoActividad']

    if 'referencia' in xml_data:
        references = xml_data.pop('referencia')
        if not isinstance(references, str):  # if str, it's not useful, so let it out of our data
            if isinstance(references, dict) \
                    and len(references):
                references = [references]

            for ref in references:
                if 'numeroReferencia' in ref:
                    document = documents_dao.get_document(
                        company['id'], ref['numeroReferencia']
                    )
                    if document is not None:
                        ref['fecha'] = document['datesign'].isoformat()
                    else:
                        ref['fecha'] = parse_datetime(ref['fecha'], 'referencia => fecha').isoformat()

            if references:
                xml_data['referencia'] = references

    if 'receptor' in xml_data:
        recipient = xml_data['receptor']

        additional_emails = recipient.get('correosAdicionales', [])
        if additional_emails:
            additional_emails = list(set(additional_emails))  # remove duplicates
        else:  # for now... falling back to "correo_gastos" if exists
            fallback_email = recipient.get('correo_gastos')
            if fallback_email and isinstance(fallback_email, str):
                additional_emails.append(fallback_email)

        recipient['correosAdicionales'] = additional_emails

    other_charges = arrange_other_charges(xml_data.pop('otrosCargos', []))
    if other_charges:
        xml_data['otrosCargos'] = other_charges

    xml_data['totalServGravados'] = data.get('totalServGravados', DEFAULT_MONEY_VALUE)
    xml_data['totalServExentos'] = data.get('totalServExentos', DEFAULT_MONEY_VALUE)
    xml_data['totalServExonerado'] = data.get('totalServExonerado', DEFAULT_MONEY_VALUE)
    xml_data['totalMercanciasGravados'] = data.get('totalMercanciasGravados', DEFAULT_MONEY_VALUE)
    xml_data['totalMercanciasExentos'] = data.get('totalMercanciasExentos', DEFAULT_MONEY_VALUE)
    xml_data['totalMercExonerada'] = data.get('totalMercExonerada', DEFAULT_MONEY_VALUE)
    xml_data['totalGravados'] = data.get('totalGravados', DEFAULT_MONEY_VALUE)
    xml_data['totalExentos'] = data.get('totalExentos', DEFAULT_MONEY_VALUE)
    xml_data['totalExonerado'] = data.get('totalExonerado', DEFAULT_MONEY_VALUE)
    xml_data['totalDescuentos'] = data.get('totalDescuentos', DEFAULT_MONEY_VALUE)
    xml_data['totalImpuestos'] = data.get('totalImpuestos', DEFAULT_MONEY_VALUE)
    xml_data['totalIVADevuelto'] = data.get('totalIVADevuelto', DEFAULT_MONEY_VALUE)
    xml_data['totalOtrosCargos'] = data.get('totalOtrosCargos', DEFAULT_MONEY_VALUE)

    return xml_data


def arrange_other_charges(other_charges) -> list:
    if not other_charges:
        return []

    _other_charges = other_charges
    if isinstance(other_charges, dict):
        _other_charges = [other_charges]

    arranged = []
    for charge in _other_charges:
        if not charge.get('tipoDocumento'):
            continue

        arranged_charge = {}
        for prop, value in charge.items():
            if value.strip():
                arranged_charge[prop] = value
        arranged.append(arranged_charge)

    return arranged


def arrange_pdf_data(data: dict, company_data: dict) -> dict:
    pdf_data = {}

    _data = arrange_pdf_parties(data, company_data)

    body_data = build_pdf_body_data(_data, company_data)
    pdf_data['body'] = body_data

    header_data = build_pdf_header_data(_data)
    pdf_data['header'] = header_data

    footer_data = build_pdf_footer_data(_data)
    pdf_data['footer'] = footer_data

    return pdf_data


# kinda convoluted...
def arrange_details(details: list, process_pdf: bool = True):
    xml_details = []
    pdf_details = []

    line_count = 1
    for i in range(len(details)):
        line = deepcopy(details[i])

        if 'impuesto' in line:
            arrange_taxes(line['impuesto'])

        cabys = line['codigo']
        amount_total = line['montoTotal'].strip().strip('0.')
        if cabys and amount_total:
            xml_line = deepcopy(line)
            xml_line['numero'] = line_count
            base_imponible = xml_line.pop('baseImponible', '')
            if base_imponible.strip('0.'):
                xml_line['baseImponible'] = base_imponible

            xml_details.append(xml_line)
            line_count += 1

        if process_pdf:
            pdf_line = {
                'numero': line_count - 1,
                '_cabys': line['codigo'],
                'detalle': line.get('detalle', ''),
                'cantidad': utils.stringRound(line['cantidad'])
                if line['cantidad'].strip('0.')
                else DEFAULT_PDF_DECIMAL_VALUE,
                'precioUnitario': utils.stringRound(line['precioUnitario'])
                if line['precioUnitario'].strip('0.')
                else DEFAULT_PDF_DECIMAL_VALUE,
                'impuestoNeto': utils.stringRound(line['impuestoNeto'])
                if line['impuestoNeto'].strip('0.')
                else DEFAULT_PDF_DECIMAL_VALUE,
                'subtotal': utils.stringRound(line['subtotal'])
                if line['subtotal'].strip('0.')
                else DEFAULT_PDF_DECIMAL_VALUE,
                'totalLinea': utils.stringRound(line['totalLinea'])
                if line['totalLinea'].strip('0.')
                else DEFAULT_PDF_DECIMAL_VALUE
            }

            if 'impuesto' in line:
                pdf_line['impuesto'] = deepcopy(line['impuesto'])

            if not cabys or not amount_total:
                pdf_line['numero'] = '∟'
                pdf_line['_cabys'] = \
                    pdf_line['cantidad'] = \
                    pdf_line['precioUnitario'] = \
                    pdf_line['impuestoNeto'] = \
                    pdf_line['subtotal'] = \
                    pdf_line['totalLinea'] = ''

            pdf_details.append(pdf_line)

    if process_pdf:
        return xml_details, pdf_details
    else:
        return xml_details


def arrange_taxes(taxes: list):
    for tax in taxes:
        ex = tax.get('exoneracion')
        if ex and isinstance(ex, dict):
            tax['exoneracion'] = [ex]


def arrange_pdf_parties(data: dict, company_data: dict) -> dict:
    arranged = deepcopy(data)

    # the company the api is generating the pdf for
    first_party = {
        'company_user': company_data['company_user'],
        'name': company_data['name'],
        'idn_type': company_data['type_identification'],
        'idn_number': company_data['identification_dni'],
        'phone': company_data['phone'],
        'email': company_data['email'],
        'address': company_data['address']
    }

    # the "recipient" specified in our json data. This would be an issuer instead if document type is '8' (FEC)
    recipient = data['receptor']
    second_party = {
        'name': recipient['nombre'],
        'idn_type': recipient.get('tipoIdentificacion', ''),
        'idn_number': recipient.get('numeroIdentificacion', ''),
        'phone': recipient.get('telefono', ''),
        'email': recipient.get('correo', ''),
        'address': recipient.get('otrasSenas', '')
    }

    # if document type is '8' (FEC), flip first party for second party (issuer <=> recipient)
    if data['tipo'] == '8':
        arranged['issuer'] = second_party
        arranged['recipient'] = first_party
    else:
        arranged['issuer'] = first_party
        arranged['recipient'] = second_party

    return arranged


def build_pdf_body_data(data: dict, company_data: dict) -> dict:
    total_document = utils.stringRound(data['totalComprobantes'])
    recipient = data['recipient']
    currency = data['codigoTipoMoneda']

    body_data = {
        'key_mh': data['clavelarga'],
        'total_document': total_document,
        'total_taxes': utils.stringRound(data.get('totalImpuestos', '0')),
        'total_discounts': utils.stringRound(data.get('totalDescuentos', '0')),
        'total_sales': utils.stringRound(data['totalVentas']),
        'recipient': recipient
    }
    if 'codigoVendedor' in data:
        body_data['salesman_code'] = data['codigoVendedor']
    elif 'codigo_vendedor' in data:
        body_data['salesman_code'] = data['codigo_vendedor']

    payment_methods_csvs = ', '.join(
        list(
            fe_enums.paymentMethods.get(
                pm.get('codigo'), 'Efectivo'
            ) for pm in data['medioPago']
        )
    )
    body_data['payment_method'] = payment_methods_csvs

    body_data['sale_condition'] = fe_enums.saleConditions.get(
        data['condicionVenta'], 'No especificada'
    )

    body_data['currency'] = {
        'tipoMoneda': currency['tipoMoneda']
    }
    if company_data['pdf_exchangerate']:
        body_data['currency']['tipoCambio'] = utils.stringRound(currency['tipoCambio'])

    body_data['currencySymbol'] = fe_enums.currencies.get(
        currency['tipoMoneda'], ''
    )

    body_data['activity_code'] = data['codigoActividad']
    body_data['total_document_words'] = utils.numToWord(
        total_document, currency['tipoMoneda']
    ).upper()

    if 'totalIVADevuelto' in data:
        body_data['total_returned_iva'] = utils.stringRound(data['totalIVADevuelto'])

    body_data['type_iden_recipient'] = fe_enums.tipoCedulaPDF.get(
        recipient.get('idn_type'),
        'Tipo de identificación no especificada'
    )

    order_num = data.get('numOrden', data.get('numFecha', '')).strip()
    # just making sure "order_num" ain't suddenly a date...
    try:
        parse_datetime(order_num, 'numOrden/numFecha')
        order_num = None
    except ValidationError:
        pass
    if order_num:
        body_data['order_num'] = order_num

    sale_condition = data['condicionVenta']
    if sale_condition == '02':
        issued_date = parse_datetime(
            data['fechafactura'], 'fechafactura'
        )
        term_days = data.get('plazoCredito', 0)
        if not term_days:
            raise ValidationError(
                error_code=ValidationErrorCodes.INVALID_DOCUMENT,
                message=(
                    'Se especifico que la condicion de venta para este documento'
                    ' es "{}" ({}), pero, no se indicó un plazo válido.\nPlazo: "{}"'
                ).format('Credito', sale_condition, term_days)
            )

        body_data['due_date'] = (issued_date + timedelta(
            days=int(term_days)
        )).strftime(DATETIME_DISPLAY_FORMAT)
        body_data['credit_term'] = term_days

    details = data['detalles']
    exemptions = {}
    for line in details:
        for tax in line.get('impuesto', []):
            exemption = tax.get('exoneracion')
            if not exemption:
                continue

            ex_doc_num = exemption['NumeroDocumento']
            if ex_doc_num not in exemptions:
                exemptions[ex_doc_num] = {
                    'doc_type': fe_enums.ExemptionDocType[
                        exemption['Tipodocumento']
                    ],
                    'doc_number': exemption['NumeroDocumento'],
                    'issuer': exemption['NombreInstitucion'],
                    'issued_date': parse_datetime(
                        exemption['FechaEmision'], 'exoneracion => FechaEmision'
                    ).isoformat(),
                    'percentage': exemption['porcentajeExoneracion']
                }
            elif Decimal(exemptions[ex_doc_num]['percentage']) < Decimal(exemption['porcentajeExoneracion']):
                exemptions[ex_doc_num]['percentage'] = exemption['porcentajeExoneracion']

    if exemptions:
        body_data['exemption'] = {
            'items': tuple(exemptions.values()),
            'total_exempt': data['totalExonerado']
        }

    ref = arrange_pdf_reference(data.get('referencia', []))
    if ref:
        body_data['references'] = ref

    return body_data


def arrange_pdf_reference(data):
    if not data or isinstance(data, str):
        return None

    data_references = data.copy()
    if isinstance(data_references, dict):
        data_references = [data_references]

    references = []
    for data_ref in data_references:
        ref_doc_type_desc = fe_enums.REFERENCE_DOCUMENT_TYPE.get(
            data_ref['tipoDocumento'],
            'Indefinido ({})'.format(data_ref['tipoDocumento'])
        )

        ref = {
            'type': ref_doc_type_desc,
            'date': data_ref['fecha']
        }
        if 'numeroReferencia' in data_ref:
            ref['number'] = data_ref['numeroReferencia']
        if 'codigo' in data_ref:
            ref_code_desc = fe_enums.REFERENCE_CODE.get(
                data_ref['codigo'],
                'Indefinido ({})'.format(data_ref['codigo'])
            )
            ref['code'] = ref_code_desc
        if 'razon' in data_ref:
            ref['reason'] = data_ref['razon']

        references.append(ref)

    return references


def build_pdf_header_data(data: dict) -> dict:
    header_data = {}

    api_doc_type = fe_enums.TipoDocumentoApi[data['tipo']]
    header_data['document_type'] = fe_enums.tagNamePDF.get(
        api_doc_type, 'Indefinido'
    )
    issuer = data['issuer']
    header_data['type_iden_issuer'] = fe_enums.tipoCedulaPDF.get(
        issuer.get('idn_type'),
        'Tipo de identificación no especificada'
    )
    if 'company_user' in issuer:
        logo = companies_dao.get_logo_data(issuer['company_user'])['logo']
        if logo is not None:
            header_data['logo'] = logo.decode('utf-8')

    header_data['issuer'] = issuer
    header_data['consecutive'] = data['consecutivo']
    header_data['ref_num'] = data['numReferencia']
    if 'numReferencia2' in data:
        header_data['ref_num2'] = data['numReferencia2']
    header_data['date'] = parse_datetime(
        data['fechafactura'], 'fechafactura'
    ).strftime(DATETIME_DISPLAY_FORMAT)

    return header_data


def build_pdf_footer_data(data: dict) -> dict:
    currency = data['codigoTipoMoneda']

    footer_data = {}

    pdf_notes = data.get('notas',
                         data.get('observaciones',
                                  data.get('piedepagina', [])
                                  )
                         )
    if not isinstance(pdf_notes, list):
        pdf_notes = []

    if data['condicionVenta'] == CREDIT_CONDITION_CODE \
            and currency['tipoMoneda'] != LOCAL_CURRENCY:
        pdf_notes.insert(0,
                         CREDIT_CURRENCY_EXCHANGE_POLICY)

    # footer_data['email'] = data['issuer'].get('email', '')  # jic
    footer_data['notes'] = pdf_notes
    return footer_data


def parse_datetime(value, field) -> datetime:
    if isinstance(value, datetime):
        return value

    try:
        parsed = default_tzinfo(
            parser.parse(value, dayfirst=True), TZ_CR
        )
    except ValueError as ver:
        raise ValidationError(
            value, field,
            error_code=ValidationErrorCodes.INVALID_DATETIME_FORMAT
        ) from ver
    else:
        return parsed


def generates_pdf(data: dict) -> bool:
    doctype = data['tipo']
    if doctype in NO_PDF_TYPES:
        return False

    if doctype in CONDITIONAL_PDF_TYPES.keys():
        return CONDITIONAL_PDF_TYPES[doctype](data)

    return 'receptor' in data


def references_fe(data: dict) -> bool:
    ref = data.get('referencia')
    if isinstance(ref, str) or ref is None:
        return False

    if not isinstance(ref, (dict, list)):  # jic
        raise ValidationError(
            error_code=ValidationErrorCodes.INVALID_DOCUMENT,
            message=('La propiedad "referencia" posee un valor de tipo inválido.'
                     ' Tipo recibido: {} . Tipo esperado: object').format(type(ref))
        )

    if isinstance(ref, list):
        if len(ref):
            ref = ref[0]
        else:
            return False

    doctype = ref.get('tipoDocumento', '').strip()
    if not doctype:
        raise ValidationError(
            error_code=ValidationErrorCodes.INVALID_DOCUMENT,
            message=('La referencia recibida no posee un tipo de documento asociado válido. '
                     'Valor de "tipoDocumento": {}'.format(doctype))
        )

    return doctype == fe_enums.TipoDocumento['FE']


CONDITIONAL_PDF_TYPES = {
    fe_enums.TipoDocumentApiSwapped['ND']: references_fe,
    fe_enums.TipoDocumentApiSwapped['NC']: references_fe
}
