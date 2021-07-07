import sys
import json
import base64
import datetime
import os.path

from lxml import etree

import app
from infrastructure import companies as dao_companies
from infrastructure import documents as dao_documents
from infrastructure.dbadapter import commit as db_commit


XML_FILE_FORMAT = '{resource_url}/{doc_key}.xml'
PDF_FILE_FORMAT = '{resource_url}/{doc_key}.pdf'


# console progress bar util
def progress_bar(iterable, prefix='', suffix='', decimals=1, length=100, fill='█', print_end="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        print_end    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)

    # Progress Bar Printing Function
    def print_progress_bar (iteration):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filled_length = int(length * iteration // total)
        bar = fill * filled_length + '-' * (length - filled_length)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=print_end)
    # Initial Call
    print_progress_bar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        print_progress_bar(i + 1)
    # Print New Line on Complete
    print()


def do_exit(msg):
    print(msg)
    sys.exit()


def parse_documents_json(d_json):
    if not d_json:
        do_exit('No documents json file specified')

    with open(d_json) as json_file:
        docs = json.load(json_file)

    if not docs:
        do_exit('Documents was empty')

    return docs


def parse_xml_file_from_url(signed_url, xml_url):
    parsed = None
    try:
        parsed = etree.parse(signed_url)
    except Exception:
        try:
            parsed = etree.parse(xml_url)
        except Exception as ex:
            print('Something went wrong: {} => {}'.format(
                signed_url + '(/)' + xml_url, str(ex)
            ))
    return parsed


def parse_pdf_file_from_url(url):
    parsed = None
    try:
        with open(url, 'rb') as pdf_data:
            parsed = pdf_data.read()
    except Exception as ex:
        print('Something went wrong: {} => {}'.format(
            url, str(ex)
        ))
    return parsed


def parse_answer_file_from_url(url):
    parsed = None
    try:
        parsed = etree.parse(url)
    except Exception as ex:
        print('Something went wrong: {} => {}'.format(
            url, str(ex)
        ))
    return parsed


def parse_doc_type(etree_xml_file):
    tag_name = etree.QName(etree_xml_file.getroot().tag).localname
    if tag_name == 'NotaCreditoElectronica':
        return 'NC'
    elif tag_name == 'NotaDebitoElectronica':
        return 'ND'
    elif tag_name == 'TiqueteElectronico':
        return 'TE'
    elif tag_name == 'FacturaElectronicaCompra':
        return 'FEC'
    elif tag_name == 'FacturaElectronicaExportacion':
        return 'FEE'
    else:
        return 'FE'


def parse_idn(etree_xml_file):
    el_recipient = etree_xml_file.find('{*}Receptor')
    if el_recipient is None:
        return None, None

    el_idn = el_recipient.find('{*}Identificacion')
    if el_idn is None:
        return None, None

    idn_type = el_idn.findtext('{*}Tipo')
    idn_number = el_idn.findtext('{*}Numero')
    return idn_type, idn_number


def parse_document_summary(etree_xml_file):
    el_summary = etree_xml_file.find('{*}ResumenFactura')
    if el_summary is not None:
        doc_total_text = el_summary.findtext('{*}TotalComprobante')
        doc_taxes_text = el_summary.findtext('{*}TotalImpuesto')
        return doc_total_text, doc_taxes_text
    else:
        return None, None


# prep done, doing stuff
with app.app.app.app_context():
    company_user = sys.argv[1]
    company = dao_companies.get_company_data(company_user)
    if not company:
        do_exit('Company not found: {}'.format(company_user))
    company_id = company['id']

    documents_json = sys.argv[2]
    importable_docs = parse_documents_json(documents_json)

    local_url = sys.argv[3]
    if not local_url:
        do_exit('No file directory specified.')

    if not os.path.isdir(local_url):
        do_exit('No directory {} found.'.format(local_url))

    xml_dir = '{base_dir}/xml'.format(base_dir=local_url)
    signed_dir = '{base_dir}/firmado'.format(base_dir=local_url)
    pdf_dir = '{base_dir}/facturas'.format(base_dir=local_url)
    answer_dir = '{base_dir}/respuesta'.format(base_dir=local_url)

    for doc in progress_bar(importable_docs, prefix='Progress:', suffix='Complete', length=50):
        doc_key = doc['clave']
        if len(doc_key) != 50:
            print(
                'Document "{}" has wrong key length: {}'.format(doc_key, len(doc_key))
            )
            continue
        if dao_documents.verify_exists(company_id, doc_key):
            print(
                'Document "{}" already registered in database'.format(doc_key)
            )
            continue

        doc_user = doc['usuario']
        xml_file = parse_xml_file_from_url(
            XML_FILE_FORMAT.format(resource_url=signed_dir, doc_key=doc_key),
            XML_FILE_FORMAT.format(resource_url=xml_dir, doc_key=doc_key)
        )
        pdf_file = parse_pdf_file_from_url(
            PDF_FILE_FORMAT.format(resource_url=pdf_dir, doc_key=doc_key)
        )
        answer_file = parse_answer_file_from_url(
            XML_FILE_FORMAT.format(resource_url=answer_dir, doc_key=doc_key)
        )
        doc_status = doc['estado']
        doc_type = 'FE'
        doc_idn_type = None
        doc_dni = None
        doc_total = None
        doc_taxes = None
        doc_email = doc['correo_enviar']
        doc_date = datetime.datetime.strptime(doc['fecha'], '%Y-%m-%d')
        if xml_file is not None:
            xml_date = xml_file.find('{*}FechaEmision')
            if xml_date is not None:
                try:
                    doc_date = datetime.datetime.fromisoformat(
                        xml_date.text
                    )
                except Exception:
                    pass
            doc_type = parse_doc_type(xml_file)
            doc_idn_type, doc_dni = parse_idn(xml_file)
            doc_total, doc_taxes = parse_document_summary(xml_file)

        additional_emails = []
        if doc['correo_gastos']:
            additional_emails.append(doc['correo_gastos'])
        if doc['correo_copia']:
            additional_emails.append(doc['correo_copia'])

        save_document_args = (
            company_id,
            doc_key,
            base64.b64encode(
                etree.tostring(
                    xml_file, encoding='UTF-8'
                )
            ) if xml_file is not None else None,
            doc_status,
            doc_date,
            doc_type,
            {
                'tipoIdentificacion': doc_idn_type,
                'numeroIdentificacion': doc_dni
            },
            doc_total,
            doc_taxes,
            base64.b64encode(pdf_file) if pdf_file is not None else None,
            doc_email,
            None
        )
        document_id = dao_documents.save_document(*save_document_args)
        if additional_emails:
            additional_emails = list(set(additional_emails))
            for e in additional_emails:
                dao_documents.save_document_additional_email(document_id, e)

        update_document_args = (
            document_id,
            base64.b64encode(
                etree.tostring(
                    answer_file, encoding='UTF-8'
                )
            ) if answer_file is not None else None,
            doc_status,
            doc_date
        )
        dao_documents.update_document_2(*update_document_args)
        dao_documents.update_is_sent(document_id, 0)

        db_commit()
