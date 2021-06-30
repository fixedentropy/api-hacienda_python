from datetime import datetime

from helpers.entities.messages import RecipientMessage
from helpers.errors.enums import DBErrorCodes
from helpers.errors.exceptions import DatabaseError
from infrastructure import dbadapter as dba


def insert(company_id: int, message: RecipientMessage,
           issue_date: datetime, encoded_xml: bytes, status: str,
           issuer_email: str = None):
    procedure = 'usp_insert_message'
    args = (company_id, message.key, message.issuerIDN.number,
            message.issuerIDN.type, issue_date,
            message.code, message.recipientIDN.number,
            message.recipientSequenceNumber, encoded_xml, status,
            issuer_email)

    try:
        dba.execute_proc(proc_name=procedure, args=args, assert_unique=True)

    except dba.DbAdapterError as dbae:
        raise DatabaseError(dbae.get_message(),
                            error_code=DBErrorCodes.DB_MESSAGE_CREATE) from dbae

    return True


def update_from_answer(company_id: int, message_key: str,
                       message_rec_seq_num: str, status: str, answer_date: str = None,
                       encoded_answer_xml: bytes = None):
    procedure = 'usp_updateFromAnswer_message'
    args = (company_id, message_key, message_rec_seq_num,
            encoded_answer_xml, status, answer_date)

    try:
        dba.execute_proc(proc_name=procedure, args=args, assert_unique=True)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(dbae.get_message(),
                            error_code=DBErrorCodes.DB_MESSAGE_UPDATE_ANSWER) from dbae

    return True


def update_email_sent(company_id: int, message_key: str,
                      message_rec_seq_num: str, email_sent: int):
    procedure = 'usp_updateEmailSent_message'
    args = (company_id, message_key, message_rec_seq_num, email_sent)

    try:
        dba.execute_proc(proc_name=procedure, args=args, assert_unique=True)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(dbae.get_message(),
                            error_code=DBErrorCodes.DB_MESSAGE_UPDATE_EMAILSENT
                            ) from dbae


def select(company_id: int, key_mh: str, rec_seq_num: str):
    procedure = 'usp_select_message'
    args = (company_id, key_mh, rec_seq_num)
    try:
        return dba.fetchone_from_proc(procname=procedure, args=args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_MESSAGE_SELECT_ONE) from dbae


def select_by_company(company_id: int,  with_files: bool, since: datetime,
                      until: datetime):
    procedure = 'usp_getCompanysMessages'
    args = (company_id, with_files, since, until)
    try:
        return dba.fetchall_from_proc(procname=procedure, args=args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            error_code=DBErrorCodes.DB_MESSAGE_SELECT_BY_COMPANY
        ) from dbae


def select_by_status(status: int, company_id: str = None,
                     company_is_active: bool = None, env: str = 'api-stag', limit: int = 20):
    procedure = 'usp_selectByStatus_message'
    args = (status, company_id, company_is_active, env, limit)
    try:
        return dba.fetchall_from_proc(procname=procedure, args=args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_MESSAGE_SELECT_BY_STATUS) from dbae


def select_by_code(code: int, company_id: str = None, limit: int = None):
    procedure = 'usp_selectByCode_message'
    args = (code, company_id, limit)
    try:
        return dba.fetchall_from_proc(procname=procedure, args=args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_MESSAGE_SELECT_BY_CODE) from dbae


def select_by_issuer_idn(issuer_idn: str, company_id: int = None,
                         limit: int = None):
    procedure = 'usp_selectByIssuerIDN_message'
    args = (issuer_idn, company_id, limit)
    try:
        return dba.fetchall_from_proc(procname=procedure, args=args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_MESSAGE_SELECT_BY_ISSUER_IDN) from dbae
