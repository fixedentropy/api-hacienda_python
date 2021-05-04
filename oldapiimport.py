import sys
import json
import base64
import datetime
import yaml
import time

import pymysql
import requests
from lxml import etree


# console progress bar util
def progressBar(iterable, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
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
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)
    # Progress Bar Printing Function
    def printProgressBar (iteration):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()


def do_exit(msg):
    print(msg)
    sys.exit()


with open("config.yaml", 'r') as ymlfile:
    cfg = yaml.safe_load(ymlfile)

mysql_config = cfg['mysql']
connection = pymysql.connect(
    host=mysql_config['host'],
    user=mysql_config['user'],
    password=mysql_config['passwd'],
    database=mysql_config['db'],
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)


with connection:
    def verify_company_id(c_id):
        if not c_id:
            do_exit('No company id specified')

        with connection.cursor() as cur:
            cur.callproc('sp_getCompanyInfo', (c_id,))
            if cur.fetchone() is None:
                do_exit("Company ID {} not found in the database.".format(c_id))


    def parse_documents_json(d_json):
        if not d_json:
            do_exit('No documents json file specified')

        with open(d_json) as json_file:
            docs = json.load(json_file)

        if not docs:
            do_exit('Documents was empty')

        return docs


    def is_document_registered(document_key):
        with connection.cursor() as cur:
            cur.callproc('usp_verifyExists_documents', (document_key,))
            return cur.fetchone() is not None


    company_id = sys.argv[1]
    verify_company_id(company_id)

    documents_json = sys.argv[2]
    documents = parse_documents_json(documents_json)

    base_url = 'http://35.170.39.96/assets'
    xml_url = '{base_url}/xml'.format(base_url=base_url)
    signed_url = '{base_url}/firmado'.format(base_url=base_url)
    xml_file_format = '{resource_url}/{doc_key}.xml'


    def parse_xml_file_from_url(c_id, document_key):
        parsed = None
        doc_xml_file_url = xml_file_format.format(
            resource_url='{signed_url}/{company_id}'.format(
                signed_url=signed_url, company_id=c_id
            ),
            doc_key=document_key
        )
        try:
            parsed = etree.parse(doc_xml_file_url)
        except Exception:
            doc_xml_file_url = xml_file_format.format(
                resource_url='{xml_url}/{company_id}'.format(
                    xml_url=xml_url, company_id=c_id
                ),
                doc_key=document_key
            )
            try:
                parsed = etree.parse(doc_xml_file_url)
            except Exception as ex:
                print('Something went wrong: {} => {}'.format(
                    document_key, str(ex)
                ))
        return parsed


    pdf_url = '{base_url}/facturas'.format(base_url=base_url)


    def parse_pdf_file_from_url(c_id, document_key):
        parsed = None
        doc_pdf_file_url = '{resource_url}/{doc_key}.pdf'.format(
            resource_url='{pdf_url}/{company_id}'.format(
                pdf_url=pdf_url, company_id=c_id
            ),
            doc_key=document_key
        )
        pdf_response = requests.get(doc_pdf_file_url)
        if pdf_response.status_code == 200:
            parsed = pdf_response.text
        return parsed


    answer_url = '{base_url}/respuesta'.format(base_url=base_url)


    def parse_answer_file_from_url(c_id, document_key):
        parsed = None
        doc_xml_file_url = xml_file_format.format(
            resource_url='{answer_url}/{company_id}'.format(
                answer_url=answer_url, company_id=c_id
            ),
            doc_key=document_key
        )
        try:
            parsed = etree.parse(doc_xml_file_url)
        except Exception as ex:
            print('Something went wrong: {} => {}'.format(
                document_key, str(ex)
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


    def save_document(args):
        proc = 'sp_saveDocument'
        with connection.cursor() as cur:
            cur.callproc(proc, args)


    def update_document(args):
        proc = 'sp_updateDocument'
        with connection.cursor() as cur:
            cur.callproc(proc, args)


    def save_additional_emails(document_key, emails):
        proc = 'usp_insert_documentxemail'
        with connection.cursor() as cur:
            for e in emails:
                cur.callproc(proc, (document_key, e))


    for doc in progressBar(documents, prefix='Progress:', suffix='Complete', length=50):
        doc_key = doc['clave']
        if is_document_registered(doc_key):
            print(
                'Document {} already registered in database'.format(doc_key)
            )
            continue

        doc_user = doc['usuario']
        xml_file = parse_xml_file_from_url(doc_user, doc_key)
        pdf_file = parse_pdf_file_from_url(doc_user, doc_key)
        answer_file = parse_answer_file_from_url(doc_user, doc_key)
        doc_status = doc['estado']
        doc_type = 'FE'
        doc_idn_type = None
        doc_dni = None
        doc_total = None
        doc_taxes = None
        doc_email = doc['correo_enviar']
        if xml_file is not None:
            doc_date = datetime.datetime.fromisoformat(
                xml_file.find('{*}FechaEmision').text
            )
            doc_type = parse_doc_type(xml_file)
            doc_idn_type, doc_dni = parse_idn(xml_file)
            doc_total, doc_taxes = parse_document_summary(xml_file)
        else:
            doc_date = datetime.datetime.strptime(doc['fecha'], '%Y-%m-%d')

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
            doc_idn_type,
            doc_dni,
            doc_total,
            doc_taxes,
            base64.b64encode(pdf_file.encode('utf-8')) if pdf_file is not None else None,
            doc_email,
            None
        )
        save_document(save_document_args)

        update_document_args = (
            company_id,
            doc_key,
            base64.b64encode(
                etree.tostring(
                    answer_file, encoding='UTF-8'
                )
            ) if answer_file is not None else None,
            doc_status,
            doc_date
        )
        update_document(update_document_args)

        if additional_emails:
            additional_emails = list(set(additional_emails))
            save_additional_emails(doc_key, additional_emails)

        with connection.cursor() as upd_cur:
            upd_cur.execute('UPDATE documents SET isSent = 0 WHERE key_mh = %s', (doc_key,))

        connection.commit()

        time.sleep(0.1)
