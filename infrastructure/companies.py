from helpers.errors.enums import DBErrorCodes
from helpers.errors.exceptions import DatabaseError
from infrastructure import dbadapter as dba


def create_company(company_user, name, tradename, type_identification, dni,
                   state, county, district, neighbor, address, phone_code, phone,
                   email, activity_code, is_active, pdf_exchangerate, user_mh,
                   pass_mh, signature, logo, pin_sig, env, expiration_date):
    comp_proc = 'sp_createCompany'
    comp_args = (company_user, name, tradename, type_identification, dni, state,
                 county, district, neighbor, address, phone_code, phone, email,
                 activity_code, is_active, pdf_exchangerate)
    try:
        dba.execute_proc(proc_name=comp_proc, args=comp_args, assert_unique=True)

    except dba.DbAdapterError as dbae:
        raise DatabaseError(dbae.get_message(),
                            error_code=DBErrorCodes.DB_COMPANY_CREATE) from dbae

    mh_proc = 'sp_saveMHInfo'
    mh_args = (user_mh, pass_mh, signature, logo, pin_sig, company_user, env,
               expiration_date)
    try:
        dba.execute_proc(proc_name=mh_proc, args=mh_args, assert_unique=True)

    except dba.DbAdapterError as dbae:
        raise DatabaseError(dbae.get_message(),
                            error_code=DBErrorCodes.DB_COMPANY_CREATE_MH) from dbae

    return True


def modify_company(company_user, name, tradename, type_identification, dni,
                   state, county, district, neighbor, address, phone_code, phone,
                   email, activity_code, is_active, pdf_exchangerate, user_mh,
                   pass_mh, signature, logo, pin_sig, env, expiration_date):
    comp_proc = 'sp_ModifyCompany'
    comp_args = (company_user, name, tradename, type_identification, dni, state,
                 county, district, neighbor, address, phone_code, phone, email,
                 activity_code, is_active, pdf_exchangerate)
    try:
        dba.execute_proc(proc_name=comp_proc, args=comp_args, assert_unique=True)

    except dba.DbAdapterError as dbae:
        raise DatabaseError(dbae.get_message(),
                            error_code=DBErrorCodes.DB_COMPANY_UPDATE) from dbae

    # in case the mh_info is missing for a company, we should be able to add new info to it.
    # consider changing this procedure to one less intensive.
    try:
        mh_info = dba.fetchone_from_proc('sp_getMHInfo', (company_user,))
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_COMPANY_UPDATE_MH,
                            message="A problem occurred in the database and the company couldn't be updated.")\
            from dbae
    if not mh_info:  # if no info, add new info
        mh_proc = 'sp_saveMHInfo'
    else:  # else, update it
        mh_proc = 'sp_modifyMHInfo'

    mh_args = (user_mh, pass_mh, signature, logo, pin_sig, company_user, env,
               expiration_date)
    try:
        dba.execute_proc(proc_name=mh_proc, args=mh_args, assert_unique=True)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(dbae.get_message(),
                            error_code=DBErrorCodes.DB_COMPANY_UPDATE_MH) from dbae

    return True


def delete_company_data(company_user):
    procedure = 'sp_deleteCompany'
    args = (company_user,)
    try:
        dba.execute_proc(proc_name=procedure, args=args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(dbae.get_message(),
                            error_code=DBErrorCodes.DB_COMPANY_DELETE) from dbae

    return True


def get_company_data(company_user):
    procedure = 'sp_getCompanyInfo'
    args = (company_user,)
    try:
        return dba.fetchone_from_proc(procname=procedure, args=args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_COMPANY_SELECT_ONE) from dbae


def get_companies():
    procedure = 'sp_getCompanies'
    try:
        return dba.fetchall_from_proc(procname=procedure)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_COMPANY_SELECT_ALL) from dbae


def get_sign_data(company_user):
    procedure = 'sp_getSignCompany'
    args = (company_user,)
    try:
        return dba.fetchone_from_proc(procname=procedure, args=args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_COMPANY_SIGNATURE) from dbae


def get_logo_data(company_user):
    procedure = 'sp_getLogoCompany'
    args = (company_user,)
    try:
        return dba.fetchone_from_proc(procname=procedure, args=args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_COMPANY_LOGO) from dbae


def verify_company(company_user):
    procedure = 'sp_getCompanyInfo'
    args = (company_user,)
    try:
        company = dba.fetchone_from_proc(procname=procedure, args=args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_COMPANY_VERIFY) from dbae

    if not company:
        result = False
    else:
        result = True

    return result


def update_state(company_id, new_state):
    procedure = 'USP_UpdateCompanyState'
    args = (company_id, new_state)
    try:
        dba.execute_proc(procedure, args, assert_unique=True)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(error_code=DBErrorCodes.DB_COMPANY_UPDATE) from dbae

    return True


def get_companys_documents_by_type(company_id, doc_type, return_files: bool):
    procedure = 'usp_getCompanysDocumentsByType'
    args = (company_id, doc_type, return_files)
    try:
        return dba.fetchall_from_proc(procedure, args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            error_code=DBErrorCodes.DB_COMPANY_SELECT_DOCS_BY_TYPE
        ) from dbae


def get_messages(company_id, return_files: bool):
    procedure = 'usp_getCompanysMessages'
    args = (company_id, return_files)
    try:
        return dba.fetchall_from_proc(procedure, args)
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            error_code=DBErrorCodes.DB_COMPANY_SELECT_MESSAGES
        ) from dbae
