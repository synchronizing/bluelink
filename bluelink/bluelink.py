import json
import os
from typing import List, Optional, Union

import requests

from .errors import RequestFailed
from .utils import validate

HOME = "https://owners.hyundaiusa.com"


class Car:
    """
    Interface for a BlueLink car.

    Properties:
        nickname: Nickname of the car.
        model: Model of the car.
        year: Year of the car.
        vin: VIN of the car.
        uid: Unique identifier of the car.
        bluelink: Whether the car is a BlueLink car.
    """

    def __init__(
        self,
        nickname: str,
        model: str,
        year: int,
        vin: str,
        uid: str,
        bluelink: bool,
        _auth: dict,
        _info: dict,
        _session: requests.Session,
    ):
        """
        Initializes a new car object.

        Private:
            _auth: Authentication information needed for remote API calls.
            _info: Raw information about the car.
            _session: Session object to use for remote API calls.
        """
        self.nickname = nickname
        self.model = model
        self.year = year
        self.vin = vin
        self.uid = uid
        self.bluelink = bluelink
        self._auth = _auth
        self._info = _info
        self._session = _session

    def lock(self) -> bool:
        """
        Locks the car.

        Returns:
            Whether the car was locked.

        Raises:
            RequestFailed: If the request failed.
        """
        self._request("remotelock")
        return True

    def unlock(self) -> bool:
        """
        Unlocks the car.

        Returns:
            Whether the car was unlocked.

        Raises:
            RequestFailed: If the request failed.
        """
        self._request("remoteunlock")
        return True

    def start(
        self,
        duration: int = 10,
        temp: Union[str, int] = "LO",
        defrost: bool = False,
        driver_seat_heat: int = 4,
        passenger_seat_heat: int = 4,
    ) -> bool:
        """
        Starts the car's engine.

        Args:
            duration: How long to turn the car on for. 10 minutes is max.
            temp: Temperature to set the car to. Can be 'HI', 'LO', or a number.
            defrost: Whether to defrost the car.
            driver_seat: Temperature to set the driver seat to.
            passenger_seat: Temperature to set the passenger seat to.

        Returns:
            Whether the car was started.

        Raises:
            RequestFailed: If the request failed.
        """
        self._request(
            "ignitionstart",
            headers={
                "airCtrl": "true",
                "igniOnDuration": duration,
                "airTempvalue": temp,
                "defrost": defrost,
                "heating1": "0",
                # 'seatHeaderVentInfo' expects a string, not a JSON dict.
                "seatHeaterVentInfo": json.dumps(
                    {
                        "drvSeatHeatState": driver_seat_heat,
                        "astSeatHeatState": passenger_seat_heat,
                    }
                ),
            },
        )
        return True

    def stop(self) -> bool:
        """
        Stops the car's engine.

        Returns:
            Whether the car was stopped.

        Raises:
            RequestFailed: If the request failed.
        """
        self._request("ignitionstop")
        return True

    def find(self) -> tuple:
        """
        Finds the car.

        Returns:
            Tuple with latitude and longitude.

        Raises:
            RequestFailed: If the request failed.
        """
        resp = self._request("getFindMyCar")
        coordinates = resp["RESPONSE_STRING"]["coord"]
        latitude, longitude = coordinates["lat"], coordinates["lon"]
        return (latitude, longitude)

    @property
    def odometer(self) -> int:
        """
        Gets the car's odometer.

        Returns:
            The car's odometer.

        Raises:
            RequestFailed: If the request failed.
        """
        resp = self._request("getRecMaintenanceTimeline")
        info = resp["RESPONSE_STRING"]["MaintenanceInfo"][0]
        mileage = int(info["CurrentMileage"])
        return mileage

    def _request(self, action: str, headers: dict = {}) -> dict:
        """
        Sends a request to the remote API.

        Args:
            action: The action to perform.

        Returns:
            The response from the remote API.

        Raises:
            RequestFailed: If the request failed.
        """
        if action == "getRecMaintenanceTimeline":
            endpoint = "VehicleHealthServlet"
        else:
            endpoint = "remoteAction"

        resp = self._session.post(
            url=f"{HOME}/bin/common/{endpoint}",
            headers={
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "csrf-token": "undefined",
                "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "x-requested-with": "XMLHttpRequest",
            },
            data={
                **self._auth,
                "vin": self.vin,
                "url": HOME,
                "gen": 2,
                "regId": self.uid,
                "service": action,
                **headers,
            },
        )
        # Validates the response.
        json = validate(resp=resp, action=action)

        # Returns the response.
        return json

    def __repr__(self) -> str:
        return f"Car(nickname={self.nickname}, bluelink={self.bluelink})"

    def __str__(self) -> str:
        return self.__repr__()


