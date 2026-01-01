from django import template
from django.apps import apps
from results.models import ClassSubjectTeacher
from ..utils import interpret_grade as utils_interpret_grade


register = template.Library()


@register.filter
def get_psycho_value(dictionary, args):
    """
    Usage in template: psycho_dict|get_psycho_value:"student_id,skill"
    Looks up composite key (student_id, skill) in dictionary
    """
    try:
        student_id, skill = args.split(',')
        return dictionary.get((int(student_id), skill), "")
    except Exception:
        return ""

@register.filter
def get_affective_value(dictionary, args):
    """
    Usage in template: affective_dict|get_affective_value:"student_id,domain"
    Looks up composite key (student_id, domain) in dictionary
    """
    try:
        student_id, domain = args.split(',')
        return dictionary.get((int(student_id), domain), "")
    except Exception:
        return ""


@register.filter
def get_item(dictionary, key):
    if dictionary and key in dictionary:
        return dictionary.get(key)
    return None

@register.filter
def to_list(start, end):
    # usage: 1|to_list:5 -> [1,2,3,4,5]
    return list(range(int(start), int(end)+1))

@register.filter
def get_item(dictionary, key):
    """Gets an item from a dictionary by key."""
    if dictionary is None:
        return None
    return dictionary.get(key)



@register.filter
def get_token(student):
    ResultVerification = apps.get_model('results', 'ResultVerification')
    obj = ResultVerification.objects.filter(student=student, valid=True).first()
    return obj.verification_token if obj else ''



@register.filter
def to_grade(value):
    mapping = {5: 'A', 4: 'B', 3: 'C', 2: 'D', 1: 'E', 0: '-'}
    try:
        return mapping.get(int(value), '-')
    except:
        return '-'


@register.filter
def to_grade(value):
    if not value:
        return ""
    mapping = {
        5: "Excellent",
        4: "Very Good",
        3: "Good",
        2: "Fair",
        1: "Poor"
    }
    return mapping.get(int(value), "")


@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key))



register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_item(dictionary, key):
    if not dictionary:
        return None
    try:
        return dictionary.get(key)
    except AttributeError:
        return None




@register.filter
def num_range(start, end):
    """
    Generates a range from start to end (inclusive).
    Usage: {% for i in 1|num_range:5 %}
    """
    return range(int(start), int(end) + 1)





@register.filter
def get_item(dictionary, key):
    """
    Safely fetch dictionary[key] whether key is int or str.
    """
    if not dictionary:
        return None

    # Convert key to string (because JSON dicts store keys as strings)
    key = str(key)

    return dictionary.get(key)

@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, 0)  # default to 0


@register.filter
def get_student_comment(comments, student_id):
    return comments.filter(student_id=student_id).first()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)




@register.filter
def dict_get(d, key):
    """Get key from dictionary safely."""
    if not d:
        return None
    return d.get(key)



@register.filter
def dict_get(dict_obj, key):
    return dict_obj.get(key)


@register.filter
def get(data, key):
    return data.get(key, {})



@register.filter(name='add_class')
def add_class(field, css):
    """
    Adds a CSS class to a Django form field widget.
    Usage in template: {{ form.field|add_class:"class-name" }}
    """
    return field.as_widget(attrs={"class": css})





@register.filter
def subject_teacher(subject, school_class):
    try:
        cst = ClassSubjectTeacher.objects.get(
            school_class=school_class,
            subject=subject
        )
        return cst.teacher.get_full_name()
    except ClassSubjectTeacher.DoesNotExist:
        return "N/A"






@register.filter
def get_field_value(obj, field_name):
    if obj is None:
        return 0
    return getattr(obj, field_name, 0)



@register.filter
def to_int(value):
    try:
        return int(value)
    except:
        return 0



@register.filter
def to_dict(obj):
    """
    Converts a model instance to dict of field names and values
    Excludes auto fields and private attributes.
    """
    return {f.name: getattr(obj, f.name) for f in obj._meta.fields if not f.auto_created and not f.name.startswith('_')}


@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, '')


@register.filter
def get_item(obj, key):
    return getattr(obj, key, '')




@register.filter
def get_item(obj, key):
    """Access dictionary/attribute by key"""
    return getattr(obj, key, '') if hasattr(obj, key) else obj.get(key, '')

@register.filter
def split(value, sep=","):
    """Split a string by separator"""
    return value.split(sep)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)




@register.filter
def interpret_grade(grade):
    return utils_interpret_grade(grade)



@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "N/A")



@register.filter
def add_class(field, css):
    return field.as_widget(attrs={"class": css})



@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, 0)



@register.filter
def get_item(dictionary, key):
    """Get value from dictionary using key"""
    return dictionary.get(key, {})



@register.filter
def dict_get(d, key):
    return d.get(key, {})



@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key))
