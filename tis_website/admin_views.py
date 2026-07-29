from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .decorators import website_admin_required

from django.shortcuts import render, redirect
from django.contrib import messages

from .models import SchoolWebsite
from .forms import SchoolWebsiteForm

from .decorators import website_admin_required



@login_required
@website_admin_required
def website_dashboard(request):

    return render(
        request,
        "tis_website/admin/dashboard.html"
    )




@login_required
@website_admin_required
def website_profile(request):

    website, created = SchoolWebsite.objects.get_or_create(

        school=request.user.school

    )


    if request.method == "POST":


        form = SchoolWebsiteForm(

            request.POST,

            request.FILES,

            instance=website

        )


        if form.is_valid():

            form.save()


            messages.success(
                request,
                "Website profile updated successfully."
            )


            return redirect(
                "tis_website_admin:profile"
            )


    else:


        form = SchoolWebsiteForm(
            instance=website
        )



    return render(

        request,

        "tis_website/admin/profile.html",

        {

            "form": form,

            "website": website

        }

    )


from .models import HomepageContent
from .forms import HomepageContentForm



@login_required
@website_admin_required
def homepage_settings(request):

    homepage, created = HomepageContent.objects.get_or_create(

        school=request.user.school

    )


    if request.method == "POST":


        form = HomepageContentForm(

            request.POST,

            request.FILES,

            instance=homepage

        )


        if form.is_valid():

            form.save()


            messages.success(
                request,
                "Homepage updated successfully."
            )


            return redirect(
                "tis_website_admin:homepage"
            )


    else:

        form = HomepageContentForm(
            instance=homepage
        )


    return render(

        request,

        "tis_website/admin/homepage.html",

        {
            "form":form
        }
    )


from django.shortcuts import render, redirect, get_object_or_404

from .models import NewsEvent

from .forms import NewsEventForm

from accounts.models import School



def news_list(request):

    school = request.user.school


    news = NewsEvent.objects.filter(
        school=school
    )


    return render(

        request,

        "tis_website/admin/news_list.html",

        {
            "news":news
        }

    )






def news_create(request):

    school = request.user.school



    if request.method == "POST":


        form = NewsEventForm(
            request.POST,
            request.FILES
        )


        if form.is_valid():

            news = form.save(
                commit=False
            )


            news.school = school


            news.save()


            return redirect(
                "tis_website_admin:news_list"
            )



    else:

        form = NewsEventForm()



    return render(

        request,

        "tis_website/admin/news_form.html",

        {
            "form":form
        }

    )







def news_update(request, pk):


    school = request.user.school


    news = get_object_or_404(

        NewsEvent,

        id=pk,

        school=school

    )



    form = NewsEventForm(

        request.POST or None,

        request.FILES or None,

        instance=news

    )



    if form.is_valid():

        form.save()


        return redirect(
            "tis_website_admin:news_list"
        )




    return render(

        request,

        "tis_website/admin/news_form.html",

        {
            "form":form
        }

    )









def news_delete(request, pk):


    school=request.user.school


    news=get_object_or_404(

        NewsEvent,

        id=pk,

        school=school

    )


    news.delete()


    return redirect(

        "tis_website_admin:news_list"

    )


from .models import Gallery

from .forms import GalleryForm




def gallery_list(request):

    school = request.user.school


    gallery = Gallery.objects.filter(
        school=school
    )


    return render(

        request,

        "tis_website/admin/gallery_list.html",

        {
            "gallery":gallery
        }

    )







def gallery_create(request):

    school = request.user.school


    if request.method == "POST":


        form = GalleryForm(

            request.POST,

            request.FILES

        )


        if form.is_valid():


            item=form.save(
                commit=False
            )


            item.school=school


            item.save()



            return redirect(
                "tis_website_admin:gallery_list"
            )



    else:

        form=GalleryForm()



    return render(

        request,

        "tis_website/admin/gallery_form.html",

        {
            "form":form
        }

    )









def gallery_update(request,pk):


    school=request.user.school



    item=get_object_or_404(

        Gallery,

        id=pk,

        school=school

    )




    form=GalleryForm(

        request.POST or None,

        request.FILES or None,

        instance=item

    )




    if form.is_valid():

        form.save()


        return redirect(
            "tis_website_admin:gallery_list"
        )





    return render(

        request,

        "tis_website/admin/gallery_form.html",

        {
            "form":form
        }

    )









def gallery_delete(request,pk):


    school=request.user.school



    item=get_object_or_404(

        Gallery,

        id=pk,

        school=school

    )


    item.delete()



    return redirect(

        "tis_website_admin:gallery_list"

    )


from .models import AdmissionApplication




def admission_list(request):


    school=request.user.school



    applications = AdmissionApplication.objects.filter(

        school=school

    )



    return render(

        request,

        "tis_website/admin/admission_list.html",

        {

            "applications":applications

        }

    )







def admission_update_status(request,pk,status):


    school=request.user.school



    application=get_object_or_404(

        AdmissionApplication,

        id=pk,

        school=school

    )



    application.status=status


    application.save()



    return redirect(

        "tis_website_admin:admission_list"

    )


from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)


from .models import AdmissionApplication

from .forms import AdmissionExamAssignmentForm




def assign_admission_exam(request, pk):

    application = get_object_or_404(
        AdmissionApplication,
        id=pk,
        school=request.user.school
    )


    if request.method == "POST":

        form = AdmissionExamAssignmentForm(
            request.POST,
            instance=application,
            school=request.user.school
        )


        if form.is_valid():

            admission = form.save(
                commit=False
            )

            admission.status = "exam_assigned"

            admission.save()


            return redirect(
                "tis_website_admin:admission_list"
            )


    else:

        form = AdmissionExamAssignmentForm(
            instance=application,
            school=request.user.school
        )


    return render(
        request,
        "tis_website/admin/assign_admission_exam.html",
        {
            "application": application,
            "form": form
        }
    )