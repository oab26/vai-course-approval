"""VAI Course Approval Workflow for Open edX."""

from setuptools import setup, find_packages

setup(
    name='vai-course-approval',
    version='0.1.0',
    description='Course approval workflow for VAI Open edX platform',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'cms.djangoapp': [
            'course_approval = course_approval.apps:CourseApprovalConfig',
        ],
        'lms.djangoapp': [
            'course_approval = course_approval.apps:CourseApprovalConfig',
        ],
    },
)
