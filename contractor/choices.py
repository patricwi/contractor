# -*- coding: utf-8 -*-

"""Provide enums for booth and paket choices.

We use enums because they have some very nice advantages:

- We can get the right one very easily

```
>>> choice = BoothChoice(('big', 'A', 2))
<BoothChoice.bA2: ('big', 'A', 2)>
```

- We can iterate over the enum (used to create price form)

- We can print them nicely without some dict acrobatic storing fulltext.

-We have handy creation and checking functions.

```
>>> choice.size == 'big'
True
```

Profit :D

([Enums](https://docs.python.org/3/library/enum.html) are relatively new in
 python, but very nice to work with)
"""

from enum import Enum


class BoothChoice(Enum):
    """Enum for booth choices.

    You can use the properties `size`, `category` and `days`
    for easy comparisons:

    ```
    >>> BoothChoice.sA1.days == 1
    True
    ```
    """

    # Small booths
    sA1 = ('small', 'A', 1)
    sA2 = ('small', 'A', 2)
    sB1 = ('small', 'B', 1)
    sB2 = ('small', 'B', 2)

    # Big booths
    bA1 = ('big', 'A', 1)
    bA2 = ('big', 'A', 2)
    bB1 = ('big', 'B', 1)
    bB2 = ('big', 'B', 2)

    # Startup (In SOAP they have category 'C' so we use that here)
    su1 = ('startup', 'C', 1)
    su2 = ('startup', 'C', 2)

    def __init__(self, size, category, days):
        """Put info into handy variables."""
        self.size = size
        self.category = category
        self.days = days

        # Create fullname string
        # Booth name, only display "booth" for small and big booths
        booth = "%s booth, " % size if size != 'startup' else "startup, "

        # Category C isn't actually a thing, just a marker for startup
        # Don't show
        cat = "category %s, " % category if category != 'C' else ""

        # Days with plural to be fancy ^^
        days = "%s days" % days if days > 1 else "1 day"

        self.fullname = booth + cat + days

    def __str__(self):
        """Print fullname."""
        return self.fullname


class PacketChoice(Enum):
    """Enum for packet choices.

    If you want to compare to this enum, you can
    either use the conventional aproach:

    ```
    >>> myobject == PacketChoice.media
    ```

    Or, if importing the enum would be trouble (e.g. in a template),
    you can just use

    ```
    >>> myobject.name == "media"
    ```

    to compare strings.
    """

    first = "first packet"
    business = "business packet"
    media = "media packet"

    def __str__(self):
        """Return the value (the description string)."""
        return self.value
