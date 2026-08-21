from dataclasses import dataclass


@dataclass(slots=True)
class VideoParserError(Exception):
    code: str
    message: str
    status_code: int

    def __str__(self) -> str:
        return self.message


def invalid_link(message: str = "分享链接格式无效") -> VideoParserError:
    return VideoParserError("invalid_link", message, 422)


def upstream_error(message: str = "平台内容暂时无法访问") -> VideoParserError:
    return VideoParserError("upstream_error", message, 502)


def parse_error(message: str = "平台页面结构已变化，暂时无法解析") -> VideoParserError:
    return VideoParserError("parse_error", message, 502)
