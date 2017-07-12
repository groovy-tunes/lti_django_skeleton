from django.views.generic import View
from django.urls import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from lti import ToolConfig

def ensure_canvas_arguments(request):
    """
    Returns roles and course of the current user.

    :param request: the incoming HttpRequest
    :return: roles and course of user
    """
    roles = Role.objects.filter(user=request.user)
    context_id = request.user.last_launch_parameters.get("context_id", "")
    context_title = request.user.last_launch_parameters.get("context_title", "")
    course = Course.from_lti("canvas",
                             context_id,
                             context_title,
                             request.user.id)

    return roles, course

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

def index(request, a_id, a_g_id):
    """
    Initial access page to the lti provider.  This page provides
    authorization for the user.

    :param request: HttpRequest
    :return: index page for lti provider
    """
    assignment_id = a_id
    assignment_group_id = a_g_id
    user = request.user
    roles, course = ensure_canvas_arguments(request)
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
