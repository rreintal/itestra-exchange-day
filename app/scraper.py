class Result:
    def __init__(self, restaurants):
        self.restaurants = restaurants  # list of Restaurant


class Restaurant:
    def __init__(self, name, emoji, meals):
        self.name = name
        self.emoji = emoji
        self.meals = meals  # list of Offer


class Offer:
    def __init__(self, name, price):
        self.name = name
        self.price = price


# TODO:
def getFormattedMenus():
    # bla bla ...
    return ""