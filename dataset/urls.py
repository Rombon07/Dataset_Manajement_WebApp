# dataset/urls.py
from django.urls import path
from django.shortcuts import redirect
from . import views
from django.contrib.auth.views import LogoutView

from django.urls import path
from .views import receive_dataset_request


def upload_redirect(request):
    return redirect('upload_step1')

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),

    path("upload/", upload_redirect, name="upload_redirect"),  # redirect /upload/ ke step1
    path("upload/step1/", views.upload_step1, name="upload_step1"),
    path("upload/step2/", views.upload_step2, name="upload_step2"),

    path("mydata/", views.mydata, name="mydata"),
    path("dataset/<int:pk>/", views.dataset_detail, name="dataset_detail"),
    # path("dataset/<int:pk>/edit/", views.edit_dataset, name="edit_dataset"),
    path("edit/<int:pk>/step1/", views.edit_dataset_step1, name="edit_dataset_step1"),
    path("edit/<int:pk>/step2/", views.edit_dataset_step2, name="edit_dataset_step2"),
    
    path("dataset/<int:pk>/delete/", views.delete_dataset, name="delete_dataset"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),

    path("dataset/<int:dataset_id>/log_action/", views.log_dataset_action, name="log_dataset_action"),
    path("dataset/<int:dataset_id>/log_print/", views.log_print_action, name="log_print_action"),
    path("dataset/<int:pk>/print/", views.dataset_report, name="print_dataset"),
    path("dataset/<int:pk>/summary-pdf/", views.download_summary_pdf, name="download_summary"),
    
    #API
    path('request-list/', views.request_list, name='request_list'),
    # path('api/dataset-request/', views.dataset_request_api, name='dataset_request_api'),
    # path('api/dataset-response/', views.dataset_response_api, name='dataset_response_api'),
    
    #
    path("pilih-dataset/<int:request_id>/", views.pilih_dataset_untuk_request, name="pilih_dataset_untuk_request"),
    path("konfirmasi-pilih-dataset/<int:request_id>/<int:dataset_id>/", views.konfirmasi_pilih_dataset, name="konfirmasi_pilih_dataset"),


    path('api/dataset-request/', receive_dataset_request),

    path("api/kirim-dataset/<int:dataset_id>/<int:request_id>/", views.api_kirim_dataset_ke_teman_file, name="api_kirim_dataset_ke_teman"),
    path("api/request-list/", views.api_request_list, name="api_request_list"),

]
