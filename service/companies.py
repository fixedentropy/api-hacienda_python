import base64

from helpers.errors.enums import InputErrorCodes
from helpers.errors.exceptions import InputError
from helpers.utils import build_response_data
from infrastructure import companies
from infrastructure.dbadapter import commit as db_commit
from service import utils_mh


def create_company(data, files):
    # verify company first, 'cuz can't save a company that already exists.
    _company_user = data['id_compania']

    company_exists = companies.verify_company(
        _company_user
    )
    if company_exists:
        raise InputError('The company with ID: {}'
                         .format(_company_user),
                         error_code=InputErrorCodes.DUPLICATE_RECORD)

    signature = files['firma'].read()
    _pin = data['pin']
    _expiration_date = utils_mh.p12_expiration_date(
        signature, _pin
    )

    # get the company data
    _name = data['nombre_compania']
    _tradename = data['nombre_comercial']
    _type_identification = data['tipo_identificacion']
    _dni = data['cedula']
    _state = data['provincia']
    _county = data['canton']
    _district = data['distrito']
    _neighbor = data['barrio']
    _address = data['otras_senas']
    _phone_code = data['cod_telefono']
    _phone = data['telefono']
    _email = data['email']
    _activity_code = data['codigo_actividad']
    _user_mh = data['usuario_hacienda']
    _pass_mh = data['password_hacienda']
    _env = data['ambiente']
    _is_active = data['estado']
    _pdf_exchangerate = data['pdf_tipocambio']

    b64signature = base64.b64encode(signature)

    _logo = None
    if 'logo' in files:
        _logo = base64.b64encode(files['logo'].read())

    companies.create_company(
        _company_user, _name, _tradename, _type_identification, _dni, _state,
        _county, _district, _neighbor, _address, _phone_code, _phone, _email,
        _activity_code, _is_active, _pdf_exchangerate, _user_mh, _pass_mh,
        b64signature, _logo, _pin, _env, _expiration_date
    )
    db_commit()

    return build_response_data({'message': 'company created successfully!'})


def get_list_companies(id_company=0):
    if id_company == 0:
        result = {'data': {'companies': companies.get_companies()}}
    else:
        result = {'data': {'company': companies.get_company_data(id_company)}}

    return build_response_data(result)


def delete_company(id_company):
    companies.delete_company_data(id_company)
    db_commit()
    return build_response_data({'message': 'The company has been succesfully deleted.'})


def modify_company(data, files):
    _company_user = data['id_compania']
    company_exists = companies.verify_company(
        _company_user
    )
    if not company_exists:
        raise InputError('Company', _company_user,
                         error_code=InputErrorCodes.NO_RECORD_FOUND)

    signature = files['firma'].read()
    _pin = data['pin']
    _expiration_date = utils_mh.p12_expiration_date(
        signature, _pin
    )

    _name = data['nombre_compania']
    _tradename = data['nombre_comercial']
    _type_identification = data['tipo_identificacion']
    _dni = data['cedula']
    _state = data['provincia']
    _county = data['canton']
    _district = data['distrito']
    _neighbor = data['barrio']
    _address = data['otras_senas']
    _phone_code = data['cod_telefono']
    _phone = data['telefono']
    _email = data['email']
    _activity_code = data['codigo_actividad']
    _user_mh = data['usuario_hacienda']
    _pass_mh = data['password_hacienda']
    _env = data['ambiente']
    _is_active = data['estado']
    _pdf_exchange_rate = data['pdf_tipocambio']

    b64signature = base64.b64encode(signature)
    _logo = None
    if 'logo' in files:
        _logo = base64.b64encode(files['logo'].read())

    result = companies.modify_company(
        _company_user, _name, _tradename, _type_identification, _dni, _state,
        _county, _district, _neighbor, _address, _phone_code, _phone, _email,
        _activity_code, _is_active, _pdf_exchange_rate, _user_mh, _pass_mh,
        b64signature, _logo, _pin, _env, _expiration_date
    )
    db_commit()

    return build_response_data({'message': 'company modified successfully!'})


def patch_company(company_id, data, files):
    # not using files for now...
    # this be a catch all for updating stuff from the company...
    # but, for now, just updating state
    if 'estado' in data:
        state = data['estado']
        companies.update_state(company_id, state)
        db_commit()
        return build_response_data({
            'message': 'Company patch succesful',
            'data': {
                'state': state
            }
        })
    return build_response_data({
        'message': 'Invalid data received.',
        'http_status': 400,
        'error': {
            'message': 'No valid fields received in order to proceed with a patch.'
        }
    })
