from django import template

register = template.Library()

@register.filter
def percentage_of_target(value, target=100):
    try:
        return (value / target) * 100
    except ZeroDivisionError:
        return 0


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_date_for(occupancy_by_date, date):
    return occupancy_by_date.get(str(date), 0)
