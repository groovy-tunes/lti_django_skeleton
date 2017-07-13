from datetime import datetime, timedelta
import time
import re
import os
import json
import logging

from django.db import models

from ltilaunch.models import LTIUser


class Base(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __tablename__(cls):
        return cls.__name__.lower()
    def __repr__(self):
        return str(self)

    class Meta:
        abstract = True


class Course(Base):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(LTIUser, on_delete=models.CASCADE)
    service = models.CharField(max_length=80, default="")
    external_id = models.CharField(max_length=255, default="")

    def __str__(self):
        return '<Course {}>'.format(self.id)

    @staticmethod
    def new_lti_course(service, external_id, name, user_id):
        owner = LTIUser.objects.get(pk=user_id)
        new_course = Course(name=name, owner=owner,
                            service=service, external_id=external_id)
        new_course.save()
        return new_course

    @staticmethod
    def from_lti(service, lti_context_id, name, user_id):
        lti_course = Course.objects.filter(external_id=lti_context_id).first()
        if lti_course is None:
            return Course.new_lti_course(service=service,
                                         external_id=lti_context_id,
                                         name=name,
                                         user_id=user_id)
        else:
            return lti_course


class Role(Base):
    name = models.CharField(max_length=80)
    user = models.ForeignKey(LTIUser, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    NAMES = ['teacher', 'admin', 'student']

    def __str__(self):
        return '<User {} is {}>'.format(self.user, self.name)


class Settings(Base):
    mode = models.CharField(max_length=80)
    connected = models.CharField(max_length=80)
    user = models.ForeignKey(LTIUser, on_delete=models.CASCADE)

    def __str__(self):
        return '<{} settings ({})>'.format(self.user_id, self.id)


class Assignment(Base):
    url = models.CharField(max_length=255, default="")
    name = models.CharField(max_length=255, default="Untitled")
    body = models.TextField(default="")
    on_run = models.TextField(default="def on_run(code, output, properties):\n    return True")
    on_step = models.TextField(default="def on_step(code, output, properties):\n    return True")
    on_start = models.TextField(default="")
    answer = models.TextField(default="")
    due = models.DateTimeField(default=None)
    type = models.CharField(max_length=10, default="normal")
    visibility = models.CharField(max_length=10, default="visible")
    disabled = models.CharField(max_length=10, default="enabled")
    mode = models.CharField(max_length=10, default="blocks")
    owner = models.ForeignKey(LTIUser, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    version = models.IntegerField(default=0)

    @staticmethod
    def edit(assignment_id, presentation=None, name=None, on_run=None, on_step=None, on_start=None, parsons=None, text_first=None):
        assignment = Assignment.objects.get(pk=assignment_id)
        if name is not None:
            assignment.name = name
            assignment.version += 1
        if presentation is not None:
            assignment.body = presentation
            assignment.version += 1
        if on_run is not None:
            assignment.on_run = on_run
            assignment.version += 1
        if on_step is not None:
            assignment.on_step = on_step
            assignment.version += 1
        if on_start is not None:
            assignment.on_start = on_start
            assignment.version += 1
        assignment.type = 'normal'
        if parsons is True:
            assignment.type = 'parsons'
            assignment.version += 1
        if text_first is True:
            assignment.type = 'text'
            assignment.version += 1
        assignement.save()
        return assignment

    def to_dict(self):
        return {
            'name': self.name,
            'id': self.id,
            'body': self.body,
            'title': self.title()
        }

    def __str__(self):
        return '<Assignment {} for {}>'.format(self.id, self.course.id)

    def title(self):
        return self.name if self.name != "Untitled" else "Untitled ({})".format(self.id)

    @staticmethod
    def new(owner_id, course_id):
        owner = LTIUser.objects.get(pk=owner_id)
        course = Course.objects.get(pk=course_id)
        assignment = Assignment(owner=owner, course=course)
        assignement.save()
        return assignment

    @staticmethod
    def remove(assignment_id):
        Assignment.objects.get(pk=assignment_id).delete()

    @staticmethod
    def by_course(course_id, exclude_builtins=True):
        if exclude_builtins:
            course = Course.objects.get(pk=course_id)
            return (Assignment.objects.filter(course=course)
						                        .exclude(mode='maze')
                                    .all())
        else:
            return Assignment.objects.filter(course=course)

    @staticmethod
    def by_id(assignment_id):
        return Assignment.objects.get(pk=assignment_id)

    @staticmethod
    def by_builtin(type, id, owner_id, course_id):
        course = Course.object.get(pk=course_id)
        assignment = Assignment.objects.filter(course=course,
                                                mode=type,
                                                name=id).first()
        if not assignment:
            assignment = Assignment.new(owner_id, course_id)
            assignment.mode = type
            assignment.name = id
            assignment.save()
        return assignment

    @staticmethod
    def by_id_or_new(assignment_id, owner_id, course_id):
        if assignment_id is None:
            assignment = None
        else:
            assignment = Assignment.objects.get(pk=assignment_id)
        if not assignment:
            assignment = Assignment.new(owner_id, course_id)
        return assignment

    def context_is_valid(self, context_id):
        course = Course.objects.get(pk=self.course_id)
        if course:
            return course.external_id == context_id
        return False

    def get_submission(self, user_id):
        return Submission.load(user_id, self.id)


class AssignmentGroup(Base):
    name = models.CharField(max_length=255, default="Untitled")
    owner = models.ForeignKey(LTIUser, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    @staticmethod
    def new(owner_id, course_id):
        owner = LTIUser.objects.get(pk=owner_id)
        course = Course.objects.get(pk=course_id)
        assignment_group = AssignmentGroup(owner=owner, course=course)
        assignment_group.save()
        return assignment_group

    @staticmethod
    def remove(assignment_group_id):
        targ_group = AssignmentGroup.objects.get(assignment_group_id)
        AssignmentGroup.objects.get(pk=assignment_group_id).delete()
        AssignmentGroupMembership.objects.filter(assignment_group=targ_group).delete()

    @staticmethod
    def edit(assignment_group_id, name=None):
        assignment_group = AssignmentGroup.objects.get(pk=assignment_group_id)
        if name is not None:
            assignment_group.name = name
        assignment_group.save()
        return assignment_group

    @staticmethod
    def by_id(assignment_group_id):
        return AssignmentGroup.objects.get(pk=assignment_group_id)

    @staticmethod
    def by_course(course_id):
        course = Course.objects.get(pk=course_id)
        return (AssignmentGroup.objects.filter(course=course)
                                     .order_by('name')
                                     .all())

    @staticmethod
    def get_ungrouped_assignments(course_id):
        course = Course.objects.get(pk=course_id)
        return (Assignment.objects
                          .filter(course=course)
                          .filter(assignmentgroupmembership__assignment__isnull=True)
                          .all())

    def get_assignments(self):
        return (Assignment.query
                          .join(AssignmentGroupMembership,
                                AssignmentGroupMembership.assignment_id == Assignment.id)
                          .filter(AssignmentGroupMembership.assignment_group_id==self.id)
                          .order_by(AssignmentGroupMembership.position)
                          .all())


class AssignmentGroupMembership(Base):
    assignment_group = models.ForeignKey(AssignmentGroup, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    position = models.IntegerField()

    @staticmethod
    def move_assignment(assignment_id, new_group_id):
        assignment = Assignment.objects.get(pk=assignment_id)
        new_assignment_group = AssignmentGroup.objects.get(pk=new_group_id)
        membership = (AssignmentGroupMembership.objects
                                               .filter(assignment=assignment)
                                               .first())
        if membership is None:
            membership = AssignmentGroupMembership(assignment_group=new_assignment_group,
                                                   assignment=assignment,
                                                   position=0)
        else:
            membership.assignment_group = new_assignment_group
        membership.save()
        return membership


class Submission(Base):
    code = models.TextField(default="")
    status = models.IntegerField(default=0)
    correct = models.BooleanField(default=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    user = models.ForeignKey(LTIUser, on_delete=models.CASCADE)
    assignment_version = models.IntegerField(default=0)
    version = models.IntegerField(default=0)

    def __str__(self):
        return '<Submission {} for {}>'.format(self.id, self.user)

    @staticmethod
    def load(user_id, assignment_id):
        submission = Submission.objects.filter(assignment_id=assignment_id,
                                                user_id=user_id).first()
        if not submission:
            submission = Submission(assignment_id=assignment_id, user_id=user_id)
            assignment = Assignment.objects.get(pk=assignment_id)
            if assignment.mode == 'explain':
                submission.code = json.dumps(Submission.default_explanation(''))
            else:
                submission.code = assignment.on_start
            submission.save()
        return submission

    @staticmethod
    def default_explanation(code):
        return {
                'code': code,
                'elements': {
                    'CORGIS_USE': {'line': 0, 'present': False, 'answer': '', 'name': 'CORGIS_USE'},
                    'FOR_LOOP': {'line': 0, 'present': False, 'answer': '', 'name': 'FOR_LOOP'},
                    'DICTIONARY_ACCESS': {'line': 0, 'present': False, 'answer': '', 'name': 'DICTIONARY_ACCESS'},
                    'IMPORT_CORGIS': {'line': 0, 'present': False, 'answer': '', 'name': 'IMPORT_CORGIS'},
                    'LIST_APPEND': {'line': 0, 'present': False, 'answer': '', 'name': 'LIST_APPEND'},
                    'IMPORT_MATPLOTLIB': {'line': 0, 'present': False, 'answer': '', 'name': 'IMPORT_MATPLOTLIB'},
                    'ASSIGNMENT': {'line': 0, 'present': False, 'answer': '', 'name': 'ASSIGNMENT'},
                    'MATPLOTLIB_PLOT': {'line': 0, 'present': False, 'answer': '', 'name': 'MATPLOTLIB_PLOT'},
                    'LIST_ASSIGNMENT': {'line': 0, 'present': False, 'answer': '', 'name': 'LIST_ASSIGNMENT'}
                }
        }

    @staticmethod
    def save_explanation_answer(user_id, assignment_id, name, answer):
        submission = Submission.objects.filter(user_id=user_id,
                                                assignment_id=assignment_id).first()
        submission_destructured = json.loads(submission.code)
        elements = submission_destructured['elements']
        if name in elements:
            elements[name]['answer'] = answer
            submission.code = json.dumps(submission_destructured)
            submission.version += 1
            submission.save()
            submission.log_code()
            return submission_destructured


    def save_explanation_code(self, code, elements):
        try:
            submission_destructured = json.loads(self.code)
        except ValueError:
            submission_destructured = {}
        if 'code' in submission_destructured:
            submission_destructured['code'] = code
            existing_elements = submission_destructured['elements']
            for element in existing_elements:
                existing_elements[element]['present'] = False
            for element, value in elements.items():
                existing_elements[element]['line'] = value
                existing_elements[element]['present'] = True
        else:
            submission_destructured = Submission.default_explanation(code)
        self.code = json.dumps(submission_destructured)
        self.version += 1
        self.save()
        self.log_code()
        return submission_destructured

    ELEMENT_PRIORITY_LIST = ['CORGIS_USE', 'FOR_LOOP', 'DICTIONARY_ACCESS',
                         'IMPORT_CORGIS', 'LIST_APPEND', 'IMPORT_MATPLOTLIB',
                         'ASSIGNMENT', 'MATPLOTLIB_PLOT']

    @staticmethod
    def abbreviate_element_type(element_type):
        return ''.join([l[0] for l in element_type.split("_")])

    def load_explanation(self, max_questions):
        submission_destructured = json.loads(self.code)
        code = submission_destructured['code']
        # Find the first FIVE
        available_elements = []
        used_lines = set()
        e = submission_destructured['elements']
        for element in Submission.ELEMENT_PRIORITY_LIST:
            # Not present?
            if not e[element]['present']:
                continue
            # Already used that line?
            if e[element]['line'][0] in used_lines:
                continue
            # Cool, then add it
            available_elements.append(e[element])
            used_lines.add(e[element]['line'][0])
            # Stop if we have enough already
            if len(available_elements) >= max_questions:
                break
        return code, available_elements

    @staticmethod
    def save_code(user_id, assignment_id, code, assignment_version):
        submission = Submission.objects.filter(user_id=user_id,
                                                assignment_id=assignment_id).first()
        is_version_correct = True
        if not submission:
            submission = Submission(assignment_id=assignment_id,
                                    user_id=user_id,
                                    code=code,
                                    assignment_version=assignment_version)
        else:
            submission.code = code
            submission.version += 1
            current_assignment_version = Assignment.objects.get(pk=submission.assignment_id).version
            is_version_correct = (assignment_version == current_assignment_version)
        submission.save()
        submission.log_code()
        return submission, is_version_correct

    @staticmethod
    def save_correct(user_id, assignment_id):
        submission = Submission.query.filter_by(user_id=user_id,
                                                assignment_id=assignment_id).first()
        if not submission:
            submission = Submission(assignment_id=self.id,
                                    user_id=user_id,
                                    correct=True)
        else:
            submission.correct = True
        submission.save()
        return submission

    def log_code(self, extension='.py'):
        '''
        Store the code on disk, mapped to the Assignment ID and the Student ID
        '''
        # Multiple-file logging
        directory = os.path.join(app.config['BLOCKLY_LOG_DIR'],
                                 str(self.assignment_id),
                                 str(self.user_id))

        ensure_dirs(directory)
        name = time.strftime("%Y%m%d-%H%M%S")
        file_name = os.path.join(directory, name + extension)
        with open(file_name, 'wb') as blockly_logfile:
            blockly_logfile.write(self.code)
        # Single file logging
        student_interactions_logger = logging.getLogger('StudentInteractions')
        student_interactions_logger.info(
            StructuredEvent(self.user_id, self.assignment_id, 'code', 'set', self.code)
        )


class Log(Base):
    event = models.CharField(max_length=255, default="")
    action = models.CharField(max_length=255, default="")
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    user = models.ForeignKey(LTIUser, on_delete=models.CASCADE)

    @staticmethod
    def new(event, action, assignment_id, user_id):
        assignment = Assignment.objects.get(pk=assignment_id)
        user = User.objects.get(pk=user_id)
        # Database logging
        log = Log(event=event, action=action, assignment=assignment, user=user)
        log.save()
        # Single-file logging
        student_interactions_logger = logging.getLogger('StudentInteractions')
        student_interactions_logger.info(
            StructuredEvent(user_id, assignment_id, event, action, '')
        )
        return log

    def __str__(self):
        return '<Log {} for {}>'.format(self.event, self.action)
