from app.models import School, SchoolComment
from app.forms import EnquiryForm, CommentForm
from django.shortcuts import render
from app import utils
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q


class PublicView():
    def school_list(request):
        latitude, longitude, has_coordinate = utils.get_coordinate_from_request(request)
        queryset = School.objects.all()
        queryset_without_alphabet = queryset

        if request.GET:
            if 'school_name' in request.GET:
                queryset = queryset.filter(school_name__icontains=request.GET['school_name'])
            if 'score' in request.GET:
                try:
                    score = int(request.GET['score'])

                    # ada between
                    queryset = queryset.filter(
                       (Q(express_nonaff_lower__isnull=False) & Q(express_nonaff_lower__lte=score)) |
                       (Q(normal_technical_nonaff_lower__isnull=False) & Q(normal_technical_nonaff_lower__lte=score)) |
                       (Q(normal_academic_nonaff_lower__isnull=False) & Q(normal_academic_nonaff_lower__lte=score))
                    )
                except ValueError:
                    pass
            if 'distance' in request.GET and 'latitude' in request.GET and 'longitude' in request.GET:
                distance = float(request.GET['distance'])
                latitude = float(request.GET['latitude'])
                longitude = float(request.GET['longitude'])

                degreediff = distance / 111
                queryset = queryset.filter(
                    lat__isnull=False,
                    lng__isnull=False,
                )
                queryset = queryset.filter(
                    Q(lng__lte=longitude + degreediff) &
                    Q(lng__gte=longitude - degreediff) &
                    Q(lat__lte=latitude + degreediff) &
                    Q(lat__gte=latitude - degreediff)
                )

            if 'zoneNorth' in request.GET:
                queryset = queryset.filter(~Q(zone_code='NORTH'))

            if 'zoneSouth' in request.GET:
                queryset = queryset.filter(~Q(zone_code='SOUTH'))

            if 'zoneEast' in request.GET:
                queryset = queryset.filter(~Q(zone_code='EAST'))

            if 'zoneWest' in request.GET:
                queryset = queryset.filter(~Q(zone_code='WEST'))

            if 'spIP' in request.GET:
                queryset = queryset.filter(ip_ind='No')

            if 'spSAP' in request.GET:
                queryset = queryset.filter(sap_ind='No')

            if 'spNone' in request.GET:
                queryset = queryset.filter(Q(ip_ind='Yes') | Q(sap_ind='Yes'))

            if 'chineseMT' not in request.GET:
                queryset = queryset.filter(
                    Q(mothertongue1_code='Chinese') | Q(mothertongue2_code='Chinese') | Q(mothertongue3_code='Chinese')
                )

            if 'malayMT' not in request.GET:
                queryset = queryset.filter(
                    Q(mothertongue1_code='Malay') | Q(mothertongue2_code='Malay') | Q(mothertongue3_code='Malay')
                )

            if 'tamilMT' in request.GET:
                queryset = queryset.filter(
                    Q(mothertongue1_code='Tamil') | Q(mothertongue2_code='Tamil') | Q(mothertongue3_code='Tamil')
                )

            if 'sortAsc' in request.GET:
                queryset = queryset.order_by('-school_name')

            queryset_without_alphabet = queryset
            if 'alphabet' in request.GET:
                queryset = queryset.filter(school_name__istartswith=request.GET['alphabet'])

        # queryset and pagination
        paginator = Paginator(queryset, 10)  # one page contains 10 items
        page = request.GET.get('page')
        try:
            school_list = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            school_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            school_list = paginator.page(paginator.num_pages)

        compare_school_id_list = request.session.get('compare_school_id_list', [])

        tmp_queryset = queryset_without_alphabet.all()
        school_alphabet = [{'alphabet': chr(65 + x), 'disabled': True} for x in range(26)]
        for school in tmp_queryset:
            first_letter = school.school_name[0]
            idx = ord(first_letter.upper()) - 65
            school_alphabet[idx]['disabled'] = False

        params_text_without_alphabet = ''.join(['&{}={}'.format(x[0], x[1]) for x in request.GET.items() if x[0] != 'alphabet'])
        params_text = ''.join(['&{}={}'.format(x[0], x[1]) for x in request.GET.items() if x[0] != 'page'])

        return render(request, 'app/school/school_list.html', {
            'school_list': school_list,
            'allow_compare': len(compare_school_id_list) < 6,
            'has_coordinate': has_coordinate,
            'latitude': latitude,
            'longitude': longitude,
            'params_text': params_text,
            'params_text_without_alphabet': params_text_without_alphabet,
            'school_alphabet': school_alphabet,
            'params': request.GET
        })

    def school_detail(request, school_id):
        latitude, longitude, has_coordinate = utils.get_coordinate_from_request(request)
        school = School.objects.get(id=school_id)

        # queryset and pagination
        queryset = SchoolComment.objects.filter(school=school)
        paginator = Paginator(queryset, 10)  # one page contains 10 items
        page = request.GET.get('page')
        try:
            comment_list = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            comment_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            comment_list = paginator.page(paginator.num_pages)

        comment_form = ''
        if request.user.is_authenticated():
            if request.POST:
                comment_form = CommentForm(request.POST)
                if comment_form.is_valid():
                    comment = comment_form.save(commit=False)
                    comment.school = school
                    comment.created_by = request.user
                    comment.save()
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            comment_form = CommentForm()

        return render(request, 'app/school/school_detail.html', {
            'school': school,
            'comment_form': comment_form,
            'comment_list': comment_list,
            'has_coordinate': has_coordinate,
            'latitude': latitude,
            'longitude': longitude
        })

    def add_to_comparison(request, school_id):
        compare_school_id_list = request.session.get('compare_school_id_list', [])
        if school_id not in compare_school_id_list and len(compare_school_id_list) < 6:
            compare_school_id_list.append(school_id)
        request.session['compare_school_id_list'] = compare_school_id_list
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def remove_from_comparison(request, school_id):
        compare_school_id_list = request.session.get('compare_school_id_list', [])
        if school_id in compare_school_id_list:
            compare_school_id_list = [x for x in compare_school_id_list if x != school_id]
        request.session['compare_school_id_list'] = compare_school_id_list
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def compare_schools(request):
        compare_school_id_list = request.session.get('compare_school_id_list', [])
        compared_school_list = School.objects.filter(id__in=compare_school_id_list)
        return render(request, 'app/comparison/index.html', {
            'compared_school_list': compared_school_list
        })

    def contact_us(request):
        if request.method == "POST":
            form = EnquiryForm(request.POST)
            if form.is_valid():
                new_enquiry = form.save(commit=False)
                new_enquiry.save()
                return HttpResponseRedirect("/")
        else:
            form = EnquiryForm()
        return render(request, 'app/contactus/index.html', {'form': form})
