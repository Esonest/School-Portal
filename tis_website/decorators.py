from django.core.exceptions import PermissionDenied



def website_admin_required(view_func):

    def wrapper(request, *args, **kwargs):

        if request.user.role not in [
            "schooladmin",
            "superadmin"
        ]:

            raise PermissionDenied


        return view_func(
            request,
            *args,
            **kwargs
        )


    return wrapper