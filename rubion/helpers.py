import re

# test if any of a is in b
# https://stackoverflow.com/questions/10668282/one-liner-to-check-if-at-least-one-item-in-list-exists-in-another-list
# Might be faster than my for-loop three-liner
def any_in( a, b ):
    return not set(a).isdisjoint(b)

def distinct_no_order( l ):
    return list(set( l ))


def bases( cls ):
# taken from https://stackoverflow.com/questions/4094624/is-there-a-standard-function-to-iterate-over-base-classes
    classes = [cls]
    i = 0
    while 1:
        try:
            cls = classes[i]
        except IndexError:
            return classes
        i += 1
        classes[i:i] = [base for base in cls.__bases__ if base not in classes] 
    return classes

def get_unique_value(model, proposal, field_name="slug", instance_pk=None, separator="-"):
    """ Returns unique string by the proposed one.
    Optionally takes:
    * field name which can  be 'slug', 'username', 'invoice_number', etc.
    * the primary key of the instance to which the string will be assigned.
    * separator which can be '-', '_', ' ', '', etc.
    By default, for proposal 'example' returns strings from the sequence:
        'example', 'example-2', 'example-3', 'example-4', ...
    """

# taken from https://djangosnippets.org/snippets/98/

    if instance_pk:
        similar_ones = model.objects.filter(**{field_name + "__startswith": proposal}).exclude(pk=instance_pk).values(field_name)
    else:
        similar_ones = model.objects.filter(**{field_name + "__startswith": proposal}).values(field_name)
    similar_ones = [elem[field_name] for elem in similar_ones]
    if proposal not in similar_ones:
        return proposal
    else:
        numbers = []
        for value in similar_ones:
            match = re.match(r'^%s%s(\d+)$' % (proposal, separator), value)
            if match:
                numbers.append(int(match.group(1)))
        if len(numbers)==0:
            return "%s%s2" % (proposal, separator)
        else:
            largest = sorted(numbers)[-1]
            return "%s%s%d" % (proposal, separator, largest + 1)
