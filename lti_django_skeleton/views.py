from django.views.generic import View
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.html import MLStripper
from urllib.parse import quote as url_quote
from urllib.parse import urlencode


from lti import ToolConfig
from lti_django_skeleton.models import Role, Course
from ltilaunch.models import LTIUser
from lti_django_skeleton.models import Assignment, AssignmentGroup, Submission

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def error(exception=None):
    """
    Error page

    :param exception: optional exception
    :return: the error.html template rendered
    """
    print(exception)
    if request.method == 'POST':
        params = request.form.to_dict()
    else:
        params = request.args.to_dict()
    return render('error.html')

def ensure_canvas_arguments(request):
    """
    Returns roles and course of the current user.

    :param request: the incoming HttpRequest
    :return: roles and course of user
    """
    user = LTIUser.objects.get(user=request.user)
    roles = user.last_launch_parameters.get("roles", "")
    context_id = user.last_launch_parameters.get("context_id", "")
    context_title = user.last_launch_parameters.get("context_title", "")
    course = Course.from_lti("canvas",
                             context_id,
                             context_title,
                             user.id)

    return user, roles, course


class ConfigView(View):
    """
    Returns the configuration xml for the LTI provider.
    """
    def get(self, request):
        app_title = 'My App'
        app_description = 'An example LTI app'
        launch_view_name = 'lti_launch'
        launch_url = request.build_absolute_uri(reverse('lti_launch'))

        # maybe you've got some extensions
        extensions = {
            'my_extensions_provider': {
                # extension settings...
            }
        }

        lti_tool_config = ToolConfig(
            title=app_title,
            launch_url=launch_url,
            secure_launch_url=launch_url,
            extensions=extensions,
            description = app_description
        )

        return HttpResponse(lti_tool_config.to_xml(), content_type='text/xml')


@login_required
def index(request):
    """
    Initial access page to the lti provider.  This page provides
    authorization for the user.

    :param request: HttpRequest
    :return: index page for lti provider
    """
    assignment_id = request.GET.get('assignment_id', None)
    assignment_group_id = request.GET.get('assignment_group_id', None)
    user, roles, course = ensure_canvas_arguments(request)
    # Assignment group or individual assignment?
    if assignment_group_id is not None:
        group = AssignmentGroup.by_id(assignment_group_id)
        assignments = group.get_assignments()
        submissions = [a.get_submission(user.id) for a in assignments]
    elif assignment_id is not None:
        assignments = [Assignment.by_id(assignment_id)]
        submissions = [assignments[0].get_submission(user.id)]
    else:
        return error()
    # Use the proper template
    if assignments[0].mode == 'maze':
        context = {
            'assignment': assignments[0],
            'submission': submissions[0],
            'level': assignments[0].name,
            'user_id': user.id
        }
        return render(request, 'lti/maze.html', context)
    elif assignments[0].mode == 'explain':
        MAX_QUESTIONS = 5
        code, elements = submissions[0].load_explanation(MAX_QUESTIONS)
        context = {
            'assignment': assignments[0],
            'submission': submissions[0],
            'code': code,
            'elements': elements,
            'user_id': user.id
        }
        return render(request, 'lti/explain.html', context)
    else:
        context = {
            'group': zip(assignments, submissions),
            'user_id': user.id
        }
        return render(request, 'lti/index.html', context)

@login_required
def select(request):
    """
    Let's the user select from a list of assignments.

    :param request: HttpRequest
    :return: the select.html template rendered
    """
    user, roles, course = ensure_canvas_arguments(request)
    assignments = Assignment.by_course(course.id, exclude_builtins=True)
    groups = [(group, group.get_assignments())
              for group in AssignmentGroup.by_course(course.id)]
    strays = AssignmentGroup.get_ungrouped_assignments(course.id)
    return_url = user.last_launch_parameters.get('launch_presentation_return_url', None)

    context = {
        'assignments': assignments,
				'strays': strays,
				'groups': groups,
				'return_url': return_url,
				'menu': 'select'
    }
    return render(request, 'lti/select.html', context)