class BlueLink:
    """
    Wrapper for interacting with the remote API.

    Properties:
        email: Email address of the BlueLink account.
        password: Password of the BlueLink account.
        pin: PIN of the BlueLink account.
        cars: List of cars owned by the BlueLink account.
    """

    _session = requests.Session()

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        pin: Optional[str] = None,
    ):
        """
        Initializes a new BlueLink object.

        Notes:
            If any of the inputs are not provided, environment variables will be used.
        """
        self.email = email if email else os.environ.get("BLUELINK_EMAIL")
        self.password = password if password else os.environ.get("BLUELINK_PASSWORD")
        self.pin = pin if pin else os.environ.get("BLUELINK_PIN")

        if not self.email or not self.password or not self.pin:
            raise ValueError("Bluelink credentials were not provided.")

        # Gets set once login is successful. CSRF and JWT token.
        self._auth = {}

        # Cache for 'cars' property.
        self._cars = []

    def login(self):
        """
        Logins to BlueLink.

        Raises:
            RequestFailed: API returned an error when logging in.
        """

        # Won't re-login if already logged in.
        if self._auth:
            return

        # Gets CSRF token.
        resp = self._session.get(f"{HOME}/etc/designs/ownercommon/us/token.json")
        csrf = resp.json()["jwt_token"]

        # Validates CSRF token.
        resp = self._session.get(
            f"{HOME}/libs/granite/csrf/token.json",
            headers={"csrf_token": csrf},
        )
        if resp.status_code != 200:
            raise RequestFailed("Failed to get CSRF token.")

        # Sends login request.
        resp = self._session.post(
            url=f"{HOME}/bin/common/connectCar",
            data={
                ":cq_csrf_token": csrf,
                "username": self.email,
                "password": self.password,
                "url": f"{HOME}/us/en/index.html",
            },
        )

        # Validates the response.
        json = validate(resp=resp, action="login")

        # Retrieves JWT ID that is needed for API calls.
        jwt = json["RESPONSE_STRING"]["jwt_id"]

        # Stores authentication information needed for remote API calls.
        self._auth = {"username": self.email, "pin": self.pin, "token": jwt}

    @property
    def cars(self) -> List[Car]:
        """
        Gets a list of all cars owned by the user.

        Returns:
            List of all cars owned by the user.

        Raises:
            RequestFailed: API returned an error when getting cars.
        """
        if not self._auth:
            raise RequestFailed("You must login first.")

        # Returns cached results.
        if self._cars:
            return self._cars

        # Gets car information.
        resp = self._session.post(
            f"{HOME}/bin/common/MyAccountServlet",
            data={
                "username": self.email,
                "token": self._auth["token"],
                "url": f"{HOME}/us/en/page/dashboard.html",
                "service": "getOwnerInfoService",
            },
        )

        # Validates the response.
        json = validate(resp=resp, action="get cars")

        # Retrieves car information.
        cars = {}
        for info in json["RESPONSE_STRING"]["OwnersVehiclesInfo"]:
            car = Car(
                nickname=info["VehicleNickName"],
                model=info["Name"],
                year=info["Year"],
                vin=info["VinNumber"],
                uid=info["RegistrationID"],
                bluelink=bool(info["IsBlueLinkCar"]),
                _auth=self._auth,
                _info=info,
                _session=self._session,
            )
            cars[info["VinNumber"]] = car

        self._cars = cars
        return cars

    def __repr__(self) -> str:
        return f"BlueLink(email={self.email}, logged_in={bool(self._auth)})"

    def __str__(self) -> str:
        return self.__repr__()
