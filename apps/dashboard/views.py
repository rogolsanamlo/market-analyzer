from django.shortcuts import render


def index(request):
    """The single page of the site - the JavaScript on it loads the data from /api/."""
    return render(request, "dashboard.html")
