from typing import Union

import click

from .bluelink import BlueLink
from .utils import get


@click.group()
def main():
    """
    CLI for Hyundai's BlueLink service.
    """


@main.command("cars")
def cars():
    bluelink = BlueLink()
    bluelink.login()
    for car in bluelink.cars.values():
        print(f"{car.model} - {car.vin}")


@main.command("lock")
@click.argument("vin")
def lock(vin: str):
    car = get(vin, "lock")
    if car:
        print("Locking...")


@main.command("unlock")
@click.argument("vin")
def unlock(vin: str):
    car = get(vin, "unlock")
    if car:
        print("Unlocking...")


@main.command("start")
@click.argument("vin")
@click.option("--duration", default=10, help="Duration to run engine in seconds.")
@click.option("--temp", default="LO", help="Temperature to turn on AC.")
@click.option("--defrost", default=False, help="Defrost the car.", is_flag=True)
@click.option("--driver-seat-heat", "--dsh", default=4, help="Driver seat heat level.")
@click.option(
    "--passenger-seat-heat", "--psh", default=4, help="Passenger seat heat level."
)
def start(
    vin: str,
    duration: int,
    temp: Union[str, int],
    defrost: bool,
    driver_seat_heat: int,
    passenger_seat_heat: int,
):
    car = get(
        vin,
        "start",
        duration,
        temp,
        defrost,
        driver_seat_heat,
        passenger_seat_heat,
    )
    if car:
        print("Starting...")


@main.command("stop")
@click.argument("vin")
def stop(vin: str):
    car = get(vin, "stop")
    if car:
        print("Stopping...")


@main.command("find")
@click.argument("vin")
def find(vin: str):
    find = get(vin, "find")
    if find:
        latitude, longitude = find
        print(f"Latitude: {latitude}")
        print(f"Longitude: {longitude}")


@main.command("odometer")
@click.argument("vin")
def odometer(vin: str):
    odometer = get(vin, "odometer")
    if odometer:
        print(odometer)
