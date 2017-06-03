from textwrap import dedent

from src.app import db
from src.models.certificate import Certificate
from src.models.scenario_settings import ScenarioSettings
from src.models.vuln_type import VulnType


def create_db():
    db.create_all()


def fill_db():
    _add_default_settings()


def drop_db():
    db.drop_all()


def _add_default_settings():
    mitmproxy_ca_signed = Certificate(
        name='Untrusted mitmproxy CA',
        description=dedent('''
        This is a not expired, on-the-fly generated certificate with the right hostname.
        It is signed by the mitmproxy default certificate authority.
        '''))

    other_hostname = Certificate(
        name='Untrusted CA 3 with fixed hostname',
        description=dedent('''
        This is a not expired certificate with a fixed hostname (*.mitmproxy.org).
        It is signed by the untrusted certificate authority 3.
        '''),
        custom_cert="default/cert1.pem")

    untrusted_ca = Certificate(
        name='Untrusted CA 1',
        description=dedent('''
        This is a not expired, on-the-fly generated certificate with the right hostname.
        It is signed by an untrusted certificate authority.
        '''),
        custom_ca="default/ca1.pem")

    untrusted_expired_ca = Certificate(
        name='Untrusted expired CA 2',
        description=dedent('''
        This is a not expired, on-the-fly generated certificate with the right hostname.
        It is signed by an expired and untrusted certificate authority.
        '''),
        custom_ca="default/expired_ca.pem")

    snd_untrusted_ca = Certificate(
        name='Untrusted CA 3',
        description=dedent('''
        This is a not expired, on-the-fly generated certificate with the right hostname.
        It is signed by an untrusted certificate authority.
        '''),
        custom_ca="default/ca3.pem")

    db.session.add(mitmproxy_ca_signed)
    db.session.add(other_hostname)
    db.session.add(untrusted_ca)
    db.session.add(untrusted_expired_ca)
    db.session.add(snd_untrusted_ca)

    db.session.flush()

    mitmproxy_ca_signed_tm = ScenarioSettings(
        name="TrustManager accepting untrusted CA",
        vuln_type=VulnType.trust_manager,
        mitm_certificate=mitmproxy_ca_signed,
        info_message='''The app has a vulnerable TrustManager implementation and a man-in-the-middle attack with a certificate generated by a untrusted certificate authority (but otherwise valid) was possible.''')

    expired_trusted_ca_tm = ScenarioSettings(
        name="TrustManager accepting expired CA",
        vuln_type=VulnType.trust_manager,
        mitm_certificate=untrusted_expired_ca,
        sys_certificates=[untrusted_expired_ca],
        info_message='''The app has a vulnerable TrustManager implementation and a man-in-the-middle attack with a certificate generated by a trusted but expired certificate authority was possible.''')

    # TODO: notyetvalid_ca_tm?
    # TODO: expired_trusted_cert_tm? how
    # TODO: notyetvalid_trusted_cert_tm? how?

    other_hostname_untrusted_hv = ScenarioSettings(
        name="HostnameVerifier accepting fixed hostname and untrusted CA",
        vuln_type=VulnType.hostname_verifier,
        mitm_certificate=other_hostname,
        info_message='''The app has a vulnerable HostnameVerifier implementation and a man-in-the-middle attack with a certificate with another hostname (*.mitmproxy.org), signed by an untrusted certificate authority was possible.''')

    other_hostname_trusted_hv = ScenarioSettings(
        name="HostnameVerifier accepting fixed hostname",
        vuln_type=VulnType.hostname_verifier,
        mitm_certificate=other_hostname,
        sys_certificates=[snd_untrusted_ca],
        info_message='''The app has a vulnerable HostnameVerifier implementation and a man-in-the-middle attack with a certificate with another hostname (*.mitmproxy.org), signed by a trusted certificate authority was possible.''')

    no_pinning_hv = ScenarioSettings(
        name="HostnameVerifier accepting fixed trusted CA (No pinning)",
        vuln_type=VulnType.hostname_verifier,
        mitm_certificate=untrusted_ca,
        sys_certificates=[untrusted_ca],
        info_message='''The app has a possibly vulnerable HostnameVerifier implementation and certificate pinning is not implemented (securely).''',
        strace=True)

    no_pinning_tm = ScenarioSettings(
        name="TrustManager accepting fixed trusted CA (No pinning)",
        vuln_type=VulnType.trust_manager,
        mitm_certificate=untrusted_ca,
        sys_certificates=[untrusted_ca],
        info_message='''The app has a vulnerable TrustManager implementation in which certificate pinning is not implemented (securely).''',
        strace=True)

    no_pinning_tm_added_upstream_certs = ScenarioSettings(
        name="TrustManager accepting peer certificates (No pinning)",
        vuln_type=VulnType.trust_manager,
        mitm_certificate=untrusted_ca,
        sys_certificates=[untrusted_ca],
        info_message='''The app has a vulnerable TrustManager implementation in which certificate pinning is not implemented (securely). If the other scenario with the same description is not vulnerable, then this is a getPeerCertificates() bug vulnerability.''',
        add_upstream_certs=True,
        strace=True)

    no_pinning_sa = ScenarioSettings(
        name="App accepting fixed trusted CA (No pinning)",
        vuln_type=VulnType.selected_activities,
        mitm_certificate=untrusted_ca,
        sys_certificates=[untrusted_ca],
        info_message='''The app has not implemented certificate pinning (securely).''',
        strace=True)

    no_pinning_sa_added_upstream_certs = ScenarioSettings(
        name="App accepting peer certificates (No pinning)",
        vuln_type=VulnType.selected_activities,
        mitm_certificate=untrusted_ca,
        sys_certificates=[untrusted_ca],
        info_message='''The app has not implemented certificate pinning (securely). If the other scenario with the same description is not vulnerable, then this is a getPeerCertificates() bug vulnerability.''',
        add_upstream_certs=True,
        strace=True)


    mitmproxy_ca_signed_wv = ScenarioSettings(
        name="WebViewClient accepting untrusted CA",
        vuln_type=VulnType.web_view_client,
        mitm_certificate=mitmproxy_ca_signed,
        info_message='''The app has a vulnerable WebViewClient implementation and a man-in-the-middle attack with a certificate generated by a untrusted certificate authority (but otherwise valid) was possible.''')

    expired_trusted_ca_wv = ScenarioSettings(
        name="WebViewClient accepting expired CA",
        vuln_type=VulnType.web_view_client,
        mitm_certificate=mitmproxy_ca_signed,
        sys_certificates=[mitmproxy_ca_signed],
        info_message='''The app has a vulnerable WebViewClient implementation and a man-in-the-middle attack with a certificate generated by a trusted but expired certificate authority was possible.''')

    other_hostname_untrusted_wv = ScenarioSettings(
        name="WebViewClient accepting fixed hostname and untrusted CA",
        vuln_type=VulnType.web_view_client,
        mitm_certificate=other_hostname,
        info_message='''The app has a vulnerable WebViewClient implementation and a man-in-the-middle attack with a certificate with another hostname (*.mitmproxy.org), signed by an untrusted certificate authority was possible.''')

    other_hostname_trusted_wv = ScenarioSettings(
        name="WebViewClient accepting fixed hostname",
        vuln_type=VulnType.web_view_client,
        mitm_certificate=other_hostname,
        sys_certificates=[snd_untrusted_ca],
        info_message='''The app has a vulnerable WebViewClient implementation and a man-in-the-middle attack with a certificate with another hostname (*.mitmproxy.org), signed by an untrusted certificate authority was possible.''')

    # TODO: notyetvalid_trusted_ca_wv?
    # TODO: expired_trusted_cert_wv? how?
    # TODO: notyetvalid_trusted_cert_wv? how?


    db.session.add(mitmproxy_ca_signed_tm)
    db.session.add(expired_trusted_ca_tm)
    db.session.add(other_hostname_untrusted_hv)
    db.session.add(other_hostname_trusted_hv)
    db.session.add(no_pinning_hv)
    db.session.add(no_pinning_tm)
    db.session.add(no_pinning_tm_added_upstream_certs)
    db.session.add(no_pinning_sa)
    db.session.add(no_pinning_sa_added_upstream_certs)
    db.session.add(mitmproxy_ca_signed_wv)
    db.session.add(expired_trusted_ca_wv)
    db.session.add(other_hostname_untrusted_wv)
    db.session.add(other_hostname_trusted_wv)

    db.session.commit()
