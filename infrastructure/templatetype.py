import typing

from infrastructure import dbadapter as dba
from helpers.errors.enums import DBErrorCodes
from helpers.errors.exceptions import DatabaseError


def save_template_type(description: str, connection=None) -> bool:
    procedure = 'usp_templatetype_insert'
    args = (description,)
    try:
        dba.execute_proc(
            proc_name=procedure,
            args=args,
            conn=connection,
            assert_unique=True
        )
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_TEMPLATE_TYPE_INSERT
        ) from dbae

    return True


def update_template_type(tmplt_type_id: int,
                         description: str, connection=None) -> bool:
    procedure = 'usp_templatetype_update'
    args = (tmplt_type_id, description)
    try:
        dba.execute_proc(
            proc_name=procedure,
            args=args,
            conn=connection,
            assert_unique=True
        )
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_TEMPLATE_TYPE_UPDATE_BY_ID
        ) from dbae

    return True


def select_all() -> typing.List[dict]:
    procedure = 'usp_templatetype_selectAll'
    try:
        return dba.fetchone_from_proc(
            procname=procedure
        )
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_TEMPLATE_TYPE_SELECT_ALL
        ) from dbae


def select_by_id(tmplt_type_id: int) -> typing.Union[dict, None]:
    procedure = 'usp_templatetype_selectById'
    args = (tmplt_type_id,)
    try:
        return dba.fetchone_from_proc(
            procname=procedure,
            args=args
        )
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_TEMPLATE_TYPE_SELECT_BY_ID
        ) from dbae


def select_by_description(description: str) -> typing.Union[dict, None]:
    procedure = 'usp_templatetype_selectByDescription'
    args = (description,)
    try:
        return dba.fetchone_from_proc(
            procname=procedure,
            args=args
        )
    except dba.DbAdapterError as dbae:
        raise DatabaseError(
            dbae.get_message(),
            error_code=DBErrorCodes.DB_TEMPLATE_TYPE_SELECT_BY_ID
        ) from dbae
