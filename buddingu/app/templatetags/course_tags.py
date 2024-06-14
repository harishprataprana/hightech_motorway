from django import template
import math
register = template.Library()


@register.simple_tag
def discount_calculation(price,discount):
    if discount is None or discount is 0:
        return price
    sellprice = price
    sellprice = price - (price * discount/100)
    return math.floor(sellprice)


@register.simple_tag
def equivalent_price_calculation(price, multiplier):
    newprice = price*multiplier
    newprice_rounded = round(newprice, 2)
    return newprice_rounded


@register.simple_tag
def equivalent_discounted_price_calculation(price, discount, multiplier):
    if discount is None or discount is 0:
        newprice = price*multiplier
        newprice_rounded = round(newprice, 2)
        return newprice_rounded

    sellprice = price
    sellprice = price - (price * discount/100)
    sellprice = sellprice*multiplier
    sellprice_rounded = round(sellprice, 2)
    return sellprice_rounded
