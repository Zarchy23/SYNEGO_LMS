"""
Admin views for enterprise features
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def admin_dashboard(request):
    """Admin dashboard"""
    return JsonResponse({'message': 'Feature coming soon'})
"""
Enterprise admin feature views.

This module previously contained AI, Blockchain, Integration, Security, Configuration,
and Analytics features but they have been removed from the system.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from lms.permission_decorators import admin_required
