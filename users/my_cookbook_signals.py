from mongoengine import signals
from .models import MyCookbook

def add_cookbook_to_user(sender, document, **kwargs):
    """
    Signal to add a new cookbook to the user's my_cookbooks list upon creation.
    """
    if document.owner and document not in document.owner.my_cookbooks:
        document.owner.my_cookbooks.append(document)
        document.owner.save()

def remove_cookbook_from_user(sender, document, **kwargs):
    """
    Signal to remove the cookbook from the user's my_cookbooks list upon deletion.
    """
    if document.owner and document in document.owner.my_cookbooks:
        document.owner.my_cookbooks.remove(document)
        document.owner.save()

# Connect signals to MyCookbook
signals.post_save.connect(add_cookbook_to_user, sender=MyCookbook)
signals.post_delete.connect(remove_cookbook_from_user, sender=MyCookbook)


