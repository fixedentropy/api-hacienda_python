import typing as t

from helpers.errors.enums import DBErrorCodes
from helpers.errors.exceptions import DatabaseError
from infrastructure import dbadapter as dba


def insert_template(id_template_type: int, id_company: int, data: str) -> bool:
    procedure = 'usp_template_insert'
    args = (id_template_type, id_company, data)
    try:
        dba.execute_proc(
            proc_name=procedure, args=args, assert_unique=True
        )
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_TEMPLATE_INSERT
        ) from dbae

    return True


def update_template_by_id(
        id_template: int, id_template_type: int, id_company: int, data: str
) -> bool:
    procedure = 'usp_template_updateById'
    args = (id_template, id_template_type, id_company, data)
    try:
        dba.execute_proc(
            proc_name=procedure, args=args, assert_unique=True
        )
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_TEMPLATE_UPDATE_BY_ID
        ) from dbae

    return True


def delete_template_by_id(id_template: int) -> bool:
    procedure = 'usp_template_deleteById'
    args = (id_template,)
    try:
        dba.execute_proc(
            proc_name=procedure,
            args=args,
            assert_unique=True
        )
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_TEMPLATE_DELETE_BY_ID
        ) from dbae

    return True


def select_common_templates(id_template_type: int = None) -> t.Union[t.List[dict], dict, None]:
    procedure = 'usp_template_selectCommon'
    args = (id_template_type,)
    try:
        if id_template_type is None:
            return dba.fetchall_from_proc(
                procname=procedure,
                args=args
            )

        result = dba.fetchone_from_proc(
            procname=procedure,
            args=args
        )
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_TEMPLATE_SELECT_COMMON
        ) from dbae

    return result['data'] if result is not None else None


def select_template_by_id(id_template: int) -> t.Union[dict, None]:
    procedure = 'usp_template_selectById'
    args = (id_template,)
    try:
        return dba.fetchone_from_proc(
            procname=procedure,
            args=args
        )
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_TEMPLATE_SELECT_BY_ID
        ) from dbae


def select_unique_template(id_template_type: int, id_company: int) -> t.Union[dict, None]:
    procedure = 'usp_template_selectByUQ_Template'
    args = (id_template_type, id_company)
    try:
        result = dba.fetchone_from_proc(
            procname=procedure,
            args=args
        )
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_TEMPLATE_SELECT_BY_UQ_TEMPLATE
        ) from dbae

    return result['data'] if result is not None else None


def select_template_by_type(id_template_type: int) -> t.List[dict]:
    procedure = 'usp_template_selectByTemplateType'
    args = (id_template_type,)
    try:
        return dba.fetchall_from_proc(
            procname=procedure,
            args=args
        )
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_TEMPLATE_SELECT_BY_TYPE
        ) from dbae


def select_template_by_company(id_company: int) -> t.List[dict]:
    procedure = 'usp_template_selectByCompany'
    args = (id_company,)
    try:
        return dba.fetchall_from_proc(
            procname=procedure,
            args=args
        )
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_TEMPLATE_SELECT_BY_COMPANY
        ) from dbae


def get_data_by_id(id_template: int) -> t.Union[str, None]:
    procedure = 'usp_template_getData'
    args = (id_template,)
    try:
        result = dba.fetchone_from_proc(
            procname=procedure,
            args=args
        )
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_TEMPLATE_GET_DATA
        ) from dbae

    return result['data'] if result is not None else None
