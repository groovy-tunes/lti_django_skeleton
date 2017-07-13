from django.contrib import admin

from .models import LTIUser, Course, Role, Authentication, Settings,
                    Submission, Assignment, AssignmentGroup,
                    AssignmentGroupMembership, Log

admin.site.register(LTIUser)
admin.site.register(Course)
admin.site.register(Role)
admin.site.register(Authentication)
admin.site.register(Settings)
admin.site.register(Submission)
admin.site.register(Assignment)
admin.site.register(AssignmentGroup)
admin.site.register(AssignmentGroupMembership)
admin.site.register(Log)
