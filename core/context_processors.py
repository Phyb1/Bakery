from .models import BakeryInfo


def bakery_info(request):
    """
    Makes {{ bakery }} available in every template (see TEMPLATES in
    settings/base.py) without every view having to fetch and pass it.

    Returns None if no BakeryInfo row exists yet (e.g. right after a fresh
    `migrate`, before anyone has logged into /admin/ to create one) -
    templates should guard with {% if bakery %} where it matters, though
    base.html handles the missing case gracefully.
    """
    return {"bakery": BakeryInfo.objects.first()}
