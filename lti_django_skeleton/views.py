from django.views.generic import View
from django.urls import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from lti import ToolConfig
from lti_django_skeleton.models import Role, Course
from ltilaunch.models import LTIUser

def error(exception=None):
    """ render error page

    :param exception: optional exception
    :return: the error.html template rendered
    """
    print(exception)
    if request.method == 'POST':
        params = request.form.to_dict()
    else:
        params = request.args.to_dict()
    return render_template('error.html')


def ensure_canvas_arguments(request):
    """
    Returns roles and course of the current user.

    :param request: the incoming HttpRequest
    :return: roles and course of user
    """
    user = LTIUser.objects.get(user=request.user)
    roles = Role.objects.filter(user=user)
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
def index(request, a_id, a_g_id):
    """
    Initial access page to the lti provider.  This page provides
    authorization for the user.

    :param request: HttpRequest
    :return: index page for lti provider
    """
    assignment_id = a_id
    assignment_group_id = a_g_id
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
        return render_template('lti/maze.html', lti=lti,
                               assignment= assignments[0],
                               submission= submissions[0],
                               level=assignments[0].name,
                               user_id=user.id)
    elif assignments[0].mode == 'explain':
        MAX_QUESTIONS = 5
        code, elements = submissions[0].load_explanation(MAX_QUESTIONS)
        return render_template('lti/explain.html', lti=lti,
                               assignment= assignments[0],
                               submission= submissions[0],
                               code = code,
                               elements=elements,
                               user_id=user.id)
    else:
        return render_template('lti/index.html', lti=lti,
                               group=zip(assignments, submissions),
                               user_id=user.id)

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
    return_url = request.user.last_launch_parameters.get('launch_presentation_return_url', None)

    return render_template('lti/select.html', assignments=assignments, strays=strays, groups=groups, return_url=return_url, menu='select')


@login_required
def check_assignments(request):
    """
    An AJAX endpoint for listing any new assignments.

    Unused.
    """
    # Store current user_id and context_id
    user, roles, course = ensure_canvas_arguments()
    assignments = Assignment.by_course(course.id)
    return jsonify(success=True, assignments=[a.to_dict() for a in assignments])


@login_required
def save_code(request):
    assignment_id = request.form.get('question_id', None)
    assignment_version = int(request.form.get('version', -1))
    if assignment_id is None:
        return jsonify(success=False, message="No Assignment ID given!")
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
    return jsonify(success=True, is_version_correct=is_version_correct)
