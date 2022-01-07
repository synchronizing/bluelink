from json.decoder import JSONDecodeError
from typing import Tuple, Union

from requests import Response

from .errors import RequestFailed


def validate(resp: Response, action: str = "") -> dict:
    """
    Checks if API returned a valid response.

    Args:
        resp: The response from the remote API.

    Returns:
        The JSON response from the remote API.

    Raises:
        RequestFailed: API returned an error.
    """

    # Ensures status code.
    status = resp.status_code
    if status != 200:
        raise RequestFailed(f"Action {action} responded with status code {status}.")

    # Attempts to decode response to JSON.
    try:
        json = resp.json()
    except JSONDecodeError:
        raise RequestFailed(f"Invalid JSON response from API for {action}: {resp.text}")

    # Verifies that the response is valid.
    if "E_IFRESULT" not in json or json["E_IFRESULT"] != "Z:Success":
        error = json["E_IFFAILMSG"]

        if error == "Bad Gateway":
            raise RequestFailed(
                f"Unable to send your request because a previous request is pending. Please wait and try again later."
            )
        else:
            raise RequestFailed(f"BlueLink {action} request failed due to: {error}")

    return json


def get(vin: str, func: str, *args, **kwargs) -> Union[Tuple[str, str], str, bool]:
    """
    Gets result from BlueLink API.

    A hacky function to prevent us from repeating ourselves.

    Args:
        vin: The VIN of the car.
        func: The function to call on the BlueLink Car API.
        *args: Arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The result of the function call.
    """
    from .bluelink import BlueLink

    # Tries to setup BlueLink.
    try:
        bluelink = BlueLink()
    except ValueError:
        print("Credentials not found. See docs for info on how to set them.")
        return

    bluelink.login()

    # Attempts to get the car.
    car = None
    if vin in bluelink.cars:
        car = bluelink.cars[vin]
    else:
        print(f"Car with VIN {vin} not found.")

    # Tries to the run the function.
    result = None
    try:
        func = getattr(car, func)
        if callable(func):
            result = func(*args, **kwargs)
        else:
            result = func
    except RequestFailed as e:
        print(e)
        exit(1)

    return result
