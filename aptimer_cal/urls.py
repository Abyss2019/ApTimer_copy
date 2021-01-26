from django.urls import path, include
from rest_framework import routers

from .views import DiffView, ExcelView, IniBoundView, DisTimeView, InputIniboundView

router = routers.DefaultRouter()

# router.register(r'cal', CalView, basename="cal")

urlpatterns = [
    path('excel', ExcelView.as_view(), name="excel"),
    path('input-inibound', InputIniboundView.as_view(), name="input-inibound"),

    # /diff?temp=900&tilt=17
    path('diff', DiffView.as_view(), name="diffusivity"),

    # /inibound?xcl_ini=0.14&xcl_left=0.22&xcl_right=0.14&xf_ini=0.69&xf_left=0.78&xf_right=0.69&xoh_ini=0.17&xoh_left=0.0&xoh_right=0.17
    path('inibound', IniBoundView.as_view(), name="inibound"),

    # /distime?dx=0.5&dt=1&iteration=230
    path('distime', DisTimeView.as_view(), name="distime"),
]
