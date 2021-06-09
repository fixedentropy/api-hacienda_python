from helpers.errors.enums import DBErrorCodes
from helpers.errors.exceptions import DatabaseError
from infrastructure import dbadapter as dba


# autoinc table; returns last id
def save_document(company_id, key_mh, sign_xml, status, date, document_type,
                  receiver, total_document, total_taxed, pdf, email, email_costs):
    receiver_type = None
    receiver_dni = None
    if receiver is not None:
        receiver_type = receiver.get('tipoIdentificacion')
        receiver_dni = receiver.get('numeroIdentificacion')

    procedure = 'sp_saveDocument'
    args = (company_id, key_mh, sign_xml, status, date, document_type,
            receiver_type, receiver_dni, total_document, total_taxed, pdf, email,
            email_costs)

    try:
        return dba.execute_proc(proc_name=procedure, args=args, assert_unique=True)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_DOCUMENT_CREATE
        ) from dbae


def save_document_line_info(company_id, doc_id, line_number, quantity, unity,
                            detail, unit_price, net_tax, total_line):
    procedure = 'sp_createDocumentLineInfo'
    args = (company_id, doc_id, line_number, quantity, unity, detail, unit_price,
            net_tax, total_line)
    try:
        return dba.execute_proc(proc_name=procedure, args=args, assert_unique=True)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(dbae.get_message(),
                            error_code=DBErrorCodes.DB_DOCUMENT_DETAIL_LINE_CREATE) from dbae


def save_document_line_taxes(doc_id, line_id, rate_code, code,
                             rate, amount):
    procedure = 'sp_createDocumentTaxInfo'
    args = (doc_id, line_id, rate_code, code, rate, amount)
    try:
        return dba.execute_proc(proc_name=procedure, args=args, assert_unique=True)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(dbae.get_message(),
                            error_code=DBErrorCodes.DB_DOCUMENT_LINE_TAX_CREATE) from dbae


def save_document_additional_email(doc_id, email):
    procedure = 'usp_insert_documentxemail'
    args = (doc_id, email)
    try:
        dba.execute_proc(proc_name=procedure, args=args, assert_unique=True)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(dbae.get_message(),
                            error_code=DBErrorCodes.DB_DOCUMENT_ADDITIONAL_EMAIL_CREATE) from dbae

    return True


def update_document(company_id, key_mh, answer_xml, status, date):
    procedure = 'sp_updateDocument'
    args = (company_id, key_mh, answer_xml, status, date)
    try:
        dba.execute_proc(proc_name=procedure, args=args,
                         assert_unique=True)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(dbae.get_message(),
                            error_code=DBErrorCodes.DB_DOCUMENT_UPDATE) from dbae

    return True


def update_is_sent(doc_id, is_sent):
    procedure = 'usp_updateIsSent_documents'
    args = (doc_id, is_sent)
    try:
        dba.execute_proc(proc_name=procedure, args=args,
                         assert_unique=True)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(dbae.get_message(),
                            error_code=DBErrorCodes.DB_DOCUMENT_UPDATE_ISSENT
                            ) from dbae


def get_document(company_id, key_mh):
    procedure = 'sp_getDocumentByKey'
    args = (company_id, key_mh)
    try:
        return dba.fetchone_from_proc(procname=procedure, args=args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_DOCUMENT_SELECT_ONE) from dbae


def get_documents_company(company_id, state):  # MFD
    procedure = 'sp_getDocumentByCompany'
    args = (company_id, state)
    return dba.fetchall_from_proc(procname=procedure, args=args)


def get_documents(state, env):
    if state == 0:
        procedure = 'sp_getDocumentsValidate'
    else:
        procedure = 'sp_getDocumentsConsult'

    try:
        return dba.fetchall_from_proc(procname=procedure, args=(env,))
    except dba.DbAdapterError as dbae:
        raise DatabaseError(procedure,
                            error_code=DBErrorCodes.DB_DOCUMENT_JOBS) from dbae


def get_documentsreport(company_id, document_type):
    procedure = 'sp_getDocumentsReport'
    args = (company_id, document_type)
    try:
        return dba.fetchall_from_proc(procname=procedure, args=args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_DOCUMENT_SELECT_BY_COMPANY_AND_TYPE) from dbae


def get_additional_emails(doc_id):
    procedure = 'usp_selectByDocKey_documentxemail'
    args = (doc_id,)
    try:
        return dba.fetchall_from_proc(procname=procedure, args=args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_DOCUMENT_SELECT_ADDITIONAL_EMAILS_BY_KEY) from dbae


def verify_exists(company_id, key_mh):
    procedure = 'usp_verifyExists_documents'
    args = (company_id, key_mh)
    try:
        result = dba.fetchone_from_proc(procname=procedure, args=args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_DOCUMENT_VERIFY) from dbae

    return result is not None