@login_required
def check_assignments(request):
    """
    An AJAX endpoint for listing any new assignments.

    Unused.
    """
    # Store current user_id and context_id
    user, roles, course = ensure_canvas_arguments()
    assignments = Assignment.by_course(course.id)
    return JsonResponse({
        'success': True,
        'assignments': [a.to_dict() for a in assignments]
    })

@login_required
def save_code(request):
    assignment_id = request.form.get('question_id', None)
    assignment_version = int(request.form.get('version', -1))
    if assignment_id is None:
        return JsonResponse({
            'success': False,
            'message': "No Assignment ID given!"
        })
    code = request.form.get('code', '')
    filename = request.form.get('filename', '__main__')
    user = User.from_lti("canvas", session["pylti_user_id"],
                         session.get("user_email", ""),
                         session.get("lis_person_name_given", ""),
                         session.get("lis_person_name_family", ""))
    is_version_correct = True
    if filename == "__main__":
        submission, is_version_correct = Submission.save_code(user.id, assignment_id, code, assignment_version)
    elif User.is_lti_instructor(session["roles"]):
        if filename == "on_run":
            Assignment.edit(assignment_id=assignment_id, on_run=code)
        elif filename == "on_change":
            Assignment.edit(assignment_id=assignment_id, on_step=code)
        elif filename == "starting_code":
            Assignment.edit(assignment_id=assignment_id, on_start=code)
    return JsonResponse({
        'success': True,
        'is_version_correct': is_version_correct
    })

@login_required
def save_events(request):
    assignment_id = request.form.get('question_id', None)
    event = request.form.get('event', "blank")
    action = request.form.get('action', "missing")
    if assignment_id is None:
        return JsonResponse({
            'success': False,
            'message': "No Assignment ID given!"
        })
    user = User.from_lti("canvas", session["pylti_user_id"],
                         session.get("user_email", ""),
                         session.get("lis_person_name_given", ""),
                         session.get("lis_person_name_family", ""))
    log = Log.new(event, action, assignment_id, user.id)
    return JsonResponse({
        'success': True
    })

@login_required
def save_correct(request):
    assignment_id = request.form.get('question_id', None)
    status = float(request.form.get('status', "0.0"))
    lis_result_sourcedid = request.form.get('lis_result_sourcedid', None)
    if assignment_id is None:
        return JsonResponse({
            'success': False,
            'message': "No Assignment ID given!"
        })
    user = User.from_lti("canvas", session["pylti_user_id"],
                         session.get("user_email", ""),
                         session.get("lis_person_name_given", ""),
                         session.get("lis_person_name_family", ""))
    assignment = Assignment.by_id(assignment_id)
    if status == 1:
        submission = Submission.save_correct(user.id, assignment_id)
    else:
        submission = assignment.get_submission(user.id)
    if submission.correct:
        message = "Success!"
    else:
        message = "Incomplete"
    url = url_for('lti_assignments.get_submission_code', submission_id=submission.id, _external=True)
    if lis_result_sourcedid is None:
        return JsonResponse({
            'success': False,
            'message': "Not in a grading context."
        })
    if assignment.mode == 'maze':
        lti.post_grade(float(submission.correct), "<h1>{0}</h1>".format(message), endpoint=lis_result_sourcedid);
    else:
        lti.post_grade(float(submission.correct), "<h1>{0}</h1>".format(message)+"<div>Latest work in progress: <a href='{0}' target='_blank'>View</a></div>".format(url)+"<div>Touches: {0}</div>".format(submission.version)+"Last ran code:<br>"+highlight(submission.code, PythonLexer(), HtmlFormatter()), endpoint=lis_result_sourcedid)
    return JsonResponse({
        'success': True
    })

@login_required
def get_submission_code(request, submission_id):
    user, roles, course = ensure_canvas_arguments(request)
    submission = Submission.objects.get(pk=submission_id)
    if LTIUser.is_lti_instructor(roles) or submission.user.id == user.id:
        return HttpResponse(submission.code) if submission.code else "#No code given!"
    else:
        return HttpResponse("Sorry, you do not have sufficient permissions to spy!")

