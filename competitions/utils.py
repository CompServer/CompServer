"""Request utilities for the competitions module"""
from enum import Enum

http_codes = {
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",
    103: "Early Hints",

    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    208: "Already Reported",
    218: "This is fine", # apache servers... https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#Unofficial_codes
    226: "IM Used",

    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy", # depricated
    306: "Unused", # depricated
    307: "Temporary Redirect",
    308: "Permanent Redirect",

    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot", # this is real btw
    420: "Enhance Your Calm", # unofficial twitter response code??? https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#Unofficial_codes
    421: "Misdirected Request",
    422: "Unprocessable Content",
    423: "Locked",
    424: "Failed Dependency",
    425: "Too Early",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    430: "Shopify Security Rejection", # unofficial shopify servers... https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#Unofficial_codes
    431: "Request Header Fields Too Large",
    444: "No Response", # unofficial nginx  https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#Unofficial_codes
    449: "Retry With", # unofficial
    450: "Blocked by Windows Parental Controls", # bro what https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#Unofficial_codes
    451: "Unavailable For Legal Reasons",

    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required",
    520: "Web Server Returned an Unknown Error", # unoffical code cloudflare
    521: "Web Server is Down", # unoffical code cloudflare
    522: "Connection Timed Out", # unoffical code cloudflare
    523: "Origin is Unreachable", # unoffical code cloudflare
    524: "A Timeout Occurred", # unoffical code cloudflare
    525: "SSL Handshake Failed", # unoffical code cloudflare
    526: "Invalid SSL Certificate", # unoffical code cloudflare
    527: "Railgun Error", # unoffical code cloudflare
    530: "Site is Frozen", # unoffical code cloudflare

    598: "Network Read Timeout Error", # unoffical code
    599: "Network Connect Timeout Error", # unoffical code
}

class HTTPCode:
    status: int
    def __init__(self, status: int):
        self.status = status
        assert status in http_codes.keys(), f"Invalid HTTP status code {status}"

    @property
    def name(self) -> str:
        return http_codes.get(self.status, "Unknown")

    @property
    def is_1xx(self) -> bool:
        return 100 <= self.status < 200

    @property
    def is_2xx(self) -> bool:
        return 200 <= self.status < 300

    @property
    def is_3xx(self) -> bool:
        return 300 <= self.status < 400

    @property
    def is_4xx(self) -> bool:
        return 400 <= self.status < 500

    @property
    def is_5xx(self) -> bool:
        return 500 <= self.status < 600

    def __str__(self) -> str:
        return f"{self.status} {self.name}"
    
    def __int__(self) -> int:
        return self.status

class RequestType(Enum):
    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    PUT = 'PUT'
    DELETE = 'DELETE'

    # def get_method_callable(self, session: aiohttp.ClientSession) -> Callable:
    #     if self is RequestType.GET:
    #         return session.get
    #     elif self is RequestType.POST:
    #         return session.post
    #     elif self is RequestType.PATCH:
    #         return session.patch
    #     elif self is RequestType.PUT:
    #         return session.put
    #     elif self is RequestType.DELETE:
    #         return session.delete
    #     raise ValueError(f"Invalid request type {self}")

    def __str__(self):
        return self.value.upper()

# https://github.com/fabiocaccamo/django-colorfield/blob/main/colorfield/utils.py

from PIL import Image, UnidentifiedImageError


def get_image_background_color(img, img_format: str):
    has_alpha = img_format in {"hexa", "rgba"}
    img = img.convert("RGBA" if has_alpha else "RGB")
    pixel_color = img.getpixel((1, 1))
    if img_format in {"hex", "hexa"}:
        color_format = "#" + "%02x" * len(pixel_color)
        color = color_format % pixel_color
        color = color.upper()
    elif img_format in {"rgb", "rgba"}:
        if has_alpha:
            # Normalize alpha channel to be between 0 and 1
            pixel_color = (
                *pixel_color[:3],
                round(pixel_color[3] / 255, 2),
            )
        # Should look like `rgb(1, 2, 3) or rgba(1, 2, 3, 1.0)
        color = f"{img_format}{pixel_color}"
    else:  # pragma: no cover
        raise NotImplementedError(f"Unsupported color format: {img_format}")
    return color


def get_image_file_background_color(img_file, img_format: str):
    color = ""
    try:
        with Image.open(img_file) as image:
            color = get_image_background_color(image, img_format)
    except UnidentifiedImageError:
        pass
    return color