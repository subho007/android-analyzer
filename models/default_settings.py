from settings import Certificate
from settings import ScenarioSettings
from settings import Settings


mitmproxy_ca_signed = Certificate(
    'Signed on-the-fly by unknown CA',
    '''
    This is a not expired, on-the-fly generated certificate with the right hostname.
    It is signed by the mitmproxy default certificate authority.
    ''')

other_hostname_self_signed = Certificate(
    'Self-signed with fixed hostname',
    '''
    This is a not expired certificate with a fixed hostname (*.mitmproxy.org).
    It is self signed.
    ''',
    custom_cert="mitmproxy/other_hostname_self_signed.pem")


default_certificates = [mitmproxy_ca_signed, other_hostname_self_signed]


mitmproxy_ca_signed_tm = ScenarioSettings(
    ['TrustManager'],
    mitmproxy_ca_signed,
    '''
    The app has a vulnerable TrustManager implementation and a man-in-the-middle attack with a certificate generated by a untrusted certificate authority (but otherwise valid) was possible.
    ''')

other_hostname_self_signed_hv = ScenarioSettings(
    ['HostnameVerifier'],
    other_hostname_self_signed,
    '''
    The app has a vulnerable HostnameVerifier implementation and a man-in-the-middle attack with a self signed certificate with another hostname (*.mitmproxy.org) was possible.
    ''')


default_scenarios = [mitmproxy_ca_signed_tm, other_hostname_self_signed_hv]

default_settings = Settings(default_scenarios)


# TODO: Many cases still to do:

mitmproxy_self_signed = Certificate(
    '',
    '''
    This is a not expired, on-the-fly generated certificate with the right hostname.
    It is self signed.
    ''')  # TODO: how to generate such certificates on the fly? search all https URLs in static analysis?

expired_ca_signed = Certificate(
    '',
    '''
    This is an expired, on-the-fly generated certificate with the right hostname.
    It is signed by a trusted certificate authority.
    ''')  # TODO: is this even possible??
expired_self_signed = Certificate(
    '',
    '''
    This is an expired, on-the-fly generated certificate with the right hostname.
    It is self signed.
    ''')  # TODO: how to generate such certificates on the fly? search all https URLs in static analysis?

other_hostname_ca_signed = Certificate(
    '',
    '''
    This is a not expired certificate with a fixed hostname (*.mitmproxy.org).
    It is signed by a trusted certificate authority.
    ''',
    custom_cert="mitmproxy/other_hostname_ca_signed.pem")  # TODO: how to get a certificate from a trusted CA?

other_hostname_ca_signed_expired = Certificate(
    '',
    '''
    This is an expired certificate with a fixed hostname (*.mitmproxy.org).
    It is signed by a trusted certificate authority.
    ''')  # TODO: how to get a certificate from a trusted CA
other_hostname_self_signed_expired = Certificate(
    '',
    '''
    This is an expired certificate with a fixed hostname (*.mitmproxy.org).
    It is self signed.
    ''',
    custom_cert="mitmproxy/other_hostname_self_signed_expired.pem")  # TODO: generate certificate with 1 day expiration?

# TODO: user installed certificates