@login_required
def save_presentation(request):
    assignment_id = request.form.get('question_id', None)
    if assignment_id is None:
        return JsonResponse({
            'success': False,
            'message': "No Assignment ID given!"
        })
    presentation = request.form.get('presentation', "")
    parsons = request.form.get('parsons', "false") == "true"
    text_first = request.form.get('text_first', "false") == "true"
    name = request.form.get('name', "")
    if User.is_lti_instructor(session["roles"]):
        Assignment.edit(assignment_id=assignment_id, presentation=presentation, name=name, parsons=parsons, text_first=text_first)
        return JsonResponse({
            'success': True
        })
    else:
        return JsonResponse({
            'success': False,
            'message': "You are not an instructor!"
        })

@login_required
def new_assignment(request, menu):
user, roles, course = ensure_canvas_arguments(request)
    user = LTIUser.objects.get(pk=1)
    course = Course.objects.get(pk=1)
   if not LTIUser.is_lti_instructor(roles):
       return HttpResponse("You are not an instructor in this course.")
    assignment = Assignment.new(owner_id=user.id, course_id=course.id)
    launch_type = 'lti_launch_url' if menu != 'share' else 'iframe'
    endpoint = 'lti_index' if menu != 'share' else 'lti_shared'
    select = url_quote(reverse(endpoint))+"?assignment_id="+assignment_id+"&return_type="+launch_type+"&title="+url_quote(assignment.title())+"&text=BlockPy%20Exercise&width=100%25&height=600"
    return JsonResponse({
        'success': True,
        'redirect': reverse('lti_edit_assignment', kwargs={'assignment_id': assignment.id}),
        'id': assignment.id,
        'name': assignment.name,
        'body': strip_tags(assignment.body)[:255],
        'title': assignment.title(),
        'select': select,
        'edit': reverse('lti_edit_assignment', kwargs={'assignment_id': assignment.id}),
        'date_modified': assignment.date_modified.strftime(" %I:%M%p on %a %d, %b %Y").replace(" 0", " ")
    })

@login_required
def remove_assignment(request, assignment_id):
    if assignment_id is None:
        return JsonResponse({
            'success': False,
            'message': "No assignment id"
        })
    user, roles, course = ensure_canvas_arguments(request)
    if not LTIUser.is_lti_instructor(roles):
        return JsonResponse({
            'success': False,
            'message': "You are not an instructor in this course."
        })
    # TODO: Security hole, evil instructors could remove assignments outside of their course
    Assignment.remove(assignment_id)
    return JsonResponse({'success': True})

@login_required
def get_assignment(request, assignment_id):
    """
    Returns metadata about the assignment.
    """
    if assignment_id is None:
        return JsonResponse({
            'success': False,
            'message': "No assignment id"
        })
    user, roles, course = ensure_canvas_arguments(request)
    if not User.is_lti_instructor(roles):
        return JsonResponse({
            'success': False,
            'message': "You are not an instructor in this course."
        })
    # TODO: Security hole, evil instructors could remove assignments outside of their course
    assignment = Assignment.by_id(assignment_id)
    return JsonResponse({
        'success': True,
        'url': assignment.url,
        'name': assignment.name,
        'body': strip_tags(assignment.body)[:255],
        'on_run': assignment.on_run,
        'title': assignment.title(),
        'answer': assignment.answer,
        'type': assignment.type,
        'visibility': assignment.visibility,
        'disabled': assignment.disabled,
        'mode': assignment.mode,
        'version': assignment.version,
        'id': assignment.id,
        'course_id': assignment.course_id,
        'date_modified': assignment.date_modified.strftime(" %I:%M%p on %a %d, %b %Y").replace(" 0", " ")
    })

@login_required
def select_builtin_assignment(request):
    assignment_type = request.GET.get('assignment_type', None)
    assignment_id = request.GET.get('assignment_id', None)
    user, roles, course = ensure_canvas_arguments(request)
    if not User.is_lti_instructor(roles):
        return HttpResponse("You are not an instructor in this course.")
    assignment = Assignment.by_builtin(assignment_type, assignment_id,
                                       owner_id=user.id, course_id=course.id)
    assignment_url = url_for('lti_assignments.index',
                                    assignment_id=assignment.id,
                                    _external=True)
    print(assignment_url)
    encoded_url = url_quote(assignment_url)
    return JsonResponse({
        'url': encoded_url
    })

