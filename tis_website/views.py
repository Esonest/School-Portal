from django.shortcuts import render, get_object_or_404

from .models import (
    SchoolWebsite,
    HomepageContent,
    WhyChooseUs,
    SchoolStatistic
)



def get_website(slug):
    """
    Get school website profile using slug
    """

    return get_object_or_404(
        SchoolWebsite,
        slug=slug
    )



def home(request, school_slug):

    website = get_website(
        school_slug
    )

    school = website.school


    homepage = HomepageContent.objects.filter(
        school=school
    ).first()


    why_choose = WhyChooseUs.objects.filter(
        school=school
    )


    statistics = SchoolStatistic.objects.filter(
        school=school
    )


    return render(
        request,
        "tis_website/public/home.html",
        {
            "website": website,
            "homepage": homepage,
            "why_choose": why_choose,
            "statistics": statistics,
        }
    )




def about(request, school_slug):

    website = get_website(
        school_slug
    )


    return render(
        request,
        "tis_website/public/about.html",
        {
            "website": website,
        }
    )





def academics(request, school_slug):

    website = get_website(
        school_slug
    )


    return render(
        request,
        "tis_website/public/academics.html",
        {
            "website": website,
        }
    )





def admissions(request, school_slug):

    website = get_website(
        school_slug
    )


    return render(
        request,
        "tis_website/public/admissions.html",
        {
            "website": website,
        }
    )





def contact(request, school_slug):

    website = get_website(
        school_slug
    )


    return render(
        request,
        "tis_website/public/contact.html",
        {
            "website": website,
        }
    )


from .models import AdmissionApplication

from .forms import AdmissionApplicationForm




def admissions(request, school_slug):


    website = get_object_or_404(

        SchoolWebsite,

        slug=school_slug

    )



    school = website.school




    submitted = False




    if request.method == "POST":



        form = AdmissionApplicationForm(

            request.POST,

            request.FILES

        )



        if form.is_valid():



            admission = form.save(

                commit=False

            )



            admission.school = school



            admission.save()



            submitted = True



    else:


        form = AdmissionApplicationForm()




    return render(

        request,

        "tis_website/public/admissions.html",

        {

            "form":form,

            "website":website,

            "submitted":submitted

        }

    )

from cbt.models import CBTExam, CBTQuestion, CBTSubmission
from django.utils import timezone
from django.http import Http404



from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from cbt.models import CBTSubmission
from .models import AdmissionApplication


def admission_exam_access(request, token):

    application = get_object_or_404(
        AdmissionApplication,
        admission_token=token
    )

    exam = application.admission_exam

    if not exam:
        raise Http404("No examination assigned.")

    if not exam.is_active():
        return render(
            request,
            "tis_website/public/exam_not_available.html",
            {
                "application": application,
                "exam": exam,
            },
        )

    # Store applicant ID in the session
    request.session["admission_application_id"] = application.id

    return redirect(
        "cbt:start_admission_exam",
        exam_id=exam.id
    )   

