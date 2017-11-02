from django.shortcuts import render
from app.models import ReportComment, School, Enquiry, SchoolComment
from sso.models import User
from app.forms import SchoolForm, EnquiryAnswerForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from sso.utils import send_email


class AdminView():
    @user_passes_test(lambda u: u.is_superuser)
    def index(request):
        return render(request, 'app/admin_base.html')

    @user_passes_test(lambda u: u.is_superuser)
    def user_list(request):
        user_list = User.objects.all()
        return render(request, 'app/admin/admin_users.html', {'active': 'user', 'user_list': user_list})

    @user_passes_test(lambda u: u.is_superuser)
    def user_detail(request, user_id):
        user = User.objects.get(id=user_id)
        return render(request, 'app/admin/admin_users_detail.html', {'active': 'user', 'user': user})

    @user_passes_test(lambda u: u.is_superuser)
    def block_user(request, user_id):
        user = User.objects.get(id=user_id)
        user.is_active = False
        user.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    @user_passes_test(lambda u: u.is_superuser)
    def unblock_user(request, user_id):
        user = User.objects.get(id=user_id)
        user.is_active = True
        user.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    @user_passes_test(lambda u: u.is_superuser)
    def school_list(request):
        school_list = School.objects.all()
        return render(request, 'app/admin/admin_schools.html', {'active': 'school', 'school_list': school_list})

    @user_passes_test(lambda u: u.is_superuser)
    def school_detail(request, school_id):
        school = School.objects.get(id=school_id)
        return render(request, 'app/admin/admin_schools_detail.html', {'active': 'school', 'school': school})

    @user_passes_test(lambda u: u.is_superuser)
    def edit_school(request, school_id):
        school = School.objects.get(id=school_id)
        if request.method == 'POST':
            form = SchoolForm(request.POST, instance=school)
            if form.is_valid():
                new_school = form.save(commit=False)
                new_school.save()
                return HttpResponseRedirect(reverse('app:admin_schools'))
        else:
            form = SchoolForm(instance=school)
        return render(request, 'app/admin/admin_edit_school.html', {'active': 'school', 'form': form})

    @user_passes_test(lambda u: u.is_superuser)
    def delete_school(request, school_id):
        school = School.objects.get(id=school_id)
        school.delete()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    @user_passes_test(lambda u: u.is_superuser)
    def enquiry_list(request):
        enquiry_list = Enquiry.objects.all()
        return render(request, 'app/admin/admin_enquiries.html', {'active': 'enquiry', 'enquiry_list': enquiry_list})

    @user_passes_test(lambda u: u.is_superuser)
    def enquiry_detail(request, enquiry_id):
        enquiry = Enquiry.objects.get(id=enquiry_id)
        if request.method == 'POST':
            form = EnquiryAnswerForm(request.POST)
            if form.is_valid():
                new_answer = form.save(commit=False)
                new_answer.enquiry = enquiry
                new_answer.answered_by = request.user
                new_answer.save()
                enquiry.status = 'A'
                enquiry.save()

                full_name = enquiry.name
                content = 'Hi, {} <br><br> Thank you for using SchoolPedia. <br><br>' \
                          'Your enquiry is answered by SchoolPedia Admin! <br><br>' \
                          'Q: {} <br>' \
                          'A: {} <br><br>' \
                          'Have a good day!'

                send_email(
                    enquiry.email,
                    'SchoolPedia Registration',
                    content.format(full_name, enquiry.message, new_answer.answer))

                return HttpResponseRedirect(reverse('app:admin_enquiries'))
        else:
            form = EnquiryAnswerForm()
        return render(request, 'app/admin/admin_enquiries_detail.html', {'active': 'enquiry', 'enquiry': enquiry, 'form': form})

    @user_passes_test(lambda u: u.is_superuser)
    def report_list(request):
        report_list = ReportComment.objects.filter(comment__created_by__is_active=True)
        return render(request, 'app/admin/admin_reports.html', {'active': 'report', 'report_list': report_list})

    @user_passes_test(lambda u: u.is_superuser)
    def ignore_report(request, report_id):
        report = ReportComment.objects.get(id=report_id)
        report.delete()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    @user_passes_test(lambda u: u.is_superuser)
    def delete_comment(request, comment_id):
        comment = SchoolComment.objects.get(id=comment_id)
        comment.delete()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
