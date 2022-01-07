# 🚙 BlueLink

Unofficial Python API wrapper for Hyundai's [Bluelink®](https://www.hyundaiusa.com/us/en/blue-link). Allows you to remotely control your Hyundai car via Python.

## Installing

```
pip install bluelink
```

## Documentation

Documentation can be found below. See code for more details.

## Using

You can use this module either through the built-in CLI, or directly through Python. `lock`, `unlock`, `start`, `stop`, `find`, and `odometer` are supported.

### CLI

Note that every individual command will sign-in in to BlueLink. If you plan on chaining commands, you should use the Python API.

```bash
$ export BLUELINK_EMAIL=<email>
$ export BLUELINK_PASSWORD=<password>
$ export BLUELINK_PIN=<pin>

$ bluelink cars
Elantra - <vin>
Santa Fe - <vin>

$ bluelink <vin> lock
Locking...

$ bluelink <vin> unlock
Unlocking...

# 'dsh' stands for 'driver seat heat'
# 'psh' stands for 'passenger seat heat'
$ bluelink <vin> start --duration=10 --temp="LO" --defrost --dsh=4 --psh=4
Starting...

$ bluelink <vin> stop
Stopping...

$ bluelink <vin> find
Latitude: <latitude>
Longitude: <longitude>

$ bluelink <vin> odometer
7,643
```

### Python

The Python wrapper comes with two classes: `BlueLink` and `Car`. The former is the main class that allows logging into the service, and the latter is a wrapper for specific cars linked to the account.

```python
from bluelink import BlueLink

# Logins to BlueLink. You may also choose to set the username, password, 
# and pin via environment variables (same convention as the CLI) and
# leave the arguments blank.
bl = BlueLink(email='<email>', password='<password>', pin='<pin>')
bl.login()

# Prints the BlueLink object.
print(bl) # BlueLink(email=<email>, is_logged=True)

# Print all of the cars in the account. 'cars' is a standard dictionary.
for vin, car in bl.cars.items():
    print(vin, car) # <vin> Car(nickname=<nickname>, bluelink=<has_bluelink>)

# Gets the first car.
elantra = bl.cars['<vin>']

elantra.lock() # Returns True if successful.
elantra.unlock() # Returns True if successful.
elantra.start(
    duration=10, 
    temp="LO", 
    defrost=True,
    driver_seat_heat=4,
    passenger_seat_heat=4,
) # Returns True if successful.
elantra.stop() # Returns True if successful.
elantra.find() # Returns a tuple of (latitude, longitude).
elantra.odometer # Returns an integer. Note this is a property, and not a method.
```