@login_required
def edit_assignment(request, assignment_id):
    user, roles, course = ensure_canvas_arguments(request)
    assignment = Assignment.by_id(assignment_id)
    if not assignment:
        return HttpResponse("Assignment ID not found")
    if not LTIUser.is_lti_instructor(roles):
        return HttpResponse("You are not an instructor in this course.")
    if not assignment.context_is_valid(course.external_id):
        return HttpResponse("This assignment does not belong to this course.")
    submission = assignment.get_submission(user.id)
    submission = assignment.get_submission(1)
    context = {
        'assignment': assignment,
        'submission': submission,
        'user_id': user.id,
        'context_id': course.id
    }
    return render('lti/edit.html', context)

@login_required
def batch_edit(request):
    user, roles, course = ensure_canvas_arguments(request)
    if not LTIUser.is_lti_instructor(roles):
        return HttpResponse("You are not an instructor in this course.")
    assignments = Assignment.by_course(course.id)

    context = {
        'assignments': assignments,
        'user_id': user.id,
        'context_id': course.id
    }
    return render('lti/batch.html', context)

@login_required
def dashboard(request):
    """ render the contents of the staff.html template

    :param request: the Django HttpRequest
    :return: the staff.html template rendered
    """
    return HttpResponse("Choose from the below:<ol><li>Test</li></ol>")

@login_required
def share(request):
    """ render the contents of the staff.html template

    :param request: the Django HttpRequest
    :return: the staff.html template rendered
    """
    user, roles, course = ensure_canvas_arguments(request)
    assignments = Assignment.by_course(course.id, exclude_builtins=True)
    groups = [(group, group.get_assignments())
              for group in AssignmentGroup.by_course(course.id)]
    strays = AssignmentGroup.get_ungrouped_assignments(course.id)
    return_url = user.last_launch_parameters.get('launch_presentation_return_url', '')

    context = {
        'assignments': assignments,
        'strays': strays,
        'groups': groups,
        'return_url': return_url,
        'menu': 'share'
    }
    return render('lti/select.html', context)

@login_required
def shared(request):
    """ render the contents of the assignment template

    :param request: the Django HttpRequest
    :return: the staff.html template rendered
    """
    assignment_id = request.GET.get('assignment_id', None)
    assignment_group_id = request.GET.get('assignment_group_id', None)
    user, roles, course = ensure_canvas_arguments()
    # Assignment group or individual assignment?
    if assignment_group_id is not None:
        group = AssignmentGroup.by_id(assignment_group_id)
        assignments = group.get_assignments()
        submissions = [a.get_submission(user.id) for a in assignments]
    elif assignment_id is not None:
        assignments = [Assignment.by_id(assignment_id)]
        submissions = [assignments[0].get_submission(user.id)]
    else:
        return error()
    # Use the proper template
    if assignments[0].mode == 'maze':
        context = {
            'assignment': assignments[0],
            'submission': submissions[0],
            'level': assignments[0].name,
            'user_id': user.id
        }
        return render('lti/maze.html', context)
    elif assignments[0].mode == 'explain':
        context = {
            'assignment': assignments[0],
            'submission': submissions[0],
            'user_id': user.id
        }
        return render('lti/explain.html', context)
    else:
        context = {
            'group': zip(assignments, submissions),
            'user_id': user.id
        }
        return render('lti/index.html', context)

@login_required
def grade(request):
    """
    Post grade

    :param request: the Django HttpRequest
    :return: grade rendered by grade.html template
    """
    assignment_id = request.form.get('question_id', None)
    if assignment_id is None:
        return JsonResponse({
            'success': False,
            'message': "No Assignment ID given!"
        })
    user = LTIUser.from_lti("canvas", session["pylti_user_id"],
                         session.get("user_email", ""))
    submission = Submission.save_correct(user.id, assignment_id)
    if 'lis_result_sourcedid' not in session:
        return "Failure"
    lti.post_grade(1, "<h1>Success</h1>"+highlight(submission.code, PythonLexer(), HtmlFormatter()))
    return HttpResponse("Successful!")
