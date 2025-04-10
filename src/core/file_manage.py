import base64

from fastapi import UploadFile
from PIL import Image

from src.core.exceptions import (
    WrongFileSizeException,
    WrongFileTypeException,
    WrongImageDimensionsException,
)
from src.settings import settings


def check_file_size(file: UploadFile, size: int) -> UploadFile:
    """
    Check if the file size exceeds the limit.
    """
    if file.size > size:
        raise WrongFileSizeException()
    return file


def check_image_dimensions(file: UploadFile) -> UploadFile:
    """
    Check if the image dimensions are within the allowed range.
    The shortest side of the image must be more than MIN IMAGE DIMENSIONS.
    """
    try:
        file.file.seek(0)
        with Image.open(file.file) as img:
            width, height = img.size
            if min(width, height) < settings.upload_file.MIN_IMAGE_DIMENSIONS:
                raise WrongImageDimensionsException(
                    "Image dimensions are too small. The shortest side must be at least 300 pixels."
                )
        file.file.seek(0)
        return file
    except Exception as e:
        raise WrongImageDimensionsException("Failed to validate image dimensions") from e


def verify_file(file: UploadFile) -> UploadFile:
    """
    Verify the file type and size.
    """
    ct = file.content_type

    if ct in settings.upload_file.ALLOWED_IMAGE_CONTENT_TYPE:
        check_file_size(file, settings.upload_file.MAX_IMAGE_SIZE)
        check_image_dimensions(file)
    elif ct in settings.upload_file.ALLOWED_VIDEO_CONTENT_TYPE:
        check_file_size(file, settings.upload_file.MAX_VIDEO_SIZE)
    else:
        raise WrongFileTypeException

    return file


def verify_subject_image(file: UploadFile) -> UploadFile:
    """
    Verify the file type and size.
    """
    ct = file.content_type

    if ct in settings.upload_file.ALLOWED_IMAGE_CONTENT_TYPE:
        check_file_size(file, settings.upload_file.MAX_IMAGE_SIZE)
    else:
        raise WrongFileTypeException

    return file


async def convert_base64(file: UploadFile) -> str:
    """
    Convert the file to base64.
    """
    file_content = await file.read()
    return base64.b64encode(file_content).decode("utf-8")
